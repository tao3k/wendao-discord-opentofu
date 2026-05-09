#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import re
import sys
import time
import tomllib
import urllib.error
import urllib.request
from datetime import datetime, timezone


API_BASE = "https://discord.com/api/v10"
GUILD_TEXT = 0
GUILD_PUBLIC_THREAD = 11
GUILD_FORUM = 15
GUILD_MEDIA = 16
SUPPORTED_KINDS = {"agenda_item", "kanban_card", "review_gate"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or ensure a Discord forum post/card from an agenda or kanban intent."
    )
    parser.add_argument(
        "--intent",
        required=True,
        help="Path to agenda_item or kanban_card intent TOML.",
    )
    parser.add_argument(
        "--receipt-path",
        default=None,
        help="Optional receipt output path. Defaults to .run/receipts/<intent>.<timestamp>.toml.",
    )
    parser.add_argument(
        "--operation-path",
        default="",
        help="Optional knowledge_operation path that produced this action.",
    )
    parser.add_argument(
        "--action-id",
        default="",
        help="Optional local action ID inside the knowledge_operation.",
    )
    parser.add_argument(
        "--workflow-node-ref",
        default="",
        help="Optional Wendao BPMN node reference for this action.",
    )
    parser.add_argument(
        "--graph-node-ref",
        default="",
        help="Optional Wendao petgraph node reference for this action.",
    )
    parser.add_argument(
        "--command-label",
        default="direnv exec . just create-work-item-post",
        help="Command label written into the receipt verification section.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print the planned action without calling Discord.",
    )
    return parser.parse_args()


def required_env(names: tuple[str, ...], label: str) -> str:
    for name in names:
        value = os.environ.get(name, "").removeprefix("Bot ").strip()
        if value:
            return value
    raise SystemExit(f"missing {label}")


def request_json(
    method: str,
    path: str,
    token: str,
    body: dict | None = None,
) -> tuple[int, dict | list]:
    data = None
    headers = {
        "Authorization": f"Bot {token}",
        "User-Agent": "wendao-discord-opentofu-runtime/0.1",
    }
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode()
                return response.status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            raw_error = error.read().decode()
            try:
                error_body = json.loads(raw_error)
            except Exception:
                error_body = {"message": raw_error or "<non-json body>"}
            if error.code == 429 and attempt < 2:
                retry_after = float(error_body.get("retry_after", 1))
                time.sleep(retry_after)
                continue
            return error.code, error_body

    raise RuntimeError("unreachable retry state")


def load_intent(path: pathlib.Path) -> dict:
    intent = tomllib.loads(path.read_text())
    kind = str(intent.get("kind", ""))
    if kind not in SUPPORTED_KINDS:
        supported = ", ".join(sorted(SUPPORTED_KINDS))
        raise SystemExit(f"{path} kind must be one of: {supported}")
    for key in ("target", "title"):
        if not str(intent.get(key, "")).strip():
            raise SystemExit(f"{path} is missing required field: {key}")
    return intent


def find_target_channel(channels: list[dict], target: str) -> dict:
    normalized = target.removeprefix("#")
    for channel in channels:
        if channel.get("id") == normalized:
            return channel
    for channel in channels:
        if channel.get("name") == normalized:
            return channel
    raise SystemExit(f"target channel not found: {target}")


def find_active_thread(threads: list[dict], parent_id: str, title: str) -> dict | None:
    for thread in threads:
        if thread.get("parent_id") == parent_id and thread.get("name") == title:
            return thread
    return None


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "work-item"


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def toml_array(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=True)


def display_state(intent: dict) -> str:
    if intent.get("kind") == "agenda_item":
        return str(intent.get("status", "proposed"))
    if intent.get("kind") == "review_gate":
        return str(intent.get("review_status", "pending-review"))
    return str(intent.get("state", "todo"))


def requested_tags(intent: dict) -> list[str]:
    values = [str(item) for item in intent.get("forum_tags", []) if str(item).strip()]
    state = display_state(intent)
    if state and state not in values:
        values.insert(0, state)
    return values


