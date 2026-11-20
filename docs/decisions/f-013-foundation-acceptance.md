# F-013 foundation acceptance review

**Review coordinator** B. **Decision status** Constitution ratified. Mock foundation independently accepted with no exceptions.

Review the shared foundation at commit
`754f4bb525ca08c93f4389737076fbeaa868513d` and
[constitution v1.0.0](../../.specify/memory/constitution.md).
The scope is the key-free mock foundation, frozen contracts, ownership gates,
and member onboarding. The final publication inventory is verified separately
during F-007.

## Evidence for review

- [Frozen contracts and bindings](../team/frozen-contracts-handoff.md) define
  the interface and exact canonical evidence checks. The constitution preserves
  English output, owner isolation, and public/synthetic input limits.
- The [mock startup runbook](../platform/f-005-mock-startup.md) covers the
  synthetic report, evidence links, mixed answers, and owned-process shutdown.
  The [F-011 closure](../platform/f-011-health-verification-plan.md#f-011-closure-2026-11-19)
  records 213 key-free HTTP cases on its reviewed checkpoint.
- [PR #10](https://github.com/NemanjaManic/notelens/pull/10) received independent
  approval and passed hosted CI before publishing the updated handoffs,
  F-010 evidence and the F-006 verifier. Its approval covered those changes.
  F-013's separate acceptance is recorded below.

On 2026-11-20, Nemanja (A) reported independently verifying startup and
shutdown, the English demo notices, evidence and source links, ownership
rules, and all four member handoffs. He accepted the key-free mock foundation
at `754f4bb` for F-013 with no exceptions.

## Review decisions requested

1. Ask the user or team to ratify constitution v1.0.0 at the named commit.
   Record the reviewing human, decision date and review reference. Update
   the constitution's ratification date only after the recorded decision.
2. Ask an independent reviewer from A, C or D to accept the named mock
   foundation or list explicit exceptions. Review the English demo notices,
   unchanged canonical text and claim provenance, ownership gates, key-free
   startup and cleanup, and the working-copy and handoff instructions.
   For an exception, record its approved limits, owner and follow-up.

Pending work includes the F-007 inventory refresh for later merged RAG files.
D's newer evaluation candidate was verified separately at `66ee547`.
[PR #11](https://github.com/NemanjaManic/notelens/pull/11) tracks its verified
inventory update outside this reviewed tree. C's provisional split, real
module integrations, live providers, deployment and final evaluation have
their own gates.

## Acceptance record

Keep the decision fields null until people have actually reviewed the named
basis. For `constitution_review`, use decision `ratified` and record a named
reviewer, an ISO date and a review reference. For `foundation_review`, use
`accepted` or `accepted_with_exceptions`, reviewer A, C or D, an ISO date,
a review reference, and the approved exception list. Use an empty list when
the reviewer accepts without exceptions.

```json
{
  "reviewed_commit": "754f4bb525ca08c93f4389737076fbeaa868513d",
  "constitution_sha256": "2f19be05723381540a4c498ae2f817bb62e211cccbb9ab654f7a9e9b2cf87966",
  "constitution_review": {
    "decision": "ratified",
    "reviewer": "Goran Suvačarev",
    "date": "2026-11-20",
    "evidence": "Explicit ratification in the F-013 coordinator conversation on 2026-11-20. Goran ratified v1.0.0 as written at 754f4bb, effective that day."
  },
  "foundation_review": {
    "decision": "accepted",
    "reviewer": "A",
    "date": "2026-11-20",
    "evidence": "Nemanja's independent review message supplied in the F-013 coordinator conversation on 2026-11-20. He accepted the key-free mock foundation at 754f4bb for F-013 with no exceptions.",
    "exceptions": []
  }
}
```

After both decisions are recorded, run:

```powershell
uv run --locked --offline --directory scripts/project python -B check_handoffs.py --require-reviewed-foundation
```

The checker validates record consistency, the reviewed Git reference, the
constitution digest and ratification date. The cited human decisions supply
the authority. After F-013, F-007 verifies the final inventory and working-copy
instructions. F-014 still requires separate authorization to publish the SHA.
