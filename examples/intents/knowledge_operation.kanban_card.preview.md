# Track a replication task as a Discord kanban card

Goal: `kanban_card`
Workflow: `wendao` / `bpmn`
Process: `wendao://workflow/kanban-card`
Workflow node: `bpmn:SubProcess.KanbanCardProjection`

Sources:

- `wendao://paper/attention-is-all-you-need`
- `wendao://task/replicate-transformer-baseline`

Review: `plan_then_apply`

Actions:

- `open_card` -> `kanban` via runtime (`bpmn:ServiceTask.OpenKanbanCard`) using `examples/intents/kanban_card.replication_task.toml`
- `set_initial_state` -> `kanban` via runtime after `open_card` (`bpmn:ServiceTask.SetInitialKanbanState`)
- `record_receipt` -> `projection_receipt` via record after `open_card`, `set_initial_state` (`bpmn:ServiceTask.RecordKanbanReceipt`)

Receipts required: yes
