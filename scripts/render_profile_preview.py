#!/usr/bin/env python3
import argparse
import pathlib
import sys
import tomllib


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a compact Markdown preview for a vertical_community_profile TOML."
    )
    parser.add_argument(
        "profile",
        nargs="?",
        default="examples/intents/vertical_community.healthcare.toml",
        help="Path to a vertical_community_profile TOML file.",
    )
    parser.add_argument(
        "--output",
        help="Optional output path. When omitted, preview is written to stdout.",
    )
    return parser.parse_args()


def require_profile(path: pathlib.Path) -> dict:
    profile = tomllib.loads(path.read_text())
    if profile.get("kind") != "vertical_community_profile":
        raise SystemExit(f"{path} is not a vertical_community_profile")
    return profile


def render_forum_tags(title: str, tags_by_channel: dict) -> list[str]:
    if not tags_by_channel:
        return []
    lines = ["", f"{title} forum tags:", ""]
    for channel, tags in sorted(tags_by_channel.items()):
        lines.append("- `" + str(channel) + "`: " + ", ".join(f"`{tag}`" for tag in tags))
    return lines


def render(profile: dict) -> str:
    name = profile.get("name", "Vertical Community")
    domain = profile.get("domain", "unknown")
    review_mode = profile.get("review_mode", "unspecified")
    space = profile.get("space", {})
    governance = profile.get("governance", {})
    policy = profile.get("policy", {})
    roles = profile.get("roles", [])
    workflows = profile.get("workflows", [])

    lines = [
        f"# {name}",
        "",
        f"Domain: `{domain}`",
        f"Review: `{review_mode}`",
        "",
        "Channels:",
        "",
        "- text: " + ", ".join(f"`{item}`" for item in space.get("text_channels", [])),
        "- forum: " + ", ".join(f"`{item}`" for item in space.get("forum_channels", [])),
    ]

    lines.extend(render_forum_tags("Knowledge", space.get("forum_tags", {})))
    lines.extend(["", "Policy:", ""])

    if policy:
        lines.extend(f"- `{key}`: `{value}`" for key, value in sorted(policy.items()))
    else:
        lines.append("- none")

    if governance:
        lines.extend([
            "",
            "Governance:",
            "",
            f"- category: `{governance.get('category', 'Governance')}`",
            "- text: " + ", ".join(f"`{item}`" for item in governance.get("text_channels", [])),
            "- forum: " + ", ".join(f"`{item}`" for item in governance.get("forum_channels", [])),
            "- allowed roles: "
            + ", ".join(f"`{item}`" for item in governance.get("allowed_role_keys", [])),
        ])
        lines.extend(render_forum_tags("Governance", governance.get("forum_tags", {})))

    lines.extend(["", "Roles:", ""])
    if roles:
        lines.extend(f"- `{role.get('key', 'role')}`: {role.get('name', '')}" for role in roles)
    else:
        lines.append("- none")

    if governance.get("roles"):
        lines.extend(
            f"- `{role.get('key', 'role')}`: {role.get('name', '')}"
            for role in governance.get("roles", [])
        )

    lines.extend(["", "Workflows:", ""])
    if workflows:
        lines.extend(
            f"- `{workflow.get('goal', 'workflow')}` -> `{workflow.get('process_ref', '')}`"
            for workflow in workflows
        )
    else:
        lines.append("- none")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    profile_path = pathlib.Path(args.profile)
    preview = render(require_profile(profile_path))
    if args.output:
        pathlib.Path(args.output).write_text(preview)
    else:
        sys.stdout.write(preview)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
