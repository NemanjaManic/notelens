# Extraction improvement: strict quote selection and trusted assembly

Date: 2026-11-23. Candidate service SHA:
`8ef63edd4ab1cb39de73b0f31b97bb12359f7731`.

## Measured improvement

The provider now selects medical mentions, context labels and exact source quotes
through a small strict private JSON schema. Trusted Python code resolves source
positions and constructs the unchanged frozen public API records, IDs, hashes,
component versions, citation links and displayed summary/answer text. This
removes format bookkeeping from the language model without replacing its
clinical labels with reference answers. An extractive summary is assembled from
the selected literal source passages, rather than asking the model to duplicate
claims in a separate text field.

| Scope | Valid results | Exact entity F1 | Relaxed F1 |
| --- | --- | ---: | ---: |
| Earlier contract protocol, same six documents, saved-output replay | 2/6 | 0.0851 end-to-end lower bound | See original failure report |
| Quote protocol, same six observed documents | 6/6, including one explicit partial | 0.6500 | See machine-readable report |
| Three additional development documents, before final grounding fixes | 3/3 after separately labelled replay | 0.5556 | See machine-readable report |
| Two further development documents, generated after final grounding code was fixed | 2/2, including one explicit partial | 0.6789 | 0.8440 |

The end-to-end comparator retains every reference document: failed results
contribute no predictions instead of disappearing from the F1 denominator.
All 11 document outputs validate under the final builder; nine extraction
outcomes are complete and two are explicitly partial. All eleven quoted summaries
complete. Three sufficient/insufficient/partial QA regressions validate and pass
their literal facts/state/gap proxy checks. The same provider model, gpt-6-luna,
was used throughout. Two fresh saved-live-response HTTP replays also passed with
zero extra model calls.

All **130 service tests** pass, covering the private schema, canonical/Unicode
positions, repeated occurrences, partial results, summary independence, API
routes and explicit operator-policy selection. The latest evaluation suite has
141 passing tests. The [measurement report](../../eval/reports/development/d011-extraction-improvement-v2.json)
contains raw-response pins, per-case counts, labels/status accuracy, sample
partitioning and the fixed acceptance evaluation.

## Safety and traceability properties

- References/annotations/gold answers are not included in provider inputs.
- The model cannot set the selected document identity, source hash or public IDs.
- Unique literal quotes are resolved directly. Repeated quotes retain explicit
  occurrence selection; no arbitrary first match is substituted.
- A mention is resolved inside its selected supporting context. No synonym,
  altered wording or invented span is accepted as an exact source quote.
- Non-procedure status is null; an unspecified procedure status stays unknown,
  never inferred performed. Other model-selected labels are preserved.
- Unresolvable items remain missing in F1 and trigger a visible partial/failed
  extraction status, error and warning. They are not silently counted as correct.
- Summary failures do not erase independently supported extraction items.
- Incomplete/refused Responses, duplicate keys and nonfinite JSON still fail
  closed. There are no automatic network retries.

The private schema uses strict structured outputs supported by the
[official API guide](https://developers.openai.com/api/docs/guides/structured-outputs).
The shared API schema and B-owned contracts were not changed. No dependency or
lockfile update was required.

## Interpretation and remaining quality work

This is a real improvement in returned-result reliability and mention matching,
not a passing clinical-quality result. Exact F1 remains below the adopted 0.90
target. Missing concepts, extra concepts and annotation-boundary differences
remain; the higher relaxed score must not replace exact F1 in acceptance.
Independent semantic answer-risk evidence remains absent. D-011/D-009 stay open.

The first six documents were already observed when the quote prompt was chosen.
The next three were generated with the initial private builder and replayed after
general occurrence/status fixes. They are not an independent validation of the
final pipeline. The last two documents were selected and generated only after
the final grounding revision was pinned, with no prompt changes during that run.
These small length-selected development samples are not the D-007 final set or
representative clinical validation. All earlier failures and stricter thresholds
are retained.

Known cumulative worst-case reservations are **USD 0.0965479**, below USD 0.10;
this is not confirmed billed spending. This improvement used 14 new provider
calls, all bounded and individually reserved, with zero automatic retries.
No further call or final execution was performed after this validation.

## Explicit service configuration for a reviewed app check

The new protocol is opt-in. A reviewed server-side provider policy must include:

```json
{
  "model": "gpt-6-luna",
  "input_format": "messages",
  "output_format": "quote_hints"
}
```

These are only the selection fields, not an active execution policy. The policy
must also contain the separately approved operator/scope, call/token/budget
limits, rates, authentication and exclusive receipt. The old contract format
remains available for historical comparisons and is still the default when the
new output_format field is omitted. No app-call allowance or deployment approval
is granted here. Goran must test the exact selected service/configuration before
integration freeze. See the private candidate package receipt for artifact pins.
