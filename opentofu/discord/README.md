# Wendao Discord OpenTofu Library

This directory contains the OpenTofu-native Discord library for Wendao-managed
knowledge communities.

The library keeps long-lived Discord structure in HCL and leaves high-frequency
runtime posting to future Agent or bot adapters. Modules in this directory are
intended to be consumed through a Git source pinned to an exact commit:

```hcl
module "knowledge_space" {
  source = "git::https://github.com/tao3k/wendao-discord-opentofu.git//opentofu/discord/modules/knowledge_space?ref=<commit-sha>"

  server_id = var.server_id
}
```

Provider resolution is pinned through the OpenTofu Registry:

```hcl
terraform {
  required_providers {
    discord = {
      source  = "lucky3028/discord"
      version = "= 2.6.0"
    }
  }
}
```

## Modules

- `modules/knowledge_space`: creates a knowledge category, text channels,
  forum channels, optional roles, and optional channel permission overrides.
- `modules/vertical_community`: accepts a vertical community profile object and
  projects it into `knowledge_space` structure for healthcare, business, or
  other domain communities.
- `modules/paper_announcement`: creates a pinned or unpinned Discord message for
  a paper announcement using a structured embed.

Forum tags are declared in profile inputs and exposed in module outputs, but
the pinned provider does not expose `available_tags` on `discord_forum_channel`.
Use `direnv exec . just sync-forum-tags` to project those declared tags into a
real Discord server through the runtime API boundary.

## Validation

```shell
direnv exec . tofu fmt -recursive opentofu/discord
direnv exec . tofu -chdir=opentofu/discord/examples/knowledge_space_basic init
direnv exec . tofu -chdir=opentofu/discord/examples/knowledge_space_basic validate
direnv exec . python3 scripts/profile_to_tfvars.py examples/intents/vertical_community.healthcare.toml --output .run/tfvars/vertical_community.tfvars.json
direnv exec . tofu -chdir=opentofu/discord/examples/vertical_community_profile init
direnv exec . tofu -chdir=opentofu/discord/examples/vertical_community_profile validate
```

Set `TF_VAR_DISCORD_BOT_TOKEN` only when planning or applying against a real
Discord server. Static formatting and validation do not need live Discord
credentials.
