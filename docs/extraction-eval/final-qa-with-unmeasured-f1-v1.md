# Saved final QA scoring with explicitly unmeasured extraction F1

This extends the original four-component saved-output scorer. The original full
extraction profile remains supported. It does not execute models, add calls, lower
thresholds, supply missing human annotations or approve an unfinished freeze.

## Approved missing measurements

The approved D-009 scope leaves final extraction F1 unmeasured because no separate
final entity annotation set was supplied. Independent semantic answer risk also
remains missing unless eligible correctness reviews are actually received.
Do not manufacture empty entity labels, label proxy scores as independent risk,
or substitute D-013 development annotations.

In the exact approved freeze, the `extraction` and/or `answer-risk` declarations
may use this explicit form instead of reference/prediction artifacts:

```json
{
  "status": "unmeasured",
  "reason": "Separate final extraction reference annotations were not supplied.",
  "approved_by": "Milica Mileusnic",
  "decision_record": "d009-coordinator-bounded-scope-approval-v1"
}
```

The declaration cannot contain dummy `references` or `predictions`. A reason,
named approver and decision record are mandatory. Retrieval and classification
remain required; this extension does not waive their data requirements.

## Separate QA component

When extraction is unmeasured, include a `qa` component with checksum-pinned
`references` and `predictions`, using the same path/hash envelope as the other
components. All paths stay in the approved private bundle. The final bundle must
not be constructed by editing golds to match observed results.

QA references are a JSON object containing `version`, `kind: permitted_benchmark`,
`partition: final`, `human_reviewed: true`, and nonempty `cases`. The review flag
describes the actual reviewed QA references, not human rating of model answers.
Each case contains:

- `id`, nonempty `case_version`, and its non-development `group`;
- `document`, a canonical frozen PreparedDocument for document/mixed questions;
- `passages`, optional canonical literature contexts as objects containing
  `passage_id`, `text`, `text_sha256`;
- optional `expected_evidence_state` and `expected_answer_route` for diagnostic
  state/route agreement. These are reference values, not model inputs.

QA predictions contain `version`, `partition: final`, the exact frozen
`system_versions`, and one record per case: `id`, `case_version`, and `result`
holding the full frozen AnswerResult. On a technical failure use `result: null`
and preserve the original error/receipt separately. Do not turn failure into
abstention. Missing/duplicate/unexpected IDs or different versions are rejected.
Mock-mode records are rejected as final live provider evidence.

The scorer checks schema, canonical identity and exact document code-point
evidence. Literature sources are checked for literal excerpt membership in the
separately pinned canonical passage. AnswerResult does not carry literature
offsets, so that check is not claimed as literature offset validation. Missing
canonical context leaves the aggregate span-validity measurement unavailable;
it is never a vacuous pass. Semantic support/completeness remain unmeasured.

The metric scope is explicitly the saved QA AnswerResults. Extraction-output
structural validity is not covered by those rates. The QA-only profile is allowed
only when extraction is explicitly unmeasured, so QA success cannot hide failures
in a measured extraction component. Empty QA inventories are rejected.

## Exact scoring command

After actual approved generation has finished and the operator has delivered
the saved results separately from scoring references, use the pinned private
freeze and a new output run identifier:

```powershell
$freeze = 'C:\approved-final-bundle\freeze.json'
$freezeHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $freeze).Hash.ToLowerInvariant()
./eval/.venv/Scripts/python.exe -B -m notelens_eval.run --profile final --require-freeze --freeze $freeze --freeze-sha256 $freezeHash --output C:\private-final-results
```

The hash must be the coordinator-approved exact hash, not a fresh replacement
for a different approval. The command above computes it for comparison; record
and compare it with the immutable approval before invocation. Final references
and predictions must already have their exact hashes inside the freeze.

A run claims a single-use receipt before accessing its scoring components. Keep
that receipt even after a failure; do not retry under the same identity. The
command publishes only source-free aggregate reports atomically. It makes zero
provider calls. A return code of 1 can mean that scoring completed with pending
or failed acceptance; inspect `results.json` before treating it as a command
failure and never rerun merely to change the status.

Missing exact F1 or independent semantic risk remains null with
`measurement_missing`. Consequently the numerical quality decision cannot become
`passed` merely because delivery limitations were accepted administratively.
Task/delivery acceptance and the measured quality decision are distinct.

The C-owned aggregate classifier report continues to bind its published model
manifest. A different runtime startup-policy manifest must be recorded separately
with evidence that model version/artifact match; do not rewrite the owner report.
