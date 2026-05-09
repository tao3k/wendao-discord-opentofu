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
- `modules/paper_announcement`: creates a pinned or unpinned Discord message for
  a paper announcement using a structured embed.

## Validation

```shell
direnv exec . tofu fmt -recursive opentofu/discord
direnv exec . tofu -chdir=opentofu/discord/examples/knowledge_space_basic init
direnv exec . tofu -chdir=opentofu/discord/examples/knowledge_space_basic validate
```

Set `TF_VAR_DISCORD_BOT_TOKEN` only when planning or applying against a real
Discord server. Static formatting and validation do not need live Discord
credentials.
