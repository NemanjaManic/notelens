# Development evaluation with D's relayed ratings

**Current status, 2026-11-23**: This nine-case report remains a historical checkpoint.
The wider frozen development measurement covers 27 literature/mixed queries and
81 case/method results. B and D accepted **v2** for [A-008 closure](../a008-closure.md);
the [public summary](frozen-development-summary.json) preserves the accepted
aggregate results and limits. The [A-011 configuration handoff](../a011-freeze.md)
is complete, with unseen final measurement explicitly unexecuted. Earlier pending
statements below retain their original meaning and date.

Owner: Nemanja (A). Prepared: 2026-11-21. Scope: nine public development cases.

## Received D source record, 2026-11-22

Nemanja supplied D's private development-review package. Its candidate manifest
`d-cross-module-development-v2` matches SHA-256
`f01dd8c4c4aa3deb7b7d6842643fec17f8680b0991e875e38905499019203896`.
All nine package checksum entries passed. D's source-review record
`d007-public-qa-pinned-source-review-v1` has SHA-256
`e129e7e8cb8b2f8af269ca2a690e35b99444b7aa9970ed080e0b145fe07f40dd`.
It explicitly describes a non-blinded agent source review over the pinned
snapshot. Its original 12 citations and four additional observations reverified
locally and exactly match A's effective reference choices and new ranges.

The [v2 provenance record](reviewed-development-references-v2.json) now binds
that received D source, and the [v2 result](reviewed-development-evaluation-v2.json)
reproduces the earlier results for all three retrieval methods. The default v1
record and report remain unchanged and also reproduce. No case label, evidence
bundle, model, prompt, index, threshold or ranking was changed by this update.
The private D source package and cross-module document fixtures are not copied
into A's versioned records.

```powershell
uv run --locked --offline --directory services/rag python -B ../../docs/rag/evaluation/measure_reviewed.py --references docs/rag/evaluation/reviewed-development-references-v2.json
```

D's broader manifest is still a candidate. A found an inventory reconciliation
item for D to resolve before freeze; the selected 54-case route/state totals are
consistent. The proposed 54/26 and 66/14 splits, unseen final source/reviewer
assignments, out-of-scope coverage and private upload location still require the
responsible team confirmations. The exact inventory finding is retained in the
private handoff review. A-008 and A-011 remain open.

The initial 2026-11-21 checkpoint below preserves the earlier evidence state.

The [reference record](reviewed-development-references.json) incorporates the
nine-row coverage table relayed from Milica (D): seven full cases, one partial
case and one case without support. D also confirmed all 12 original citations.
The two scoped alternatives are topic `6450` for A-QA-01 and topic `363` for
the cause part of A-QA-02. Additional A-QA-07 context stays under topic `179`.
A-QA-09 retains `4643` and `4452`, with the narrower bilirubin citation.

At that initial checkpoint, the exact new ranges were A's locally verified proposals: the separately
mentioned attachment was not received. A reply was prepared for Nemanja, but
its delivery and D's canonical joint-review record are unconfirmed. This is
an owner-local evaluation candidate, not the shared benchmark freeze.

## Results

The [result record](reviewed-development-evaluation.json) re-scores the same
saved vector, hybrid and BM25 rankings. Eight cases have topic references;
the no-support case has no topic-recall denominator. There are 11 supported
requested parts and two missing parts. The partial case remains partial.

| Group | Method | Unique-topic Recall@5 | Topic MRR@5 | All required topics | Supported parts with evidence |
| --- | --- | ---: | ---: | ---: | ---: |
| Single-topic, 5 cases | Vector | 1.000 | 1.000 | 5/5 | 5/5 |
| Single-topic, 5 cases | Hybrid | 1.000 | 1.000 | 5/5 | 5/5 |
| Single-topic, 5 cases | BM25 | 1.000 | 0.867 | 5/5 | 5/5 |
| Multi-topic, 3 cases | Vector | 1.000 | 1.000 | 3/3 | 6/6 |
| Multi-topic, 3 cases | Hybrid | 0.833 | 1.000 | 2/3 | 5/6 |
| Multi-topic, 3 cases | BM25 | 1.000 | 0.778 | 3/3 | 6/6 |

Across the eight cases with topic references, vector and BM25 retain every
reviewed required topic and all 11 supported parts. Hybrid retains all
required topics for seven of eight cases and 10 of 11 supported parts. Its
overall macro Recall@5 is 0.9375. The scoped alternatives do not change the
earlier aggregate results on these fixed rankings.

Hybrid still lacks the original topic `4643` in A-QA-09's first five results.
The earlier candidates `5905`, `4645` and `259` are not credited here because
D's latest proposed decision retains `4643` and `4452`. Their presence alone
does not authorize silently changing the references or the metric.

Retain the question-only vector baseline for development. This is the
existing choice, not a new model, threshold or retrieval configuration.

## Measurement rules and provenance

- Apply the five-passage budget before deduplicating topics.
- Score Recall@5 against one complete alternative reference set; never
  combine incomplete pieces of different sets into a false full match.
- Preserve the earlier MRR convention: the first relevant topic's position
  in the unique-topic sequence within the first five passages.
- An alternative is a substitute for the relevant part, not another
  mandatory topic. Missing requested parts receive no supporting evidence.
- Evidence credit requires an entire reviewed passage bundle, including
  required context. Another passage with the same topic is insufficient.
- Validate every quote digest and passage/topic code-point range against
  the exact pinned corpus. Fourteen unique reference spans were verified.
- Bind the original proposals, ranking records and query scope by SHA-256.
  The report records corpus, index and all three retriever versions.

The evaluator made zero provider calls and zero new rankings. It reads only
public development records and the pinned corpus. No private annotation,
final test case, API credential or index/cache write is involved. These
ranking results do not measure generated-answer correctness or general
semantic rejection quality. The earlier support and HTTP checks remain
separate evidence with their recorded sample limits.

## Reproduce

From a checkout holding the verified passage artifact:

```powershell
uv run --locked --offline --directory services/rag python -B ../../docs/rag/evaluation/measure_reviewed.py
uv run --locked --offline --directory services/rag python -B -m pytest tests/test_reference_metrics.py tests/test_hybrid.py tests/test_failures.py tests/test_answers.py tests/test_contract.py
```

The targeted suite passed 105 tests. It includes alias credit, incompatible
alternative sets, repeated chunks, the five-passage limit, no-support
denominators, wrong-passage evidence, non-BMP and repeated-quote offsets,
plus the existing contract/answer/failure checks. The runner refuses changed
bound inputs, invalid canonical slices and foreign input paths. Its output
writer preserves existing files rather than replacing historical reports.

A-008 remains open for D's shared QA/reference record, the agreed wider
development benchmark, independent output evaluation and B's application
routing verification. A-011's final freeze and measurement remain pending.

## Workflow record

Used the installed `speckit-implement` agent workflow, with explicit
`SPECIFY_FEATURE_DIRECTORY=specs/001-rag` and `SPECIFY_FEATURE_NO_PERSIST=1`.
The official PowerShell `check-prerequisites.ps1 -Json -RequireTasks
-IncludeTasks` resolver selected the existing feature. Its requirements
checklist had 16 checked and zero unchecked items. Existing root ignore
rules cover secrets, environments, public-corpus artifacts and caches;
shared configuration was not edited. No `.specify/extensions.yml` hooks
were registered. This owner-local increment does not complete A-008 or
claim implementation of the remaining team tasks.
