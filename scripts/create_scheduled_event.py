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
from datetime import datetime, timedelta, timezone


API_BASE = "https://discord.com/api/v10"
GUILD_ONLY = 2
ENTITY_TYPES = {
    "stage_instance": 1,
    "voice": 2,
    "external": 3,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or ensure a Discord scheduled event from an intent manifest."
    )
    parser.add_argument(
        "--intent",
        default="examples/intents/scheduled_event.attention_reading_session.toml",
        help="Path to scheduled_event intent TOML.",
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
        default="direnv exec . just create-scheduled-event",
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


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise SystemExit(f"timestamp must include timezone offset: {value}")
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def discord_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_intent(path: pathlib.Path) -> dict:
    intent = tomllib.loads(path.read_text())
    if intent.get("kind") != "scheduled_event":
        raise SystemExit(f"{path} is not a scheduled_event intent")
    for key in ("title", "scheduled_start_time"):
        if not str(intent.get(key, "")).strip():
            raise SystemExit(f"{path} is missing required field: {key}")
    entity_type = str(intent.get("entity_type", "external"))
    if entity_type not in ENTITY_TYPES:
        raise SystemExit(f"{path} has unsupported entity_type: {entity_type}")
    if entity_type != "external":
        raise SystemExit("only external scheduled events are supported in this runtime slice")
    if not str(intent.get("location", "")).strip():
        raise SystemExit(f"{path} is missing required field for external event: location")
    return intent


def event_times(intent: dict) -> tuple[datetime, datetime]:
    start = parse_timestamp(str(intent["scheduled_start_time"]))
    if intent.get("scheduled_end_time"):
        end = parse_timestamp(str(intent["scheduled_end_time"]))
    else:
        duration = int(intent.get("duration_minutes", 60))
        end = start + timedelta(minutes=duration)
    if end <= start:
        raise SystemExit("scheduled_end_time must be after scheduled_start_time")
    return start, end


def find_existing_event(events: list[dict], name: str, start: datetime) -> dict | None:
    target_start = discord_timestamp(start)
    for event in events:
        if event.get("name") != name:
            continue
        event_start = str(event.get("scheduled_start_time", ""))
        if discord_timestamp(parse_timestamp(event_start)) == target_start:
            return event
    return None


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "scheduled-event"


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def toml_array(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=True)


def render_receipt(receipt: dict) -> str:
    lines = [
        'kind = "projection_receipt"',
        'intent_kind = "scheduled_event"',
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
        'runtime = "scripts/create_scheduled_event.py"',
        f"entity_type = {toml_string(receipt['entity_type'])}",
        f"location = {toml_string(receipt['location'])}",
        "",
        "[discord]",
        f"server_id = {toml_string(receipt['server_id'])}",
        f"scheduled_event_id = {toml_string(receipt['scheduled_event_id'])}",
        f"scheduled_event_name = {toml_string(receipt['scheduled_event_name'])}",
        f"scheduled_start_time = {toml_string(receipt['scheduled_start_time'])}",
        f"scheduled_end_time = {toml_string(receipt['scheduled_end_time'])}",
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
    start, end = event_times(intent)
    name = str(intent["title"])
    entity_type = str(intent.get("entity_type", "external"))
    location = str(intent["location"])

    if args.dry_run:
        print(
            "DRY_RUN scheduled_event "
            f"name={name} start={discord_timestamp(start)} end={discord_timestamp(end)} "
            f"entity_type={entity_type} location={location}"
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

    events_status, events = request_json("GET", f"/guilds/{server_id}/scheduled-events", token)
    if events_status != 200 or not isinstance(events, list):
        print(f"failed to list scheduled events: {events}", file=sys.stderr)
        return 1

    existing_event = find_existing_event(events, name, start)
    created = existing_event is None

    if existing_event:
        event = existing_event
    else:
        payload = {
            "name": name,
            "description": str(intent.get("description", "")),
            "privacy_level": GUILD_ONLY,
            "scheduled_start_time": discord_timestamp(start),
            "scheduled_end_time": discord_timestamp(end),
            "entity_type": ENTITY_TYPES[entity_type],
            "entity_metadata": {"location": location},
        }
        create_status, event = request_json(
            "POST",
            f"/guilds/{server_id}/scheduled-events",
            token,
            payload,
        )
        if create_status not in (200, 201):
            print(f"failed to create scheduled event: {event}", file=sys.stderr)
            return 1

    receipt = {
        "status": "applied",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "operation_path": args.operation_path,
        "action_id": args.action_id,
        "workflow_node_ref": args.workflow_node_ref or str((intent.get("workflow") or {}).get("workflow_node_ref", "")),
        "graph_node_ref": args.graph_node_ref or str((intent.get("workflow") or {}).get("graph_node_ref", "")),
        "intent_path": intent_path.as_posix(),
        "source_refs": [str(item) for item in intent.get("source_refs", [])],
        "entity_type": entity_type,
        "location": location,
        "server_id": server_id,
        "scheduled_event_id": str(event.get("id", "")),
        "scheduled_event_name": str(event.get("name", name)),
        "scheduled_start_time": discord_timestamp(parse_timestamp(str(event.get("scheduled_start_time", discord_timestamp(start))))),
        "scheduled_end_time": discord_timestamp(parse_timestamp(str(event.get("scheduled_end_time", discord_timestamp(end))))),
        "created": created,
        "command": args.command_label,
        "dedupe": "scheduled_event_name_and_start_time",
    }

    receipt_path = pathlib.Path(args.receipt_path) if args.receipt_path else default_receipt_path(intent_path, name)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(render_receipt(receipt))

    print(f"scheduled event id: {receipt['scheduled_event_id']}")
    print(f"created: {created}")
    print(f"start: {receipt['scheduled_start_time']}")
    print(f"receipt: {receipt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
