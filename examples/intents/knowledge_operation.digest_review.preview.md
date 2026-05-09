# Review a healthcare digest before promotion

Goal: `digest_review_gate`
Workflow: `wendao` / `bpmn`
Process: `wendao://workflow/healthcare-digest-review`
Workflow node: `bpmn:SubProcess.HealthcareDigestReview`

Sources:

- `wendao://paper/attention-is-all-you-need`
- `discord://thread/1502545186390016124`

Review: `human_approval_required`

Actions:

- `open_review_gate` -> `review-queue` via runtime (`bpmn:UserTask.ReviewDigestPromotion`) using `examples/intents/review_gate.digest_promotion.toml`
- `record_receipt` -> `projection_receipt` via record after `open_review_gate` (`bpmn:ServiceTask.RecordDigestReviewReceipt`)

Receipts required: yes
