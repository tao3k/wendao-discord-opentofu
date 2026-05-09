#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

import profile_to_tfvars


API_BASE = "https://discord.com/api/v10"
GUILD_FORUM = 15
GUILD_MEDIA = 16


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync desired forum tags from a vertical community profile into Discord."
    )
    parser.add_argument(
        "--profile",
        default="examples/intents/vertical_community.healthcare.toml",
        help="Path to a vertical_community_profile TOML file.",
    )
    parser.add_argument(
        "--receipt-path",
        default=None,
        help="Optional receipt output path. Defaults to .run/receipts/<profile>.<timestamp>.toml.",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Remove Discord forum tags that are not declared by the profile.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned tag changes without calling PATCH.",
    )
    return parser.parse_args()


def required_env(names: tuple[str, ...], label: str) -> str:
    for name in names:
        value = os.environ.get(name, "").removeprefix("Bot ").strip()
        if value:
            return value
    raise SystemExit(f"missing {label}")


def optional_env(names: tuple[str, ...]) -> str:
    for name in names:
        value = os.environ.get(name, "").removeprefix("Bot ").strip()
        if value:
            return value
    return ""


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
                time.sleep(float(error_body.get("retry_after", 1)))
                continue
            return error.code, error_body

    raise RuntimeError("unreachable retry state")


def slugify(value: str) -> str:
    return profile_to_tfvars.slug_key(value).replace("_", "-")


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def toml_array(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=True)


def by_channel_name(channels: list[dict]) -> dict[str, dict]:
    return {str(channel.get("name", "")).lower(): channel for channel in channels}


def normalize_existing_tag(tag: dict) -> dict:
    normalized = {
        "name": str(tag.get("name", "")),
        "moderated": bool(tag.get("moderated", False)),
    }
    for key in ("id", "emoji_id", "emoji_name"):
        if tag.get(key) is not None:
            normalized[key] = tag[key]
    return normalized


def build_available_tags(existing: list[dict], desired: list[str], prune: bool) -> tuple[list[dict], list[str], list[str], list[str]]:
    by_name = {str(tag.get("name", "")).lower(): tag for tag in existing}
    desired_lower = [tag.lower() for tag in desired]
    desired_set = set(desired_lower)
    created = [tag for tag in desired if tag.lower() not in by_name]
    applied = [str(by_name.get(tag.lower(), {"name": tag}).get("name", tag)) for tag in desired]
    preserved = [
        str(tag.get("name", ""))
        for tag in existing
        if str(tag.get("name", "")).lower() not in desired_set and not prune
    ]
    tags = [
        normalize_existing_tag(tag)
        for tag in existing
        if not prune or str(tag.get("name", "")).lower() in desired_set
    ]
    existing_lower = {str(tag.get("name", "")).lower() for tag in tags}
    for name in desired:
        if name.lower() not in existing_lower:
            tags.append({"name": name, "moderated": False})
            existing_lower.add(name.lower())
    if len(tags) > 20:
        raise SystemExit("Discord forum channels support at most 20 available tags.")
    return tags, applied, created, preserved


def render_receipt(receipt: dict) -> str:
    lines = [
        'kind = "forum_tag_sync_receipt"',
        f"status = {toml_string(receipt['status'])}",
        f"created_at = {toml_string(receipt['created_at'])}",
        f"source_profile = {toml_string(receipt['source_profile'])}",
        f"dry_run = {str(receipt['dry_run']).lower()}",
        f"prune = {str(receipt['prune']).lower()}",
        "",
        "[projection]",
        'mode = "runtime"',
        'runtime = "scripts/sync_forum_tags.py"',
        "",
        "[discord]",
        f"server_id = {toml_string(receipt['server_id'])}",
        "",
    ]
    for forum in receipt["forums"]:
        lines.extend([
            "[[forum]]",
            f"channel_key = {toml_string(forum['channel_key'])}",
            f"channel_name = {toml_string(forum['channel_name'])}",
            f"channel_id = {toml_string(forum['channel_id'])}",
            f"desired_tags = {toml_array(forum['desired_tags'])}",
            f"applied_tags = {toml_array(forum['applied_tags'])}",
            f"created_tags = {toml_array(forum['created_tags'])}",
            f"preserved_tags = {toml_array(forum['preserved_tags'])}",
            f"changed = {str(forum['changed']).lower()}",
            "",
        ])
    return "\n".join(lines)


