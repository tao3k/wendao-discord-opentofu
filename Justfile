set shell := ["bash", "-euo", "pipefail", "-c"]

discord_dir := "opentofu/discord"
knowledge_example := "opentofu/discord/examples/knowledge_space_basic"
vertical_profile_example := "opentofu/discord/examples/vertical_community_profile"
env_loader := "set -a; [ ! -f .env ] || source .env; set +a; export TF_VAR_DISCORD_BOT_TOKEN=\"${TF_VAR_DISCORD_BOT_TOKEN:-${DISCORD_BOT_TOKEN:-}}\"; export DISCORD_BOT_TOKEN=\"${DISCORD_BOT_TOKEN:-${TF_VAR_DISCORD_BOT_TOKEN}}\"; export TF_VAR_DISCORD_SERVER_ID=\"${TF_VAR_DISCORD_SERVER_ID:-${DISCORD_SERVER_ID:-${DISCORD_GUILD_ID:-${TF_VAR_server_id:-${server_id:-}}}}}\";"

default:
    @just --list

fmt:
    direnv exec . tofu fmt -recursive {{discord_dir}}

init-example:
    direnv exec . tofu -chdir={{knowledge_example}} init

init-vertical-profile-example:
    direnv exec . tofu -chdir={{vertical_profile_example}} init

validate-example:
    direnv exec . tofu -chdir={{knowledge_example}} validate

validate-vertical-profile-example:
    direnv exec . tofu -chdir={{vertical_profile_example}} validate

diff-check:
    git diff --check

docs-audit-template:
    direnv exec . wendao audit --template johnny-decimal

docs-audit:
    direnv exec . wendao audit --load wendao-episteme docs

check: fmt init-example init-vertical-profile-example validate-example validate-vertical-profile-example diff-check

plan-example:
    direnv exec . bash -lc '{{env_loader}} tofu -chdir={{knowledge_example}} plan'

apply-example:
    direnv exec . bash -lc '{{env_loader}} tofu -chdir={{knowledge_example}} apply -auto-approve'

check-discord-auth:
    direnv exec . bash -lc '{{env_loader}} python3 scripts/check_discord_auth.py'

create-discussion-post intent="examples/intents/discussion_post.toml" operation="examples/intents/knowledge_operation.publish_paper_with_discussion.toml" action="open_discussion" workflow_node="bpmn:ServiceTask.OpenPaperDiscussion" graph_node="petgraph:open_discussion":
    direnv exec . bash -lc '{{env_loader}} python3 scripts/create_discussion_post.py --intent {{intent}} --operation-path {{operation}} --action-id {{action}} --workflow-node-ref {{workflow_node}} --graph-node-ref {{graph_node}}'

create-work-item-post intent operation action workflow_node graph_node command_label="direnv exec . just create-work-item-post":
    direnv exec . bash -lc '{{env_loader}} python3 scripts/create_work_item_post.py --intent {{intent}} --operation-path {{operation}} --action-id {{action}} --workflow-node-ref {{workflow_node}} --graph-node-ref {{graph_node}} --command-label "{{command_label}}"'

create-agenda-item intent="examples/intents/agenda_item.attention_reading_session.toml" operation="examples/intents/knowledge_operation.agenda_session.toml" action="open_agenda_item" workflow_node="bpmn:ServiceTask.OpenAgendaItem" graph_node="petgraph:open_agenda_item":
    direnv exec . bash -lc '{{env_loader}} python3 scripts/create_work_item_post.py --intent {{intent}} --operation-path {{operation}} --action-id {{action}} --workflow-node-ref {{workflow_node}} --graph-node-ref {{graph_node}} --command-label "direnv exec . just create-agenda-item"'

create-kanban-card intent="examples/intents/kanban_card.replication_task.toml" operation="examples/intents/knowledge_operation.kanban_card.toml" action="open_card" workflow_node="bpmn:ServiceTask.OpenKanbanCard" graph_node="petgraph:open_kanban_card":
    direnv exec . bash -lc '{{env_loader}} python3 scripts/create_work_item_post.py --intent {{intent}} --operation-path {{operation}} --action-id {{action}} --workflow-node-ref {{workflow_node}} --graph-node-ref {{graph_node}} --command-label "direnv exec . just create-kanban-card"'

