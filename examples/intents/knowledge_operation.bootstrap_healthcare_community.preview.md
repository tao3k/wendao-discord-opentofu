# Bootstrap a healthcare evidence community

Goal: `bootstrap_vertical_community`
Workflow: `wendao` / `bpmn`
Process: `wendao://workflow/bootstrap-vertical-community`
Workflow node: `bpmn:SubProcess.BootstrapVerticalCommunity`

Sources:

- `wendao://profile/healthcare-evidence-community`

Review: `human_approval_required`

Actions:

- `project_structure` -> `Healthcare Knowledge` via opentofu (`bpmn:ServiceTask.ProjectDiscordStructure`)
- `seed_agenda` -> `agenda` via runtime after `project_structure` (`bpmn:ServiceTask.SeedAgenda`) using `examples/intents/agenda_item.attention_reading_session.toml`
- `seed_kanban` -> `kanban` via runtime after `project_structure` (`bpmn:ServiceTask.SeedKanban`) using `examples/intents/kanban_card.replication_task.toml`
- `record_receipt` -> `projection_receipt` via record after `project_structure`, `seed_agenda`, `seed_kanban` (`bpmn:ServiceTask.RecordBootstrapReceipt`)

Receipts required: yes
