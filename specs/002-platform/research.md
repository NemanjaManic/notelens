# Research: Complete Frontend and Integration

**Owner**: B. **Checked**: 2026-11-10. **Status**: proposed design, not experiment results.

Primary source details and retrieval limitations are recorded in the
[shared feasibility review](../../docs/decisions/technical-feasibility.md).

## Retention/input policies

- **Decision**: User approved memory-only documents with absolute 60-minute lifetime, 2 MiB PDFs and 100,000 code points; reject excess input.
- **Rationale**: Explicit answers on 2026-11-10, recorded in spec clarifications.
- **Alternatives considered**: Persistence, sliding renewal beyond 60 minutes or silent truncation are not approved.

## State and routing

- **Decision**: One local state-owning web process; keep all secrets/service tokens server-side. Document/literature/mixed/none routing.
- **Rationale**: Matches memory policy and independent service ownership.
- **Alternatives considered**: Multi-instance state sharing needs a new approved design; do not silently add a database.

## Canonicalization proposal

- **Decision**: nfc-lf-v1 and exact SHA256/code-point evidence rules are proposed in contracts/v1.
- **Rationale**: Cross-language highlighting requires deterministic text.
- **Alternatives considered**: No downstream trimming or UTF-16-as-code-point indexing.

## Cloud option

- **Decision**: Single suitable host is the smallest candidate; Vercel plus Python hosting is an alternative, not frozen.
- **Rationale**: Official runtime review supports local feasibility; accounts and cost remain unknown.
- **Alternatives considered**: No paid host or implicit durable serverless filesystem.


## Activation and empirical gates

No source facts are inferred from unreadable data pages. Acquisition audits decide actual
counts, permitted redistribution, duplicate/split feasibility and topic/QA evidence.
No live model ID, account quota, price, timeout/retry/rate policy or quality threshold is
silently chosen. Local mocks need none of those paid/live settings.
This design is complete for local preparation; deployment and live-provider configuration
must remain blocked until the corresponding owner/user approval and actual checks.
