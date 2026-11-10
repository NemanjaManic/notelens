# Technical Feasibility and Decision Proposals

**Checked**: 2026-11-10. **Owner**: B, with A/C/D review.
**Status**: Documentation review and design proposal; no app build, paid call or deployment.
This is not a claim of account access, measured throughput, model quality or hosting capacity.

## Feasibility result

The confirmed architecture is feasible for a small local foundation: Next.js/TypeScript
orchestration and three independent Python/FastAPI services, each with its own lockfile.
Use existing Node 24 and uv; propose Python 3.13 for service environments because it is
already installed. Verify actual dependency resolution/builds in foundation task F-004
before locking them. Keep toolkit integration at the verified Spec Kit 1.3.3.

No subagents were used: the source prompt forbids delegation without an explicit request.
Research was performed directly against the primary sources below.

## Source register

### next-install

[Next.js installation](https://nextjs.org/docs/app/getting-started/installation). Node.js minimum is 20.9; the inspected local Node 24 meets that documented requirement. This is documentation compatibility, not an executed app build.

### next-host

[Next.js self-hosting](https://nextjs.org/docs/app/guides/self-hosting). Node-server self-hosting and server-only environment variables are documented. Dynamic document routes must avoid filesystem/static caches.

### fastapi

[FastAPI manual server](https://fastapi.tiangolo.com/deployment/manually/). Small independent ASGI processes are supported; runtime/process supervision still needs measured rehearsal.

### fastapi-memory

[FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/). Worker processes normally do not share memory. A single state-owning web process is the smallest proposed fit for in-memory document sessions.

### genai

[Google Gen AI Python SDK](https://googleapis.github.io/python-genai/). The SDK exposes generation, embedding and structured-schema configuration. Exact account models, prices, limits and retention remain activation checks.

### chroma

[Chroma Python client](https://docs.trychroma.com/reference/python/client). PersistentClient writes local data and targets local development/testing; server-backed clients are recommended for production. Persist only the public corpus, never submitted documents.

### vercel-python

[Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python). Python/FastAPI support exists, but does not prove all three independent services fit one web deployment or preserve local state.

### vercel-limits

[Vercel Functions limits](https://vercel.com/docs/functions/limitations). Runtime, bundle and request limits are plan-dependent; the page documents a 4.5 MB request-body limit. The approved PDF cap is below that raw limit, but encoded/multipart overhead must still be checked.

### promptfoo-python

[Promptfoo Python provider](https://www.promptfoo.dev/docs/providers/python/). A Python call_api adapter can wrap the agreed APIs; Python outputs return output or error. D can keep its adapters and scoring under eval.

### promptfoo-cli

[Promptfoo CLI](https://www.promptfoo.dev/docs/usage/command-line/). Configuration validation, eval and no-cache/no-write controls are documented. Shared benchmark data may persist with permission; user submissions must never enter runner caches.

### sklearn

[scikit-learn installation](https://scikit-learn.org/stable/install.html). Isolated environments and pre-built packages are documented; verify the selected Python/package combination and lock it before service startup.

### xgboost

[XGBoost sklearn interface](https://xgboost.readthedocs.io/en/stable/python/sklearn_estimator.html). Classifier estimators support the intended controlled baseline comparison. This does not predict a performance win.

### medline-xml

[MedlinePlus XML](https://medlineplus.gov/xml.html). Health Topic XML includes metadata, vocabulary and summaries. A must select English topics and inspect permitted content.

### medline-reuse

[MedlinePlus reuse guidance](https://medlineplus.gov/about/using/usingcontent/). The page distinguishes reusable topic material from licensed encyclopedia/drug/image material. No blanket redistribution permission is inferred.

### medquad

[MedQuAD repository](https://github.com/abachaa/MedQuAD). Use the agreed Health Topics subset as question candidates; relevance to the selected summary snapshot still requires human review.

### mtsamples

[MTSamples Kaggle release](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions). The landing page supplied no readable dataset details in this environment. C must inspect release metadata, upstream conditions and an authorized local CSV; no counts/labels/license are treated as verified.

### jsonschema

[JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12). The proposed canonical schema uses this dialect. Semantic slice/citation/hash checks remain separate.

### openapi

[OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html). The proposed service description references the single JSON Schema source rather than duplicating language models.


## Proposed local arrangement

**Decision proposal**: one Next.js process owns sessions and document preparation;
independent RAG, classifier and extraction processes listen on configurable loopback ports.
Default-port proposals are 3000/8001/8002/8003, not user-facing product limits.
Docker is not required for local startup because it is not installed here.
Services have narrow clients/adapters and do not import each other's implementation.

**Rationale**: preserves four ownership boundaries and key-free development, avoids new
infrastructure dependencies and makes process-local session behavior explicit.
**Alternatives**: a single merged application would blur ownership; three independent
cloud purchases add unnecessary initial approvals; mandatory Docker would block this machine.

## Hosting proposal requiring approval

**Smallest viable candidate**: one existing suitable host runs one Next.js process plus
the three Python processes behind a TLS reverse proxy. Only public literature/index/model
artifacts may persist; submitted documents stay in the web process's memory.
Accounts, available capacity, TLS, service authentication and any cost must be approved
and rehearsed before deployment. No host has been selected, purchased or provisioned.

**Alternative**: Vercel web plus separately hosted Python services. This needs explicit
handling of process-local document state and backend connectivity, and durable public-corpus
storage. The confirmed memory-only policy must not be silently replaced with a database.
Verify request overhead, exact runtime limits and account prices at deployment time.

This is an inference from documented runtime capabilities, not an executed deployment.
The cloud portion remains unfrozen; local foundation planning is independent of it.

## Provider and corpus decisions

Gemini is a candidate behind Python Google Gen AI adapters. Keep model IDs, dimensions,
pricing and account quotas explicit configuration, checked against the actual account
before authorization. Live execution fails closed without a reviewed budget/configuration.
Documentation fetches for some Gemini pricing/rate-limit pages were inaccessible through
the web reader; SDK capabilities were verified, but no exact prices/quotas are asserted.

Chroma is a candidate behind A's vector-store interface. Local fixture tests can use
in-memory data; real corpus indexes need versioned persistent public-data storage.
An embedding-model/dimension/preprocessing change creates a new index and reindexing.
Do not use default embedding downloads or provider calls in mock startup.

C's required comparison is TF-IDF + Logistic Regression with a majority baseline versus
XGBoost on controlled validation data. Optional embedding features and ONNX are nonblocking.
A's retrieval comparison is embedding-only versus lexical/hybrid on the same development
questions. D uses Promptfoo adapters calling the agreed APIs, deterministic scorers and
optional separately authorized judges. None of these results is known yet.

## User-resolved privacy/input decisions

On 2026-11-10 the user approved:
- Submitted documents in application server memory only, with an absolute 60-minute maximum
  from preparation, deletion on expiry/restart and earlier process-loss handled explicitly.
- At most 2 MiB (2,097,152 bytes) per PDF and 100,000 Unicode code points per document;
  reject rather than silently truncate.
- Built-in public examples may remain in the repository.

Document-bound history/results/cache entries must not outlive documents. Do not expose
submissions to static/ISR/filesystem caches or shared Promptfoo outputs.
Third-party model retention requires a separate live-activation review.

## Explicit deferred gates

Unknown budget/account/model prices, hosting, service secrets, rate/retry/timeout/history
values and quality thresholds remain blocked at their dependent activation tasks.
They are not silently chosen defaults or blockers for deterministic local design/mocks.
Data counts, split feasibility, duplicate criteria and corpus sizes require actual audits;
plans define the decision/measurement procedure instead of inventing results.
Constitution and schema proposals remain pending review; no ratification/freeze is claimed.