create-review-gate intent="examples/intents/review_gate.digest_promotion.toml" operation="examples/intents/knowledge_operation.digest_review.toml" action="open_review_gate" workflow_node="bpmn:UserTask.ReviewDigestPromotion" graph_node="petgraph:review_digest_promotion":
    direnv exec . bash -lc '{{env_loader}} python3 scripts/create_work_item_post.py --intent {{intent}} --operation-path {{operation}} --action-id {{action}} --workflow-node-ref {{workflow_node}} --graph-node-ref {{graph_node}} --command-label "direnv exec . just create-review-gate"'

create-scheduled-event intent="examples/intents/scheduled_event.attention_reading_session.toml" operation="examples/intents/knowledge_operation.agenda_session.toml" action="schedule_session" workflow_node="bpmn:ServiceTask.ScheduleSession" graph_node="petgraph:schedule_session":
    direnv exec . bash -lc '{{env_loader}} python3 scripts/create_scheduled_event.py --intent {{intent}} --operation-path {{operation}} --action-id {{action}} --workflow-node-ref {{workflow_node}} --graph-node-ref {{graph_node}} --command-label "direnv exec . just create-scheduled-event"'

dry-run-agenda-item intent="examples/intents/agenda_item.attention_reading_session.toml":
    python3 scripts/create_work_item_post.py --intent {{intent}} --dry-run

dry-run-kanban-card intent="examples/intents/kanban_card.replication_task.toml":
    python3 scripts/create_work_item_post.py --intent {{intent}} --dry-run

dry-run-review-gate intent="examples/intents/review_gate.digest_promotion.toml":
    python3 scripts/create_work_item_post.py --intent {{intent}} --dry-run

dry-run-scheduled-event intent="examples/intents/scheduled_event.attention_reading_session.toml":
    python3 scripts/create_scheduled_event.py --intent {{intent}} --dry-run

render-operation-preview operation="examples/intents/knowledge_operation.publish_paper_with_discussion.toml":
    python3 scripts/render_operation_preview.py {{operation}}

render-profile-preview profile="examples/intents/vertical_community.healthcare.toml":
    python3 scripts/render_profile_preview.py {{profile}}

sync-forum-tags profile="examples/intents/vertical_community.healthcare.toml":
    direnv exec . bash -lc '{{env_loader}} python3 scripts/sync_forum_tags.py --profile {{profile}}'

dry-run-forum-tags profile="examples/intents/vertical_community.healthcare.toml":
    direnv exec . bash -lc '{{env_loader}} python3 scripts/sync_forum_tags.py --profile {{profile}} --dry-run'

render-profile-tfvars profile="examples/intents/vertical_community.healthcare.toml" output=".run/tfvars/vertical_community.tfvars.json":
    python3 scripts/profile_to_tfvars.py {{profile}} --output {{output}}

plan-vertical-profile-example profile="examples/intents/vertical_community.healthcare.toml":
    direnv exec . bash -lc '{{env_loader}} python3 scripts/profile_to_tfvars.py {{profile}} --output .run/tfvars/vertical_community.tfvars.json && tofu -chdir={{vertical_profile_example}} plan -var-file="$PWD/.run/tfvars/vertical_community.tfvars.json"'

apply-vertical-profile-example profile="examples/intents/vertical_community.healthcare.toml":
    direnv exec . bash -lc '{{env_loader}} python3 scripts/profile_to_tfvars.py {{profile}} --output .run/tfvars/vertical_community.tfvars.json && tofu -chdir={{vertical_profile_example}} apply -auto-approve -var-file="$PWD/.run/tfvars/vertical_community.tfvars.json"'

clean-opentofu:
    rm -rf {{knowledge_example}}/.terraform {{vertical_profile_example}}/.terraform