def resolve_applied_tags(target_channel: dict, requested: list[str]) -> tuple[list[str], list[str], list[str]]:
    available = target_channel.get("available_tags") or []
    by_name = {str(tag.get("name", "")).lower(): tag for tag in available}
    applied_ids: list[str] = []
    applied_names: list[str] = []
    missing: list[str] = []

    for name in requested:
        tag = by_name.get(name.lower())
        if tag and tag.get("id"):
            applied_ids.append(str(tag["id"]))
            applied_names.append(str(tag.get("name", name)))
        else:
            missing.append(name)

    return applied_ids, applied_names, missing


def list_lines(values: list[str]) -> list[str]:
    return [f"- `{value}`" for value in values] if values else ["- none"]


def render_agenda_message(intent: dict, intent_path: pathlib.Path) -> str:
    session = intent.get("session", {})
    lines = [
        "**Agenda item**",
        "",
        f"Objective: {intent.get('objective', '')}",
        f"Status: `{display_state(intent)}`",
        f"Facilitator: `{intent.get('facilitator_role', 'unassigned')}`",
        f"Duration: `{session.get('duration_minutes', 'unspecified')}` minutes",
        f"Scheduled for: `{session.get('scheduled_for') or 'unscheduled'}`",
        "",
        "Expected outputs:",
        *list_lines([str(item) for item in intent.get("expected_outputs", [])]),
        "",
        "Wendao refs:",
        *list_lines([str(item) for item in intent.get("source_refs", [])]),
        "",
        f"Intent: `{intent_path.as_posix()}`",
    ]
    return "\n".join(lines)


def render_kanban_message(intent: dict, intent_path: pathlib.Path) -> str:
    lines = [
        "**Kanban card**",
        "",
        f"Summary: {intent.get('summary', '')}",
        f"State: `{display_state(intent)}`",
        f"Priority: `{intent.get('priority', 'normal')}`",
        f"Owner role: `{intent.get('owner_role', 'unassigned')}`",
        "",
        "Acceptance criteria:",
        *list_lines([str(item) for item in intent.get("acceptance_criteria", [])]),
        "",
        "Wendao refs:",
        *list_lines([str(item) for item in intent.get("source_refs", [])]),
        "",
        f"Intent: `{intent_path.as_posix()}`",
    ]
    return "\n".join(lines)


def render_review_gate_message(intent: dict, intent_path: pathlib.Path) -> str:
    lines = [
        "**Review gate**",
        "",
        f"Decision needed: {intent.get('decision_prompt', '')}",
        f"Status: `{display_state(intent)}`",
        f"Reviewer roles: {', '.join(f'`{role}`' for role in intent.get('reviewer_roles', [])) or '`unassigned`'}",
        "",
        "Policy checks:",
        *list_lines([str(item) for item in intent.get("policy_checks", [])]),
        "",
        "Decision options:",
        *list_lines([str(item) for item in intent.get("decision_options", [])]),
        "",
        "Wendao refs:",
        *list_lines([str(item) for item in intent.get("source_refs", [])]),
        "",
        f"Intent: `{intent_path.as_posix()}`",
    ]
    return "\n".join(lines)


def build_initial_message(intent: dict, intent_path: pathlib.Path) -> str:
    if intent.get("kind") == "agenda_item":
        return render_agenda_message(intent, intent_path)
    if intent.get("kind") == "review_gate":
        return render_review_gate_message(intent, intent_path)
    return render_kanban_message(intent, intent_path)


def build_parent_entry(intent: dict, intent_path: pathlib.Path, thread_id: str | None = None) -> str:
    lines = [
        f"**{intent['title']}**",
        "",
        f"Kind: `{intent['kind']}`",
        f"State: `{display_state(intent)}`",
    ]
    if thread_id:
        lines.extend(["", f"Thread: <#{thread_id}>"])
    lines.extend(["", f"Intent: `{intent_path.as_posix()}`"])
    return "\n".join(lines)


def find_parent_entry(channel_id: str, thread_id: str, thread_name: str, token: str) -> dict | None:
    status, messages = request_json("GET", f"/channels/{channel_id}/messages?limit=100", token)
    if status != 200 or not isinstance(messages, list):
        return None
    for message in messages:
        content = str(message.get("content") or "")
        if thread_id in content or f"<#{thread_id}>" in content:
            return message
        if thread_name in content and "Intent:" in content:
            return message
    return None


def create_parent_message(channel_id: str, content: str, token: str) -> dict:
    status, message = request_json(
        "POST",
        f"/channels/{channel_id}/messages",
        token,
        {"content": content},
    )
    if status not in (200, 201):
        raise RuntimeError(f"failed to create parent work-item message: {message}")
    return message


