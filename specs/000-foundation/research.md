# Research: Shared Foundation

**Owner**: B. **Checked**: 2026-11-10. **Status**: proposed design, not experiment results.

Primary source details and retrieval limitations are recorded in the
[shared feasibility review](../../docs/decisions/technical-feasibility.md).

## Shared schema and fixture ownership

- **Decision**: B maintains contracts/v1; A/C/D review interfaces. Freeze is an explicit later approval/checkpoint.
- **Rationale**: Avoid conflicting hand-maintained schemas; independent consumers need one stable meaning.
- **Alternatives considered**: Separate per-service schema forks would duplicate authority.

## Mock boundary

- **Decision**: Scaffold all three Python projects and the web app once; label every mock output and lazy-load real providers.
- **Rationale**: Modules can start independently and routine checks need no secrets.
- **Alternatives considered**: A real provider-dependent foundation would block the team.

## Approval boundary

- **Decision**: This stage writes design/tasks only; runnable scaffold, commit/push and live activation are separate approvals.
- **Rationale**: Matches the user's explicit staging instructions.
- **Alternatives considered**: Do not treat a specification or schema draft as implementation.

## Scope/working copies

- **Decision**: Separate feature contexts and branches from one checked base, with member annotation exceptions.
- **Rationale**: Reduces shared-file conflicts.
- **Alternatives considered**: A branch name alone does not select a Spec Kit feature.


## Activation and empirical gates

No source facts are inferred from unreadable data pages. Acquisition audits decide actual
counts, permitted redistribution, duplicate/split feasibility and topic/QA evidence.
No live model ID, account quota, price, timeout/retry/rate policy or quality threshold is
silently chosen. Local mocks need none of those paid/live settings.
This design is complete for local preparation; deployment and live-provider configuration
must remain blocked until the corresponding owner/user approval and actual checks.
