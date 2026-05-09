# Healthcare Evidence Community

Domain: `healthcare`
Review: `human_approval_required`

Channels:

- text: `announcements`, `general-discussion`, `knowledge`
- forum: `evidence-library`, `case-review`, `agenda`, `kanban`

Knowledge forum tags:

- `agenda`: `proposed`, `scheduled`, `in-session`, `done`, `follow-up`
- `case-review`: `deidentified-case`, `clinical-question`, `needs-review`, `resolved`
- `evidence-library`: `evidence`, `guideline`, `source-needed`, `needs-review`
- `kanban`: `todo`, `doing`, `review`, `blocked`, `done`

Policy:

- `case_review`: `deidentified_only`
- `destructive_changes`: `human_approval_required`
- `digest_publication`: `review_required`
- `medical_claims`: `evidence_required`
- `personal_advice`: `not_allowed`
- `phi`: `do_not_post`
- `runtime_discussion`: `receipt_required`

Governance:

- category: `Healthcare Governance`
- text: `moderation-log`, `agent-ops`, `privacy-checklist`
- forum: `review-queue`, `policy-decisions`, `incident-review`
- allowed roles: `reviewer`, `maintainer`, `privacy_steward`, `moderator`, `program_manager`, `agent_operator`

Governance forum tags:

- `incident-review`: `triage`, `investigating`, `resolved`, `follow-up`
- `policy-decisions`: `proposed`, `approved`, `deprecated`
- `review-queue`: `pending-review`, `needs-revision`, `approved`, `rejected`, `promote-to-knowledge`

Roles:

- `reader`: Reader
- `evidence_contributor`: Evidence Contributor
- `reviewer`: Clinical Reviewer
- `maintainer`: Healthcare Maintainer
- `privacy_steward`: Privacy Steward
- `moderator`: Healthcare Moderator
- `program_manager`: Program Manager
- `agent_operator`: Agent Operator

Workflows:

- `publish_evidence_with_discussion` -> `wendao://workflow/healthcare-evidence-review`
- `case_review_agenda` -> `wendao://workflow/healthcare-case-review-agenda`
- `digest_review_gate` -> `wendao://workflow/healthcare-digest-review`
- `moderation_incident` -> `wendao://workflow/healthcare-moderation-incident`