def merge_tag_ids(thread: dict, applied_ids: list[str]) -> list[str]:
    merged = [str(tag_id) for tag_id in thread.get("applied_tags", [])]
    for tag_id in applied_ids:
        if tag_id not in merged:
            merged.append(tag_id)
    return merged


def update_thread_tags(thread: dict, applied_ids: list[str], token: str) -> dict:
    merged = merge_tag_ids(thread, applied_ids)
    if not merged:
        return thread
    status, body = request_json(
        "PATCH",
        f"/channels/{thread['id']}",
        token,
        {"applied_tags": merged},
    )
    if status != 200:
        raise RuntimeError(f"failed to update work-item tags: {body}")
    return body


def render_receipt(receipt: dict) -> str:
    lines = [
        'kind = "projection_receipt"',
        f"intent_kind = {toml_string(receipt['intent_kind'])}",
        f"status = {toml_string(receipt['status'])}",
        f"created_at = {toml_string(receipt['created_at'])}",
        "",
        "[source]",
        f"operation_path = {toml_string(receipt['operation_path'])}",
        f"action_id = {toml_string(receipt['action_id'])}",
        f"workflow_node_ref = {toml_string(receipt['workflow_node_ref'])}",
        f"graph_node_ref = {toml_string(receipt['graph_node_ref'])}",
        f"intent_path = {toml_string(receipt['intent_path'])}",
        f"source_refs = {toml_array(receipt['source_refs'])}",
        "",
        "[projection]",
        'mode = "runtime"',
        'runtime = "scripts/create_work_item_post.py"',
        f"display_state = {toml_string(receipt['display_state'])}",
        f"requested_tags = {toml_array(receipt['requested_tags'])}",
        f"applied_tags = {toml_array(receipt['applied_tags'])}",
        f"missing_tags = {toml_array(receipt['missing_tags'])}",
        "",
        "[discord]",
        f"server_id = {toml_string(receipt['server_id'])}",
        f"channel_key = {toml_string(receipt['channel_key'])}",
        f"channel_id = {toml_string(receipt['channel_id'])}",
        f"channel_type = {receipt['channel_type']}",
        f"thread_id = {toml_string(receipt['thread_id'])}",
        f"thread_name = {toml_string(receipt['thread_name'])}",
        f"initial_message_id = {toml_string(receipt['initial_message_id'])}",
        f"parent_message_id = {toml_string(receipt['parent_message_id'])}",
        f"visible_parent_entry = {str(receipt['visible_parent_entry']).lower()}",
        f"created = {str(receipt['created']).lower()}",
        "",
        "[verification]",
        f"command = {toml_string(receipt['command'])}",
        f"dedupe = {toml_string(receipt['dedupe'])}",
        "",
    ]
    return "\n".join(lines)


def default_receipt_path(intent_path: pathlib.Path, title: str) -> pathlib.Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return pathlib.Path(".run/receipts") / f"{slugify(intent_path.stem)}.{slugify(title)}.{timestamp}.toml"


