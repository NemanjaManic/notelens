# Development evaluation with D's relayed ratings

Owner: Nemanja (A). Prepared: 2026-11-21. Scope: nine public development cases.

The [reference record](reviewed-development-references.json) incorporates the
nine-row coverage table relayed from Milica (D): seven full cases, one partial
case and one case without support. D also confirmed all 12 original citations.
The two scoped alternatives are topic `6450` for A-QA-01 and topic `363` for
the cause part of A-QA-02. Additional A-QA-07 context stays under topic `179`.
A-QA-09 retains `4643` and `4452`, with the narrower bilirubin citation.

The exact new ranges are A's locally verified proposals: the separately
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
