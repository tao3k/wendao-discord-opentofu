# Business Intelligence Community

Domain: `business`
Review: `plan_then_apply`

Channels:

- text: `announcements`, `market-discussion`, `knowledge`
- forum: `market-intelligence`, `decision-agenda`, `kanban`, `research-requests`

Policy:

- `decision_records`: `receipt_required`
- `destructive_changes`: `human_approval_required`
- `market_claims`: `source_required`
- `runtime_discussion`: `receipt_required`
- `sensitive_data`: `do_not_post_by_default`

Roles:

- `reader`: Reader
- `analyst`: Analyst
- `decision_reviewer`: Decision Reviewer

Workflows:

- `publish_market_brief_with_discussion` -> `wendao://workflow/business-market-brief`
- `decision_agenda` -> `wendao://workflow/business-decision-agenda`
