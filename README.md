# Wendao Discord OpenTofu

Wendao Discord OpenTofu is an HCL-first library for building a governed
knowledge-oriented Discord workspace.

The project keeps the original `disco` idea clear:

- OpenTofu manages durable Discord structure such as channels, roles,
  permissions, and selected long-lived messages.
- Human users express knowledge-work intent instead of provider schema.
- Agents compile that intent, plus optional Wendao knowledge context, into
  reviewable HCL projections or runtime actions.
- Receipts record what changed and why.

## Current Surface

- `opentofu/discord/modules/knowledge_space`: category, text channels, forum
  channels, roles, and channel permission overrides.
- `opentofu/discord/modules/paper_announcement`: durable paper announcement
  message.
- `examples/intents`: draft user-layer manifest examples.
- `docs`: Johnny.Decimal documentation topology and project records.

## Validation

```shell
direnv exec . just check
```

For live plans and applies, provide Discord credentials through environment
variables:

```shell
TF_VAR_DISCORD_BOT_TOKEN=... TF_VAR_DISCORD_SERVER_ID=... direnv exec . just plan-example
```

Run the live preflight before applying:

```shell
direnv exec . just check-discord-auth
```

The basic example creates text channels, a paper discussion forum channel, a
`Paper Publisher` role, a channel permission override for `papers`, and one
durable paper announcement. The role is intentionally an identity label with no
guild-level permissions; publishing capability is granted at the channel
boundary.

Create or ensure a paper discussion post from an intent manifest:

```shell
direnv exec . just create-discussion-post
```

Discussion forum posts are runtime objects, not OpenTofu state. The command
writes a receipt under `.run/receipts`.

The intended documentation audit template command is:

```shell
wendao audit --template johnny-decimal
```

The current local devenv does not yet expose `wendao`; `docs/90_operations`
tracks that tooling gap.
