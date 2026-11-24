# D-009 attempt 10 preparation

Initial preparation record. Subsequently the missing private inputs were received,
verified and used for attempt 10. See [the measured outcome](final-report.md).
The sections below preserve the initial local audit, rather than current blockers.

The requested selection rule is one complete 26-case attempt on frozen main
`ebe37dbd217483a152d1c33e70e0ff9fe034a1fc`, after the fixes in PRs #48, #49 and #51.
All nine historical attempts remain disclosed in the A-owned run-attempt record.
The existing reduced-scope closure remains historical; this preparation does not
replace it with a claim of a completed full run.

## Verified local inputs

- Runtime-only manifest: `bbba7cc58f63d840fcb533475f7610d3df138c5d245f1482db8849ab38fafbda`.
- Runtime ZIP: `a96ebf7829e96be6cc213e45220a215e37a04f9fd4cbb4364b5b8c3a4ff024f7`.
- The separately supplied branch scorer was inspected. It reports structural
  validity and cited-source retrieval proxies, not semantic accuracy or Recall@5.

## Inputs absent from this machine

The supplied historical scoring-candidate archive does not contain the later
`qa-structure-references.json`, `retrieval-references.json`, or
`bind-qa-app-document-ids.py`. Expected reference hashes from the handoff are
`710198629438386052e0c75c90a86dd007ed5b95b8a1af9cd6c6af61f1695746` and
`7522ab71087161dff281d3c21ee92b422476e3cbeec7837a2aee88aa99843e47`.
The required C-008 fitted bundle/startup manifest and A corpus/tokenizer caches
were not found in the checked workspace and Downloads paths. A C-005 model is
available but must not be substituted for C-008.
No historical run directories were found at the handoff's local restricted path.

## Execution and reporting

Receive the missing private inputs before execution. Use a new UUID and exclusive
receipts; never reuse the first pass UUID or combine results with attempt 9.
The current A launcher requires one reserved retry; D retains zero retries.
Retain the supplied monetary caps and verify effective retry reservations offline.
Do not set account-pricing or model-readiness flags without evidence.
Report the first resulting attempt even if incomplete. Final extraction F1 and
independent semantic risk remain unmeasured. Preserve failed calls and uncertain
cost reservations. No paid call was made during this preparation.
