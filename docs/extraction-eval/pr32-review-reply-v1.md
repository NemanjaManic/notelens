Hi Goran,

I reviewed PR #32 at 7743fc87aafa94f42b6fd81e34a48612352da1f1 relative to #31.
Hosted key-free CI run 45277894601 is successful on that revision. I found no
blocking code issue in the narrow exact-hash synthetic replay admission and
mock-only guidance changes. The default language checks remain unchanged and
the added preparation regression covers exact, changed and public-scope inputs.
I did not rerun the platform locally.

Before I record the reported 16-case d41 replay as accepted app evidence, please
provide its exact runner/command and source hash, plus the sanitized private
receipt mapping each unchanged case to app SHA, d41 service SHA, profile,
request/output hashes, actual outcome and listener shutdown. The tracked launcher
CLI still uses the c7-pinned adapter; its new reviewed-hash parameter is currently
programmatic. A reproducible d41 runner may stay separate from the historical one.
No new provider generation is requested. Source texts and private outputs should
remain in the restricted handoff; a source-free receipt can carry their hashes.

Please distinguish the reported development replay from the 26-case final run.
Formal B-005 acceptance and D-009 final execution/scoring remain pending.

Thanks,
Milica

Draft prepared locally, not posted to GitHub or sent by the agent.

## Follow-up: reproducibility request resolved

The supplied D005-d41-app-recheck-repro-v1.zip now provides the exact separate
runner/adapter command and pinned receipt v3 at app 7743fc87. SHA256SUMS, runner
pins, app file hashes and all sixteen archived request/raw/output hashes verify.
The original request above is historical and no longer outstanding. This accepts
reproducible owner-reported development replay; D did not rerun the platform.
Formal B-005 and final D-009 remain open.