def main() -> int:
    args = parse_args()
    intent_path = pathlib.Path(args.intent)
    intent = load_intent(intent_path)

    channel_key = str(intent["target"]).removeprefix("#")
    thread_name = str(intent["title"])
    state = display_state(intent)
    tags = requested_tags(intent)

    if args.dry_run:
        print(
            "DRY_RUN "
            f"{intent['kind']} target={channel_key} title={thread_name} "
            f"state={state} requested_tags={','.join(tags) or '-'}"
        )
        return 0

    token = required_env(
        ("TF_VAR_DISCORD_BOT_TOKEN", "DISCORD_BOT_TOKEN"),
        "TF_VAR_DISCORD_BOT_TOKEN",
    )
    server_id = required_env(
        ("TF_VAR_DISCORD_SERVER_ID", "DISCORD_SERVER_ID", "DISCORD_GUILD_ID", "TF_VAR_server_id", "server_id"),
        "TF_VAR_DISCORD_SERVER_ID",
    )

    channels_status, channels = request_json("GET", f"/guilds/{server_id}/channels", token)
    if channels_status != 200:
        print(f"failed to list guild channels: {channels}", file=sys.stderr)
        return 1

    target_channel = find_target_channel(channels, channel_key)
    channel_type = int(target_channel.get("type", -1))
    if channel_type not in (GUILD_TEXT, GUILD_FORUM, GUILD_MEDIA):
        print(
            f"target channel type {channel_type} does not support work-item posts",
            file=sys.stderr,
        )
        return 2

    active_status, active = request_json("GET", f"/guilds/{server_id}/threads/active", token)
    if active_status != 200:
        print(f"failed to list active threads: {active}", file=sys.stderr)
        return 1

    existing_thread = find_active_thread(
        active.get("threads", []),
        target_channel["id"],
        thread_name,
    )
    created = existing_thread is None
    initial_message_id = ""
    parent_message_id = ""
    visible_parent_entry = False
    applied_ids, applied_names, missing_tags = resolve_applied_tags(target_channel, tags)

    if existing_thread:
        thread = existing_thread
        if channel_type in (GUILD_FORUM, GUILD_MEDIA):
            thread = update_thread_tags(thread, applied_ids, token)
            visible_parent_entry = True
        elif channel_type == GUILD_TEXT:
            parent_message = find_parent_entry(target_channel["id"], thread["id"], thread_name, token)
            if parent_message is None:
                parent_message = create_parent_message(
                    target_channel["id"],
                    build_parent_entry(intent, intent_path, thread["id"]),
                    token,
                )
            parent_message_id = str(parent_message.get("id") or "")
            visible_parent_entry = True
    elif channel_type in (GUILD_FORUM, GUILD_MEDIA):
        payload = {
            "name": thread_name,
            "auto_archive_duration": 10080,
            "message": {"content": build_initial_message(intent, intent_path)},
        }
        if applied_ids:
            payload["applied_tags"] = applied_ids
        create_status, thread = request_json(
            "POST",
            f"/channels/{target_channel['id']}/threads",
            token,
            payload,
        )
        if create_status not in (200, 201):
            print(f"failed to create work-item forum post: {thread}", file=sys.stderr)
            return 1
        initial_message_id = str((thread.get("message") or {}).get("id") or "")
        parent_message_id = initial_message_id
        visible_parent_entry = True
    else:
        parent_message = create_parent_message(
            target_channel["id"],
            build_parent_entry(intent, intent_path),
            token,
        )
        parent_message_id = str(parent_message.get("id") or "")
        payload = {
            "name": thread_name,
            "auto_archive_duration": 10080,
        }
        create_status, thread = request_json(
            "POST",
            f"/channels/{target_channel['id']}/messages/{parent_message_id}/threads",
            token,
            payload,
        )
        if create_status not in (200, 201):
            print(f"failed to create work-item thread: {thread}", file=sys.stderr)
            return 1

        initial_message_id = parent_message_id
        visible_parent_entry = True

    receipt = {
        "intent_kind": str(intent["kind"]),
        "status": "applied",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "operation_path": args.operation_path,
        "action_id": args.action_id,
        "workflow_node_ref": args.workflow_node_ref or str((intent.get("workflow") or {}).get("workflow_node_ref", "")),
        "graph_node_ref": args.graph_node_ref or str((intent.get("workflow") or {}).get("graph_node_ref", "")),
        "intent_path": intent_path.as_posix(),
        "source_refs": [str(item) for item in intent.get("source_refs", [])],
        "display_state": state,
        "requested_tags": tags,
        "applied_tags": applied_names,
        "missing_tags": missing_tags,
        "server_id": server_id,
        "channel_key": channel_key,
        "channel_id": target_channel["id"],
        "channel_type": channel_type,
        "thread_id": thread["id"],
        "thread_name": thread.get("name", thread_name),
        "initial_message_id": initial_message_id,
        "parent_message_id": parent_message_id,
        "visible_parent_entry": visible_parent_entry,
        "created": created,
        "command": args.command_label,
        "dedupe": "active_thread_exact_name",
    }

    receipt_path = pathlib.Path(args.receipt_path) if args.receipt_path else default_receipt_path(intent_path, thread_name)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(render_receipt(receipt))

    print(f"work item thread id: {receipt['thread_id']}")
    print(f"created: {created}")
    if initial_message_id:
        print(f"initial message id: {initial_message_id}")
    if missing_tags:
        print("missing tags: " + ", ".join(missing_tags))
    print(f"receipt: {receipt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
