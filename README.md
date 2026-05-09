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
- `opentofu/discord/modules/vertical_community`: projects a vertical community
  profile into a managed knowledge space.
- `opentofu/discord/modules/paper_announcement`: durable paper announcement
  message.
- `examples/intents`: user-layer operation, intent, preview, and receipt
  examples.
- `docs`: Johnny.Decimal documentation topology and project records.

The user layer is profile-driven. A Wendao user should be able to start from a
vertical profile, such as healthcare or business, then let Wendao workflow
produce Discord projection operations for structure, paper workflows, agenda,
kanban, and receipts.

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

Create agenda and kanban forum posts from user-layer intents:

```shell
direnv exec . just create-agenda-item
direnv exec . just create-scheduled-event
direnv exec . just create-kanban-card
direnv exec . just create-review-gate
direnv exec . just sync-forum-tags
```

These commands create or reuse a forum post/card and write receipts that carry
the Wendao BPMN and petgraph refs. `sync-forum-tags` applies the profile's
declared forum tags to Discord, then the work-item runtime can attach them to
agenda items, kanban cards, and review gates.

Render the compact preview for a user-layer operation:

```shell
direnv exec . just render-operation-preview
```

Render the compact preview for a vertical community profile:

```shell
direnv exec . just render-profile-preview
```

Project a vertical community profile into OpenTofu variables and plan it:

```shell
direnv exec . just render-profile-tfvars examples/intents/vertical_community.healthcare.toml
direnv exec . just plan-vertical-profile-example examples/intents/vertical_community.healthcare.toml
```

Apply the HCL projection to a real server after reviewing the plan:

```shell
direnv exec . just apply-vertical-profile-example examples/intents/vertical_community.healthcare.toml
```

The intended documentation audit template command is:

```shell
wendao audit --template johnny-decimal
```

The current local devenv does not yet expose `wendao`; `docs/90_operations`
tracks that tooling gap.
