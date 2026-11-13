# NoteLens Canonical Contracts v1.0.0

**Status:** frozen, 2026-11-13. **Coordinator:** B.
Human owner confirmations are recorded in [the freeze decision](../../docs/decisions/contract-freeze.md).

This is the single canonical JSON Schema Draft 2020-12/OpenAPI 3.1.1 source, promoted
from accepted P2 RC1 revision 3. All 29 definitions and operation behavior are unchanged;
only schema identifier/title/comment and API title/description became canonical labels.
[freeze.json](freeze.json) binds schema/API/fixture digests to dated A/B/C/D evidence.

- [schema.json](schema.json): canonical wire records.
- [openapi.json](openapi.json): service operations, correlation and health responses.
- [Shared fixtures](fixtures/README.md): 155 outcomes and 22 simulated exchanges.
- [Generated packages and Windows commands](../generated/README.md): runtime validation and compatibility evidence.
- [Owner scaffold handoff](../../docs/team/frozen-contracts-handoff.md).

Run scripts/project/check_contracts.py --require-freeze and generate_contracts.py --check
through the locked B tooling environment. Historical P1 inputs are in contracts/history/p1;
reproduce the old candidate tools in pinned commit 92626f5d037425f74eb65cadf1294a4d8bbfac35.
New generation uses this frozen directory. Do not edit generated copies as alternate schemas.

No clinical support, live detector, provider/model, spending or numeric operational policy
is implied. Fixture-only binding/mock development is approved; real language validation
still needs selection/evaluation before B-001, and ambiguity handling before B-003.
F-004/F-014, paid activation, deployment and service migration remain separately gated.
Future interface changes require affected-owner agreement and regenerated compatibility checks.
