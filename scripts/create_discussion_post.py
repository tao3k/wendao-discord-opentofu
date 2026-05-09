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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or ensure a Discord discussion thread/post from an intent manifest."
    )
    parser.add_argument(
        "--intent",
        default="examples/intents/discussion_post.toml",
        help="Path to discussion_post intent TOML.",
    )
    parser.add_argument(
        "--receipt-path",
        default=None,
        help="Optional receipt output path. Defaults to .run/receipts/<intent>.<timestamp>.toml.",
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
    if intent.get("kind") != "discussion_post":
        raise SystemExit(f"{path} is not a discussion_post intent")
    for key in ("target", "title", "prompt"):
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


def build_initial_message(intent: dict, intent_path: pathlib.Path) -> str:
    lines = [
        f"Paper discussion for `{intent.get('paper_ref', 'unknown-paper')}`.",
        "",
        intent["prompt"],
        "",
        f"Intent: `{intent_path.as_posix()}`",
    ]
    source_refs = intent.get("source_refs") or []
    if source_refs:
        lines.append("Sources: " + ", ".join(f"`{ref}`" for ref in source_refs))
    return "\n".join(lines)


def build_parent_announcement(intent: dict, intent_path: pathlib.Path, thread_id: str | None = None) -> str:
    lines = [
        f"**{intent['title']}**",
        "",
        f"Paper: `{intent.get('paper_ref', 'unknown-paper')}`",
        f"Prompt: {intent['prompt']}",
    ]
    if thread_id:
        lines.extend(["", f"Thread: <#{thread_id}>"])
    lines.extend(["", f"Intent: `{intent_path.as_posix()}`"])
    return "\n".join(lines)


def find_parent_announcement(
    channel_id: str,
    thread_id: str,
    thread_name: str,
    token: str,
) -> dict | None:
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
        raise RuntimeError(f"failed to create parent discussion message: {message}")
    return message


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "discussion-post"


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def render_receipt(receipt: dict) -> str:
    lines = [
        'kind = "projection_receipt"',
        'intent_kind = "discussion_post"',
        f"status = {toml_string(receipt['status'])}",
        f"created_at = {toml_string(receipt['created_at'])}",
        "",
        "[source]",
        f"intent_path = {toml_string(receipt['intent_path'])}",
        f"paper_ref = {toml_string(receipt['paper_ref'])}",
        "",
        "[projection]",
        'mode = "runtime"',
        'runtime = "scripts/create_discussion_post.py"',
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

    token = required_env(
        ("TF_VAR_DISCORD_BOT_TOKEN", "DISCORD_BOT_TOKEN"),
        "TF_VAR_DISCORD_BOT_TOKEN",
    )
    server_id = required_env(
        ("TF_VAR_DISCORD_SERVER_ID", "DISCORD_SERVER_ID", "DISCORD_GUILD_ID", "TF_VAR_server_id", "server_id"),
        "TF_VAR_DISCORD_SERVER_ID",
    )

    channel_key = str(intent["target"]).removeprefix("#")
    thread_name = str(intent["title"])
    initial_message = build_initial_message(intent, intent_path)

    if args.dry_run:
        print(f"DRY_RUN discussion_post target={channel_key} title={thread_name}")
        return 0

    channels_status, channels = request_json("GET", f"/guilds/{server_id}/channels", token)
    if channels_status != 200:
        print(f"failed to list guild channels: {channels}", file=sys.stderr)
        return 1

    target_channel = find_target_channel(channels, channel_key)
    channel_type = int(target_channel.get("type", -1))
    if channel_type not in (GUILD_TEXT, GUILD_FORUM, GUILD_MEDIA):
        print(
            f"target channel type {channel_type} does not support discussion posts",
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

    if existing_thread:
        thread = existing_thread
        if channel_type == GUILD_TEXT:
            parent_message = find_parent_announcement(
                target_channel["id"],
                thread["id"],
                thread_name,
                token,
            )
            if parent_message is None:
                parent_message = create_parent_message(
                    target_channel["id"],
                    build_parent_announcement(intent, intent_path, thread["id"]),
                    token,
                )
            parent_message_id = str(parent_message.get("id") or "")
            visible_parent_entry = True
    elif channel_type in (GUILD_FORUM, GUILD_MEDIA):
        payload = {
            "name": thread_name,
            "auto_archive_duration": 10080,
            "message": {"content": initial_message},
        }
        create_status, thread = request_json(
            "POST",
            f"/channels/{target_channel['id']}/threads",
            token,
            payload,
        )
        if create_status not in (200, 201):
            print(f"failed to create forum discussion post: {thread}", file=sys.stderr)
            return 1
        initial_message_id = str((thread.get("message") or {}).get("id") or "")
        parent_message_id = initial_message_id
        visible_parent_entry = True
    else:
        parent_message = create_parent_message(
            target_channel["id"],
            build_parent_announcement(intent, intent_path),
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
            print(f"failed to create discussion thread: {thread}", file=sys.stderr)
            return 1

        initial_message_id = parent_message_id
        visible_parent_entry = True

    receipt = {
        "status": "applied",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "intent_path": intent_path.as_posix(),
        "paper_ref": str(intent.get("paper_ref", "")),
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
        "command": "direnv exec . just create-discussion-post",
        "dedupe": "active_thread_exact_name",
    }

    receipt_path = pathlib.Path(args.receipt_path) if args.receipt_path else default_receipt_path(intent_path, thread_name)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(render_receipt(receipt))

    print(f"discussion thread id: {receipt['thread_id']}")
    print(f"created: {created}")
    if initial_message_id:
        print(f"initial message id: {initial_message_id}")
    print(f"receipt: {receipt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
