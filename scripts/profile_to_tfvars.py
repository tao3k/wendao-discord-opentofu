#!/usr/bin/env python3
import argparse
import json
import pathlib
import re
import sys
import tomllib


VIEW_CHANNEL = 1024
SEND_MESSAGES = 2048
MANAGE_MESSAGES = 8192
EMBED_LINKS = 16384
READ_MESSAGE_HISTORY = 65536
GOVERNANCE_ALLOW = VIEW_CHANNEL + SEND_MESSAGES + EMBED_LINKS + READ_MESSAGE_HISTORY
GOVERNANCE_STEWARD_ALLOW = GOVERNANCE_ALLOW + MANAGE_MESSAGES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Project a vertical_community_profile TOML into OpenTofu tfvars JSON."
    )
    parser.add_argument(
        "profile",
        nargs="?",
        default="examples/intents/vertical_community.healthcare.toml",
        help="Path to a vertical_community_profile TOML file.",
    )
    parser.add_argument(
        "--output",
        help="Optional output path. When omitted, JSON is written to stdout.",
    )
    parser.add_argument(
        "--variable-name",
        default="community_profile",
        help="Root OpenTofu variable name to emit.",
    )
    return parser.parse_args()


def require_profile(path: pathlib.Path) -> dict:
    profile = tomllib.loads(path.read_text())
    if profile.get("kind") != "vertical_community_profile":
        raise SystemExit(f"{path} is not a vertical_community_profile")
    return profile


def slug_key(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "channel"


def channel_topic(domain: str, channel_name: str, channel_kind: str, scope: str = "knowledge") -> str:
    return f"{domain} {scope} {channel_kind} channel: {channel_name}."


def channel_tags(channel_name: str, tags_by_name: dict | None) -> list[str]:
    if not tags_by_name:
        return []
    normalized = {
        str(key).lower(): [str(tag) for tag in value]
        for key, value in tags_by_name.items()
    }
    for key in (channel_name, slug_key(channel_name)):
        tags = normalized.get(key.lower())
        if tags:
            return tags
    return []


def project_channels(
    domain: str,
    names: list[str],
    channel_kind: str,
    offset: int = 0,
    category_key: str | None = None,
    scope: str = "knowledge",
    sync_perms_with_category: bool = True,
    tags_by_name: dict | None = None,
) -> dict:
    channels = {}
    for index, name in enumerate(names):
        key = slug_key(name)
        channel = {
            "name": name,
            "topic": channel_topic(domain, name, channel_kind, scope),
            "position": offset + index,
            "sync_perms_with_category": sync_perms_with_category,
        }
        if category_key:
            channel["category_key"] = category_key
        tags = channel_tags(name, tags_by_name)
        if tags and channel_kind == "forum":
            channel["tags"] = tags
        channels[key] = channel
    return channels


def project_roles(roles: list[dict]) -> dict:
    return {
        role.get("key", slug_key(role.get("name", "role"))): {
            "name": role.get("name", role.get("key", "Role")),
            "mentionable": role.get("mentionable", False),
        }
        for role in roles
    }


def merge_roles(*role_lists: list[dict]) -> dict:
    roles: dict = {}
    for role_list in role_lists:
        roles.update(project_roles(role_list))
    return roles


def project_workflows(workflows: list[dict]) -> dict:
    return {
        workflow.get("goal", f"workflow_{index}"): workflow.get("process_ref", "")
        for index, workflow in enumerate(workflows)
    }


def governance_permission_overrides(governance: dict, channel_keys: list[str]) -> dict:
    allowed_role_keys = governance.get("allowed_role_keys", [])
    steward_role_keys = set(governance.get("steward_role_keys", []))
    overrides: dict = {}

    for channel_key in channel_keys:
        overrides[f"{channel_key}_deny_everyone"] = {
            "channel_key": channel_key,
            "everyone": True,
            "deny": VIEW_CHANNEL,
        }
        for role_key in allowed_role_keys:
            allow = GOVERNANCE_STEWARD_ALLOW if role_key in steward_role_keys else GOVERNANCE_ALLOW
            overrides[f"{channel_key}_allow_{role_key}"] = {
                "channel_key": channel_key,
                "role_key": role_key,
                "allow": allow,
            }
    return overrides


def project_profile(profile: dict) -> dict:
    domain = profile.get("domain", "general")
    space = profile.get("space", {})
    governance = profile.get("governance", {})
    text_channels = space.get("text_channels", [])
    forum_channels = space.get("forum_channels", [])
    governance_key = slug_key(governance.get("category", "Governance")) if governance else ""
    governance_text_channels = governance.get("text_channels", [])
    governance_forum_channels = governance.get("forum_channels", [])

    projected_text_channels = project_channels(domain, text_channels, "text", 0)
    projected_forum_channels = project_channels(
        domain,
        forum_channels,
        "forum",
        len(text_channels),
        tags_by_name=space.get("forum_tags", {}),
    )
    governance_text = {}
    governance_forums = {}
    categories = {}
    permission_overrides = {}

    if governance:
        categories[governance_key] = {
            "name": governance.get("category", "Governance"),
            "position": governance.get("position", 1),
        }
        governance_text = project_channels(
            domain,
            governance_text_channels,
            "text",
            governance.get("text_position", 0),
            governance_key,
            "governance",
            False,
        )
        governance_forums = project_channels(
            domain,
            governance_forum_channels,
            "forum",
            governance.get("forum_position", len(governance_text_channels)),
            governance_key,
            "governance",
            False,
            governance.get("forum_tags", {}),
        )
        permission_overrides = governance_permission_overrides(
            governance,
            list(governance_text.keys()) + list(governance_forums.keys()),
        )

    return {
        "kind": profile.get("kind", "vertical_community_profile"),
        "name": profile.get("name", "Vertical Knowledge Community"),
        "domain": domain,
        "review_mode": profile.get("review_mode", "plan_then_apply"),
        "category": {
            "name": space.get("category", profile.get("name", "Vertical Knowledge")),
            "position": space.get("position", 0),
        },
        "categories": categories,
        "text_channels": {**projected_text_channels, **governance_text},
        "forum_channels": {**projected_forum_channels, **governance_forums},
        "roles": merge_roles(profile.get("roles", []), governance.get("roles", [])),
        "channel_permission_overrides": permission_overrides,
        "policies": profile.get("policy", {}),
        "workflows": project_workflows(profile.get("workflows", [])),
    }


def main() -> int:
    args = parse_args()
    profile = require_profile(pathlib.Path(args.profile))
    payload = {args.variable_name: project_profile(profile)}
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"

    if args.output:
        output_path = pathlib.Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
