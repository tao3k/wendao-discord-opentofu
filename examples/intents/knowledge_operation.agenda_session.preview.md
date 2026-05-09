# Plan a reading session for Attention Is All You Need

Goal: `agenda_session`
Workflow: `wendao` / `bpmn`
Process: `wendao://workflow/agenda-session`
Workflow node: `bpmn:SubProcess.AgendaSession`

Sources:

- `wendao://paper/attention-is-all-you-need`

Review: `plan_then_apply`

Actions:

- `open_agenda_item` -> `agenda` via runtime (`bpmn:ServiceTask.OpenAgendaItem`) using `examples/intents/agenda_item.attention_reading_session.toml`
- `schedule_session` -> `agenda` via runtime after `open_agenda_item` (`bpmn:ServiceTask.ScheduleSession`) using `examples/intents/scheduled_event.attention_reading_session.toml`
- `record_receipt` -> `projection_receipt` via record after `open_agenda_item`, `schedule_session` (`bpmn:ServiceTask.RecordAgendaReceipt`)

Receipts required: yes
