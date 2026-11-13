# D local frozen-contract verification

Date: 2026-11-13. Branch: `member-d/extraction-evaluation`.
Agent implementation/testing, not human owner approval. Existing local changes
were preserved. No commit, push, collaborator message or live provider call.

Used `speckit-implement` for `specs/004-extraction-evaluation`, with the explicit
user-authorized local slices. The official prerequisite resolver succeeded with
`SPECIFY_FEATURE_DIRECTORY` and `SPECIFY_FEATURE_NO_PERSIST=1`; requirements
checklist: 16 checked, zero unchecked. Frozen F-003/F-009 handoff is the baseline;
shared contract/generated files and A/B/C-owned paths were not edited.

## Completed local scope

- D-001: synthetic practice assertion/status values aligned to frozen v1, including
  unknown assertion, independent planned/cancelled/performed procedure status and
  exact mention/evidence spans. Annotation tooling accepts unknown.
- D-004/D-005: frozen binding runtime validation, independent extraction/summary
  failures, partial and insufficient document answers, exact source/mention checks,
  source-only ICD, bounded safe failure handling and strict UUID HTTP admission.
- D-006: installed local contracts dependency and matching locks; accepted synthetic
  language-validation fixtures; UUID HTTP adapters; correct semantic-evidence error
  categorization; live/ready health checks and repeated fresh health-401 diagnostics.
- D-008 preparation: blank form, read-only validator/aggregate, integrity tests and
  review/calibration procedure. No human records were produced. The blank form yields
  one blank record, zero completed reviews and null numeric means.

## Executed verification

Commands run from repository root (Windows Python 3.11 environments):

| Command | Result |
| --- | --- |
| `./services/extraction/.venv/Scripts/python.exe -m pytest services/extraction/tests -q --tb=short` | 53 passed; one upstream Starlette/httpx deprecation warning |
| `./eval/.venv/Scripts/python.exe -m pytest eval/tests -q --tb=short` | 36 passed |
| `./eval/.venv/Scripts/python.exe -B docs/extraction-eval/check_training_examples.py` | 16 documents, 18 mentions, 37 spans pass |
| `./eval/.venv/Scripts/python.exe -m notelens_eval.annotations lint eval/fixtures/annotation-lint-synthetic-v1.json --output eval/reports/local/annotation-lint-demo.json` | zero structural issues/questions; ready for independent review, not reviewed |
| `./eval/.venv/Scripts/python.exe -m notelens_eval.readiness` | contract and local HTTP pass; cross-service not run |
| `./eval/.venv/Scripts/python.exe -m notelens_eval.http_suite` | 24 documents, 48 questions, 72 HTTP 200, zero transport errors |
| `./eval/.venv/Scripts/python.exe -m notelens_eval.answer_review eval/fixtures/answer-review-template-v1.json` | blank=1, completed=0, invalid=0 |
| `./services/extraction/.bootstrap/Scripts/uv.exe lock --directory eval --check --offline` | pass, 44 packages |
| `./services/extraction/.bootstrap/Scripts/uv.exe lock --directory services/extraction --check --offline` | pass, 43 packages |
| `git diff --check` | pass; Windows line-ending normalization warnings only |

The eval environment was synchronized with `uv sync --directory eval --locked
--offline`; its installed package now includes `notelens-contracts==1.0.0`.
Use a workspace `UV_CACHE_DIR` if the user cache is inaccessible.

HTTP success is not semantic completeness. The synthetic literal completeness
check passed all fact/gap/no-extra requirements on 10 of 48 questions; required
facts were complete on 35, and 1 of 26 expected gap mentions was disclosed.
These are narrow catalog-mock measurements, not real model or clinical results.
Local detailed reports are ignored under `eval/reports/local/`.

## Remaining ownership and independently available work

| Item | Owner | Dependency / next action |
| --- | --- | --- |
| Practice a manual review on synthetic development examples | D | Available now; D must personally inspect and record her own review, never agent-generated human approval |
| Expand adversarial synthetic fixtures and analyze mock misses | D | Available now; keep references separate and do not claim model quality |
| D annotation guideline adoption and review calibration | D/team | Actual reviewer discussion and independent records |
| F-004 shared scaffold integration, F-014 published base | B coordinates; A/C/D provide owned contributions | D local contribution checked; shared acceptance/publication remains open |
| Actual annotation sample selection and assignments | C then D | C-002 canonical document/group/split manifests and permitted source access |
| Real primary annotations, secondary reviews, adjudication | A/B/C/D then D | Frozen assignments and actual independent human submissions |
| Retrieval/classification adapters and source-reviewed QA | A/C/D | Actual A/C interfaces/results and A corpus inputs |
| Live extraction/answer validation | D/team | Approved provider/model/budget and live language/ambiguity policy; no silent activation |
| Final evaluation and substantive thresholds | Team then D | Development measurements, agreed thresholds, frozen versions and all final gates |

Parent D tasks remain unchecked where these dependencies apply. Mock tests do not
complete F-004/F-014, human calibration, real-data annotations or live-model work.

## Working-tree status at verification

All listed changes are uncommitted D-owned work, including prior local changes.

```text
 M docs/extraction-eval/annotation-guide.md
 M docs/extraction-eval/annotation-training-examples.json
 M docs/extraction-eval/answer-review-rubric.md
 M docs/extraction-eval/check_training_examples.py
 M docs/extraction-eval/integration.md
 M eval/fixtures/answer-review-template-v1.json
 M eval/fixtures/extraction-qa-synthetic-v1.json
 M eval/fixtures/smoke-references.json
 M eval/providers/document_api.py
 M eval/pyproject.toml
 M eval/src/notelens_eval/annotations.py
 M eval/src/notelens_eval/http_suite.py
 M eval/src/notelens_eval/metrics.py
 M eval/src/notelens_eval/readiness.py
 M eval/src/notelens_eval/run.py
 M eval/src/notelens_eval/suite.py
 M eval/tests/test_readiness.py
 M eval/uv.lock
 M services/extraction/README.md
 M services/extraction/fixtures/demo-question.json
 M services/extraction/fixtures/demo-request.json
 M services/extraction/pyproject.toml
 M services/extraction/src/notelens_extraction/__init__.py
 M services/extraction/src/notelens_extraction/cli.py
 M services/extraction/src/notelens_extraction/contracts.py
 M services/extraction/src/notelens_extraction/demo.py
 M services/extraction/src/notelens_extraction/main.py
 M services/extraction/src/notelens_extraction/prompts/answer-v1.txt
 M services/extraction/src/notelens_extraction/prompts/extract-v1.txt
 M services/extraction/src/notelens_extraction/providers.py
 M services/extraction/src/notelens_extraction/service.py
 M services/extraction/tests/test_http_smoke.py
 M services/extraction/tests/test_service.py
 M services/extraction/uv.lock
 M specs/004-extraction-evaluation/tasks.md
?? docs/extraction-eval/d-local-completion-2026-11-13.md
?? docs/extraction-eval/judge-calibration.md
?? eval/src/notelens_eval/answer_review.py
?? eval/tests/test_review_integrity.py
?? services/extraction/tests/test_frozen_mock.py
```
