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
and ask an English question or choose a preset. Use the document citations to
highlight canonical passages. Press Ctrl+C in the launcher terminal to stop the stack.
Each invocation reserves independent loopback ports and owns its process trees.
The launcher provides ephemeral service authentication and starts only mock services.

Run the finite smoke check against the built workspace.

```powershell
uv run --locked --offline --directory scripts/project python -B smoke_mock.py
```

The smoke check submits the built-in example and verifies owner-only access. It
exercises the report, posts free-text and preset questions, and follows saved
answer and citation links. It checks document and literature citations, partial
answers when literature is insufficient or unavailable, and an explicit document
gap. It also checks English guidance, request limits, history eviction and clearing,
a question on pasted synthetic text, and shutdown of all three stacks.
The check needs no API keys, model downloads, or corpus.

## Question limits and history

Choose **Document**, **Literature**, or **Both**. Both uses separate fields.
The mock demo accepts up to 1,000 Unicode code points across the fields and
up to 16 KiB per request. It rejects excess input and asks for a longer
English question if language detection is inconclusive. The services have
a limited set of supported mock questions.

Each session admits 10 submissions per rolling minute and runs one question at
a time. Each mock branch has a five-second timeout and zero automatic retries.
The document branch receives the prepared document and document question.
The literature branch receives the literature question. Each question is
self-contained. Prior turns are available for display only.

Each document retains the latest five completed turns within 32 KiB of
serialized UTF-8, including sources and warnings. The oldest whole turns are
evicted first. A single oversized answer is shown on the current page only.
Saved answers and citations use opaque IDs and require the owning session.
**Clear conversation history** removes those turns. Document removal, expiry,
session closure, and server restart also clear them. Questions and answers
stay out of URLs, logs, and persistent storage.

## Local verification

On Member B's branch based on PR #6 merge `1ac8bfe`, the locked smoke command
passed against the production build. Both stacks shut down and closed all eight
loopback ports. The existing 37 fixture report checks, 54 cross-runtime Unicode
cases and 15 scaffold checks passed. The smoke uses rendered HTML over HTTP.
An injected interruption stopped all four owned processes while an independent
loopback listener remained reachable.

On the B-003 branch, 17 routing, input, and history tests and all three key-free
HTTP smoke scenarios passed against the production build. Chrome verified the
free-text form, English validation, mixed inputs, evidence highlighting, saved
turn navigation, session isolation, and history clearing.
