# Reply to B: Review Update

Hi B,

Thanks for the review. I addressed all four findings in the D working copy:

1. **Procedure answer:** The mock now selects procedure mentions generally, so the canonical planned-colonoscopy fixture is supported. A regression checks the extraction and answer against the frozen fixture, including the exact evidence quote, `doc_id`, and `text_sha256`.
2. **Promptfoo readiness:** The smoke wrapper now polls `/health/ready` and checks for mock mode and an `ok` readiness status.
3. **Request-ID admission:** Business requests without exactly one canonical UUID `X-Request-ID` now receive the frozen 400 admission response before authentication is checked. Health endpoints retain fresh diagnostic IDs and ignore incoming IDs.
4. **Duplicate authorization:** When a service token is configured, duplicate `Authorization` headers are rejected on business and health endpoints, regardless of header order. Regressions also cover valid and invalid single authorization headers.

**Verification run:**

- Extraction service: `python -m pytest tests -q` — **59 passed**.
- Evaluation readiness: `python -m pytest tests/test_readiness.py -q` — **6 passed**.
- Unmodified smoke wrapper: `python smoke_http.py` — Promptfoo **3/3 passed**.
- `git diff --check` — passed.

The first smoke attempt hit a Node `os.userInfo()` `ENOMEM` error before evaluation started. The successful rerun used a temporary process-only preload to supply user information; the smoke wrapper and evaluation configuration were unchanged.

The corrected changes are currently uncommitted. The checkout's current `HEAD` remains `3e7e64ed130eeacc1eb0567e927e7ad64264d55e`; this is not a corrected commit hash. I have not published a commit.

Best,
D
