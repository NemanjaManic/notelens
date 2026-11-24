# NoteLens

NoteLens is a web workspace for reading English medical reports and checking the evidence behind findings, summaries, and answers. It was built as a SITA AI Bootcamp capstone.

[Open the hosted demo](https://notelens-live-production.up.railway.app/) · [Read the user manual](docs/platform/NoteLens-User-Manual.md) · [Download the PDF](docs/platform/NoteLens-User-Manual.pdf)

> NoteLens is an educational demonstration and does not replace a doctor. Use only public or synthetic documents written in English. Do not upload real personal medical reports.

## Try a report

Select **Chest pain report** under **Choose an example**. The workspace displays the report text, a suggested specialty, extracted findings, and a summary. Select **View passage** to highlight the evidence for a finding or summary statement.

In **Questions and literature**, choose **Document** to ask about the open report, **Literature** to ask a general question using MedlinePlus sources, or **Both** to ask one question of each. Document citations highlight the quoted text. Literature citations link to the original source. The workspace flags partial or insufficient evidence.

You can also paste English text or upload a PDF with selectable text. PDFs are limited to 2 MiB, and prepared documents are limited to 100,000 Unicode code points. Submitted documents stay in server memory for up to 60 minutes and are cleared on expiry or restart.

## Architecture

A Next.js and TypeScript web app prepares documents, manages browser sessions, and calls three Python services over HTTP. The services expose FastAPI endpoints and exchange payloads defined by the [JSON Schema and OpenAPI contracts](contracts/v1/README.md).

| Component | Implementation |
| --- | --- |
| [Web app](apps/web) | Prepares one canonical text per report, assigns a document ID and SHA-256 digest, routes questions, and renders cited passages. |
| [Specialty classifier](services/classifier) | A scikit-learn logistic regression model trained on MTSamples with word- and character-level TF-IDF features. It can return one of five specialties or abstain when the text gives too little or conflicting evidence. See the [model card](docs/ml/model-card.md). |
| [Document analysis](services/extraction) | Extracts findings, generates summaries, and answers questions about the report. The service resolves model-supplied quotes against the canonical text and validates the resulting spans before returning them. |
| [Literature retrieval](services/rag) | Searches 617 passages across 401 MedlinePlus topics. The frozen configuration uses `text-embedding-3-small` and retrieves the five nearest passages from a Chroma cosine index. The answer pipeline checks support for each part of the question and reports gaps. See the [retrieval configuration](docs/rag/a011-freeze.md). |

Document evidence uses half-open Unicode code-point ranges, `[start, end)`. The browser converts those ranges to UTF-16 indices for highlighting. When a user asks both question types, the web app keeps document and literature citations attached to their respective claims.

The [Railway deployment](infra/railway/Dockerfile.live) packages the web app and services in one container. Only the web app is exposed publicly. The Python services listen on loopback and use per-start bearer tokens.

## Run locally

The Windows quickstart runs the web app and all three services with mocks and synthetic fixtures. It requires PowerShell, Node.js 24, npm 11, Python 3.13, and uv. No provider API keys or model downloads are required.

From the repository root:

```powershell
foreach ($project in @('scripts/project', 'services/rag', 'services/classifier', 'services/extraction')) {
    uv sync --locked --directory $project --python 3.13 --no-dev
    if ($LASTEXITCODE -ne 0) { throw "Dependency setup failed for $project." }
}
npm.cmd ci
if ($LASTEXITCODE -ne 0) { throw 'Web dependency setup failed.' }
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Web build failed.' }

uv run --locked --offline --directory scripts/project python -B start_mock.py
```

Open the URL printed by the launcher. Press **Ctrl+C** to stop the stack. The [demo runbook](docs/platform/demo.md) covers the automated smoke test and browser checks.

## Evaluation

| Measure | Result |
| --- | --- |
| Specialty classification on 183 held-out MTSamples reports | **96.2% accuracy** and **0.958 macro-F1** when forced to assign a label. With abstention enabled, the model labeled 174 reports and assigned 169 correctly. |
| Final question-answering run | **26 of 26 cases completed**, with zero technical errors. |
| Structural and citation checks | **28 of 28 accepted answer branches** passed schema and exact-quotation checks. |
| End-to-end literature retrieval | **73.3% topic Recall@5** across 15 cases with reference topics, below the recorded **90%** criterion. |

Final extraction F1 and independent semantic answer risk were unmeasured. The citation checks verify that quoted text matches its source. Semantic correctness requires separate review. See the [classifier model card](docs/ml/model-card.md) and [final evaluation report](docs/extraction-eval/final-report.md).

For contributor setup, see the [working-copy guide](docs/team/working-copies.md) and [repository ownership](docs/team/allowed-paths.md).
