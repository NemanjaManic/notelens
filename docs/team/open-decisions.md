# Open Decisions Before Implementation

**Recorded**: 2026-11-10. These are pending decisions, not approved defaults.
The source prompt remains authoritative. This register does not reopen confirmed
language, workstream ownership, Python service boundaries, dataset choices or deadline.

| Decision | Responsible workstream | Must be resolved before | Current state |
| --- | --- | --- | --- |
| Exact API spending cap, provider/account authorization and enforceable usage limits | B with A/D and user | Any paid provider activation or live evaluation | Small budget exists; amount and credentials not provided. |
| Hosting accounts, Python host, persistence and service authentication | B with A/C/D and user | Plan freeze for deployment; any external deployment | Verify official constraints and propose arrangement; no paid host is approved. |
| Submitted-document retention | B | Implementation accepting user-supplied documents | Resolved by user on 2026-11-10: server memory only, at most 60 minutes; delete on expiry/restart. Built-in public examples may remain versioned. Remaining session controls still need a decision. |
| Upload size/text limits | B | Input implementation | Resolved by user on 2026-11-10: at most 2 MiB (2,097,152 bytes) per PDF and 100,000 Unicode code points per document. Reject, do not truncate. |
| Request/history limits and operational timeouts | B with affected owners and user | Real provider/integration activation | Require explicit configuration decisions; no invented numbers. Unconfigured paid/live execution remains disabled. |
| Substantive classification/extraction/retrieval/answer thresholds | All, coordinated by D | Acceptance decision after first development measurement | Target 2026-11-14; keep unset until measured and reviewed. |
| Canonical contract field/error details and contract version freeze | B collects A/C/D proposals | Parallel business implementation | Draft JSON Schema/OpenAPI proposals exist in contracts/v1; owner review, freeze, semantic fixtures and generated bindings remain pending. |
| Exact dataset counts, class mapping, split proportions and duplicate criteria | C, with A/D consumers | Published split manifests and benchmark use | Must be measured and documented, not copied from source plans. |
| Corpus snapshot, permitted distribution and actual answerable QA topics | A with D | Corpus redistribution and retrieval benchmark freeze | Review sources/licenses and measure; no corpus downloaded in this package. |
| Annotation assignment IDs, dev/final portions and exact QA counts | D with C and all members | Annotation/evaluation execution | Targets are known; IDs/counts require actual manifests. |
| Constitution ratification date | User/team, maintained by B | Reporting constitution as ratified | Draft generated; user has approved preparation, not reviewed the resulting text. |
| Real member names/GitHub handles | User/team | CODEOWNERS populated with identities | A is the repository creator; colleagues will be invited by the user. |
| Repository code license | User/team, recorded by B | Adding a license or declaring reuse terms | No project license selected. Public visibility does not select a license. |
| Teammates' operating systems | B with team | Onboarding runbook | Resolved on 2026-11-10: all four use Windows. PowerShell primary, Git Bash with powershell.exe secondary. Actual application startup remains deferred. |

A pending operational choice does not authorize a fallback. Ask a focused question when its
dependent plan or implementation requires it; continue independent approved work. Names,
accounts and provider budgets do not block key-free specifications/mocks. The two source
PDFs are unavailable; the supplied prompt explicitly permits preparation without them.
