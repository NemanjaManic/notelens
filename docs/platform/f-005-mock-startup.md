# Run the local NoteLens mock demo

Use Windows, Python 3.13, Node 24, npm 11, and uv. From the repository root,
install the existing locked environments and build the web workspace.

```powershell
uv sync --locked --directory scripts/project
uv sync --locked --directory services/rag
uv sync --locked --directory services/classifier
uv sync --locked --directory services/extraction
npm.cmd ci
npm.cmd run build
```

Start the stack from the repository root.

```powershell
uv run --locked --offline --directory scripts/project python -B start_mock.py
```

Open the printed `http://localhost:<port>/demo` URL, select **Chest pain report**,
and choose one of the preset questions. Use the document links to highlight
canonical passages. Press Ctrl+C in the launcher terminal to stop the stack.
Each invocation reserves independent loopback ports and owns its process trees.
The launcher provides ephemeral service authentication and starts only mock services.

Run the finite smoke check against the built workspace.

```powershell
uv run --locked --offline --directory scripts/project python -B smoke_mock.py
```

The smoke check submits the built-in example form and verifies that the prepared
report opens only with the owning session cookie. It follows rendered HTML links
through classification, extraction, summary, and document, literature, mixed, and
insufficient-evidence answers. It follows document citations, checks the
literature attribution, exercises a partial mixed answer with insufficient
literature, and verifies that all child jobs exit and their listening ports close.
The smoke uses one versioned synthetic document and preset questions. This
foundation check does not require API keys, model downloads, or a corpus.

## Local verification

On Member B's branch based on PR #6 merge `1ac8bfe`, the locked smoke command
passed against the production build. Both stacks shut down and closed all eight
loopback ports. The existing 37 fixture report checks, 54 cross-runtime Unicode
cases and 15 scaffold checks passed. The smoke uses rendered HTML over HTTP.
An injected interruption stopped all four owned processes while an independent
loopback listener remained reachable.
Browser automation, live service checks and foundation publication remain separate.
