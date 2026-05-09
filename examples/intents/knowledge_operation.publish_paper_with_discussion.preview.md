# Publish and discuss Attention Is All You Need

Goal: `publish_paper_with_discussion`
Workflow: `wendao` / `bpmn`
Process: `wendao://workflow/publish-paper-with-discussion`
Workflow node: `bpmn:SubProcess.PublishPaperWithDiscussion`

Sources:

- `wendao://paper/attention-is-all-you-need`

Review: `plan_then_apply`

Actions:

- `announce_paper` -> `papers` via opentofu (`bpmn:ServiceTask.AnnouncePaper`)
- `open_discussion` -> `paper-discussion-forum` via runtime after `announce_paper` (`bpmn:ServiceTask.OpenPaperDiscussion`)
- `record_receipt` -> `projection_receipt` via record after `announce_paper`, `open_discussion` (`bpmn:ServiceTask.RecordDiscordReceipt`)

Receipts required: yes
