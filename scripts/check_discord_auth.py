#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request


REQUIRED_GUILD_PERMISSIONS = {
    "manage_channels": 1 << 4,
    "manage_roles": 1 << 28,
    "view_channel": 1 << 10,
    "read_message_history": 1 << 16,
    "send_messages": 1 << 11,
    "embed_links": 1 << 14,
    "create_public_threads": 1 << 35,
    "send_thread_messages": 1 << 38,
}

ADMINISTRATOR = 1 << 3


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"missing {name}")
    return value


def get_json(url: str, token: str):
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bot {token}",
            "User-Agent": "wendao-discord-opentofu-check/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        try:
            body = json.loads(error.read().decode())
        except Exception:
            body = {"message": "<non-json body>"}
        return error.code, body


def main() -> int:
    token = (
        os.environ.get("TF_VAR_DISCORD_BOT_TOKEN")
        or os.environ.get("DISCORD_BOT_TOKEN")
        or ""
    ).removeprefix("Bot ").strip()
    if not token:
        raise SystemExit("missing TF_VAR_DISCORD_BOT_TOKEN")
    server_id = (
        os.environ.get("TF_VAR_DISCORD_SERVER_ID")
        or os.environ.get("TF_VAR_server_id")
        or ""
    ).strip()
    if not server_id:
        raise SystemExit("missing TF_VAR_DISCORD_SERVER_ID")

    me_status, me = get_json("https://discord.com/api/v10/users/@me", token)
    print(f"users/@me status: {me_status}")
    if me_status != 200:
        print(f"error: {me.get('message', '<unknown>')}")
        return 1

    print(f"bot id: {me.get('id', '<unknown>')}")

    guild_status, guilds = get_json("https://discord.com/api/v10/users/@me/guilds", token)
    print(f"users/@me/guilds status: {guild_status}")
    if guild_status != 200:
        print(f"guild error: {guilds.get('message', '<unknown>')}")
        return 1

    target_guild = next((guild for guild in guilds if guild.get("id") == server_id), None)
    found = target_guild is not None
    print(f"target server visible to bot: {found}")
    print(f"visible guild count: {len(guilds)}")
    if not target_guild:
        return 2

    permissions = int(target_guild.get("permissions") or 0)
    has_administrator = (permissions & ADMINISTRATOR) == ADMINISTRATOR
    missing = [
        name
        for name, bit in REQUIRED_GUILD_PERMISSIONS.items()
        if not has_administrator and (permissions & bit) != bit
    ]

    print(f"administrator permission: {has_administrator}")
    print(f"required example permissions satisfied: {not missing}")
    if missing:
        print(f"missing permissions: {', '.join(missing)}")
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
