#!/usr/bin/env python3
import argparse
import pathlib
import sys
import tomllib


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a compact Markdown preview for a knowledge_operation TOML."
    )
    parser.add_argument(
        "operation",
        nargs="?",
        default="examples/intents/knowledge_operation.publish_paper_with_discussion.toml",
        help="Path to a knowledge_operation TOML file.",
    )
    parser.add_argument(
        "--output",
        help="Optional output path. When omitted, preview is written to stdout.",
    )
    return parser.parse_args()


def require_operation(path: pathlib.Path) -> dict:
    operation = tomllib.loads(path.read_text())
    if operation.get("kind") != "knowledge_operation":
        raise SystemExit(f"{path} is not a knowledge_operation")
    return operation


def render(operation: dict) -> str:
    title = operation.get("title", "Knowledge Operation")
    goal = operation.get("goal", "unknown")
    review_mode = operation.get("review_mode", "unspecified")
    receipt_required = "yes" if operation.get("receipt_required") else "no"
    workflow = operation.get("workflow", {})
    source_refs = operation.get("context", {}).get("source_refs", [])
    actions = operation.get("actions", [])

    lines = [
        f"# {title}",
        "",
        f"Goal: `{goal}`",
        f"Workflow: `{workflow.get('engine', 'none')}` / `{workflow.get('model', 'none')}`",
    ]

    if workflow.get("process_ref"):
        lines.append(f"Process: `{workflow['process_ref']}`")
    if workflow.get("node_ref"):
        lines.append(f"Workflow node: `{workflow['node_ref']}`")

    lines.extend([
        "",
        "Sources:",
        "",
    ])

    if source_refs:
        lines.extend(f"- `{source_ref}`" for source_ref in source_refs)
    else:
        lines.append("- none")

    lines.extend(["", f"Review: `{review_mode}`", "", "Actions:", ""])

    for action in actions:
        action_id = action.get("id", "unnamed")
        target = action.get("target") or action.get("kind", "unknown")
        mode = action.get("mode", "unknown")
        depends_on = action.get("depends_on", [])
        workflow_node_ref = action.get("workflow_node_ref")
        intent_path = action.get("intent_path")
        suffix = f" after {', '.join(f'`{item}`' for item in depends_on)}" if depends_on else ""
        workflow_suffix = f" (`{workflow_node_ref}`)" if workflow_node_ref else ""
        intent_suffix = f" using `{intent_path}`" if intent_path else ""
        lines.append(f"- `{action_id}` -> `{target}` via {mode}{suffix}{workflow_suffix}{intent_suffix}")

    lines.extend(["", f"Receipts required: {receipt_required}", ""])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    operation_path = pathlib.Path(args.operation)
    preview = render(require_operation(operation_path))
    if args.output:
        pathlib.Path(args.output).write_text(preview)
    else:
        sys.stdout.write(preview)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
