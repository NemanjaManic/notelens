# Development acceptance decisions

## Adopted v2 decision and measured outcome (2026-11-23; current)

Milica explicitly delegated the numerical choice after allowing stricter targets.
`eval/config/acceptance.json` now records schema/spans 1.00, entity exact F1 0.90,
topic Recall@5 0.95 and semantic answer risk at most 0.05, with a named decision
record. These project gates are not prescribed clinical thresholds. The decision
and acceptance hashes were fixed before the twelve-operation development pilot.

The [measured pilot](d011-development-measurement-v1.md) returned valid results
for 1/6 extraction requests and 5/6 QA requests; acceptance is **failed**.
Official complete-case F1 is unavailable with failed extractions; independent
semantic answer-risk labels are also missing. The separately labelled literal
QA proxy has zero errors in five emitted answers, and a conservative end-to-end
entity lower bound is 0.0000. Neither replaces a missing acceptance metric.
The matched mock and prior retrieval baselines are retained with their own scope.

The regression decision rejects full release acceptance of the measured service.
D-011 measurement/decision artifacts are prepared; remediation, remeasurement
and justified semantic risk evidence remain open. D-009 retains its original
scope and cannot execute a final run while these gates fail. The older unset
threshold discussion below is historical, not the current configuration.

The D-011 proposal in `eval/config/acceptance.json` preserves the required
complete schema/span validity rates. Quality thresholds remain unset pending
development measurements and named team decisions. The initial quality entries
cover entity F1, topic recall and answer risk and can be extended by agreement.

Run `python -m notelens_eval.acceptance --config CONFIG --measurement MEASUREMENT`.
A measurement supplies `version`, matching `acceptance_version`, positive integer
`sample_count`, and a `metrics` object using the criterion names. Rates must be
between zero and one. A quality threshold requires `decision_by` and
`decision_record` fields on its criterion.

Missing measurements or decisions yield pending status. A measured threshold
violation yields failed status. Only complete passing criteria yield passed
status and exit code zero. The evaluator reads inputs without updating them.
The configuration is a proposal awaiting quality decisions and measured evidence.

## Development measurements recorded on 2026-11-21

The [measurement record](../../eval/reports/development/development-measurements-v1.json)
pins the saved outputs, datasets and configuration by SHA-256. Denominators and
versions are recorded for each measurement. The consolidation made zero provider calls.
Repository JSON digests use LF line endings. The ignored HTTP report digest uses
the exact bytes produced by the Windows run.

| Evidence | Scope | Observed result |
| --- | --- | --- |
| C-003 classification | 185 C-002 validation documents, forced choice | 174 correct, 94.05% accuracy, macro-F1 0.9285. The descriptive validation-majority comparator scored 55 correct and macro-F1 0.0917. |
| Vector retrieval | Eight development cases with proposed topics, five single-topic and three multi-topic | Topic Recall@5 and MRR@5 of 1.000. All required topics and evidence in 8/8 cases. |
| Hybrid retrieval | Same eight cases | Topic Recall@5 and passage evidence coverage@5 of 0.938. MRR@5 of 1.000. A-QA-09 missed one proposed topic and its required passage. |
| BM25 retrieval | Same eight cases | Topic Recall@5 and passage evidence coverage@5 of 1.000. MRR@5 of 0.833. |
| A answer-risk pilot | Two saved answers with scoped agent review | Two answered, zero incorrect in scope. The rejection rate and confidence curve are unavailable. |
| D synthetic loopback | 24 extraction results and 48 answers | 72/72 schema-valid records, zero evidence or relationship violations, exact and relaxed entity F1 of 0.6512, and 34/48 answers met the literal facts, gaps and extra-quote checks. |

The retrieval replay excludes A-QA-03 from topic and passage scoring because it
has no proposed required topic. Each distinct cited passage is one provisional
required evidence group. The saved rankings measure coverage against that
proposal. D's [excerpt review](qa-development-inventory.md) records the portion
checked against available text.

The classification result covers validation only. The answer pilot used
non-blinded agent judgments. The loopback result measures a deterministic mock
and the cited fixture rules. Acceptance remains pending. The structural targets
remain 1.0 and substantive quality thresholds remain unset.

## Frozen A-008 development retrieval baseline

D replayed all 81 saved case/method rows from the v2 A-008 package against the
pinned corpus and frozen references. This covers 9 literature-only and 18 mixed
queries. Five queries without reference support are outside the topic-recall
denominator. Each method has 22 supported cases and 27 supported evidence parts.

| Baseline | Topic Recall@5 | Topic MRR@5 | All required topics | Reference evidence parts |
| --- | ---: | ---: | ---: | ---: |
| Vector, selected | 1.000000 | 0.909091 | 22/22 | 27/27 |
| Hybrid | 0.977273 | 0.931818 | 21/22 | 26/27 |
| BM25 | 1.000000 | 0.852273 | 22/22 | 27/27 |

The replay recomputes metrics from recorded rankings. Risk and coverage still
have only three historical support assessments. This baseline records retrieval
evidence for D-011. Quality thresholds still require named decisions and
provider-backed extraction and answer measurements. See the [version pins and intake evidence](../../eval/reports/development/member-d-handoff-intake-2026-11-22.json).