def default_receipt_path(profile_path: pathlib.Path) -> pathlib.Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return pathlib.Path(".run/receipts") / f"forum-tags.{slugify(profile_path.stem)}.{timestamp}.toml"


def write_receipt(args: argparse.Namespace, profile_path: pathlib.Path, server_id: str, forums: list[dict]) -> pathlib.Path:
    receipt = {
        "status": "planned" if args.dry_run else "applied",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_profile": profile_path.as_posix(),
        "server_id": server_id,
        "dry_run": args.dry_run,
        "prune": args.prune,
        "forums": forums,
    }
    receipt_path = pathlib.Path(args.receipt_path) if args.receipt_path else default_receipt_path(profile_path)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(render_receipt(receipt))
    return receipt_path


def main() -> int:
    args = parse_args()
    profile_path = pathlib.Path(args.profile)
    profile = profile_to_tfvars.require_profile(profile_path)
    projected = profile_to_tfvars.project_profile(profile)
    desired_forums = {
        key: value
        for key, value in projected.get("forum_channels", {}).items()
        if value.get("tags")
    }
    if not desired_forums:
        print("no desired forum tags declared")
        return 0

    token_names = ("TF_VAR_DISCORD_BOT_TOKEN", "DISCORD_BOT_TOKEN")
    server_names = ("TF_VAR_DISCORD_SERVER_ID", "DISCORD_SERVER_ID", "DISCORD_GUILD_ID", "TF_VAR_server_id", "server_id")
    token = optional_env(token_names)
    server_id = optional_env(server_names)
    if not token or not server_id:
        if not args.dry_run:
            missing = "TF_VAR_DISCORD_BOT_TOKEN" if not token else "TF_VAR_DISCORD_SERVER_ID"
            raise SystemExit(f"missing {missing}")
        offline_receipts = []
        for channel_key, desired in desired_forums.items():
            desired_tags = [str(tag) for tag in desired.get("tags", [])]
            offline_receipts.append({
                "channel_key": channel_key,
                "channel_name": str(desired["name"]),
                "channel_id": "",
                "desired_tags": desired_tags,
                "applied_tags": [],
                "created_tags": desired_tags,
                "preserved_tags": [],
                "changed": True,
            })
            print(f"planned: #{desired['name']} tags={', '.join(desired_tags)}")
        receipt_path = write_receipt(args, profile_path, server_id, offline_receipts)
        print(f"receipt: {receipt_path}")
        return 0

    status, channels = request_json("GET", f"/guilds/{server_id}/channels", token)
    if status != 200 or not isinstance(channels, list):
        print(f"failed to list guild channels: {channels}", file=sys.stderr)
        return 1

    channels_by_name = by_channel_name(channels)
    forum_receipts: list[dict] = []

    for channel_key, desired in desired_forums.items():
        channel_name = str(desired["name"])
        channel = channels_by_name.get(channel_name.lower())
        if not channel:
            raise SystemExit(f"forum channel not found: {channel_name}")
        if int(channel.get("type", -1)) not in (GUILD_FORUM, GUILD_MEDIA):
            raise SystemExit(f"channel is not a forum/media channel: {channel_name}")

        existing = channel.get("available_tags") or []
        desired_tags = [str(tag) for tag in desired.get("tags", [])]
        available_tags, applied_tags, created_tags, preserved_tags = build_available_tags(
            existing,
            desired_tags,
            args.prune,
        )
        changed = bool(created_tags or args.prune)

        if changed and not args.dry_run:
            patch_status, body = request_json(
                "PATCH",
                f"/channels/{channel['id']}",
                token,
                {"available_tags": available_tags},
            )
            if patch_status != 200:
                print(f"failed to sync tags for {channel_name}: {body}", file=sys.stderr)
                return 1

        forum_receipts.append({
            "channel_key": channel_key,
            "channel_name": channel_name,
            "channel_id": str(channel["id"]),
            "desired_tags": desired_tags,
            "applied_tags": applied_tags,
            "created_tags": created_tags,
            "preserved_tags": preserved_tags,
            "changed": changed,
        })
        status_label = "would sync" if args.dry_run and changed else "synced" if changed else "already synced"
        print(f"{status_label}: #{channel_name} tags={', '.join(desired_tags)}")

    receipt_path = write_receipt(args, profile_path, server_id, forum_receipts)
    print(f"receipt: {receipt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
