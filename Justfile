set shell := ["bash", "-euo", "pipefail", "-c"]

discord_dir := "opentofu/discord"
knowledge_example := "opentofu/discord/examples/knowledge_space_basic"
env_loader := "set -a; [ ! -f .env ] || source .env; set +a; export TF_VAR_DISCORD_BOT_TOKEN=\"${TF_VAR_DISCORD_BOT_TOKEN:-${DISCORD_BOT_TOKEN:-}}\"; export DISCORD_BOT_TOKEN=\"${DISCORD_BOT_TOKEN:-${TF_VAR_DISCORD_BOT_TOKEN}}\"; export TF_VAR_DISCORD_SERVER_ID=\"${TF_VAR_DISCORD_SERVER_ID:-${DISCORD_SERVER_ID:-${DISCORD_GUILD_ID:-${TF_VAR_server_id:-${server_id:-}}}}}\";"

default:
    @just --list

fmt:
    direnv exec . tofu fmt -recursive {{discord_dir}}

init-example:
    direnv exec . tofu -chdir={{knowledge_example}} init

validate-example:
    direnv exec . tofu -chdir={{knowledge_example}} validate

diff-check:
    git diff --check

docs-audit-template:
    direnv exec . wendao audit --template johnny-decimal

docs-audit:
    direnv exec . wendao audit --load wendao-episteme docs

check: fmt init-example validate-example diff-check

plan-example:
    direnv exec . bash -lc '{{env_loader}} tofu -chdir={{knowledge_example}} plan'

apply-example:
    direnv exec . bash -lc '{{env_loader}} tofu -chdir={{knowledge_example}} apply -auto-approve'

check-discord-auth:
    direnv exec . bash -lc '{{env_loader}} python3 scripts/check_discord_auth.py'

create-discussion-post intent="examples/intents/discussion_post.toml":
    direnv exec . bash -lc '{{env_loader}} python3 scripts/create_discussion_post.py --intent {{intent}}'

clean-opentofu:
    rm -rf {{knowledge_example}}/.terraform
