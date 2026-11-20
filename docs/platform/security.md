# B-008 mock security verification

The local mock workspace renders document text, claims, evidence quotes and
retrieved passages as text. Literature links require credential-free HTTPS and
are followed by the user. NoteLens does not fetch those links. Responses suppress
the referrer and require browsers to respect the declared content type.

The two dynamically rendered web pages use a fresh content security policy
nonce for each response. The production policy protects framework scripts,
blocks unapproved script execution and framing, and restricts form submissions
and browser API requests to the same origin. See the
[Next.js nonce integration guide](https://nextjs.org/docs/app/guides/content-security-policy).

Text and PDF submissions use the approved 100,000-code-point and 2 MiB limits.
An oversized declared body or an unsupported content encoding is rejected
before opening a session. The stream reader also enforces the byte limit for
chunked uploads. PDF extraction runs in its bounded worker.

Browser mutations require the configured origin. Access to a report and its
history requires the owning session cookie. Reports and mutation responses are
served with `no-store`. The loopback mock launcher strips inherited provider
settings, uses ephemeral service authentication, and disables service access logs.

## Reproduce on Windows

From the repository root after locked setup, run the production build and
the key-free checks.

```powershell
$env:NEXT_TELEMETRY_DISABLED = '1'
npm.cmd run build
& .\scripts\project\.venv\Scripts\python.exe -B scripts/project/check_mock_security.py
& .\scripts\project\.venv\Scripts\python.exe -B scripts/project/smoke_mock.py
node apps/web/scripts/check-report.mjs
node apps/web/scripts/check-preparation.mjs
node apps/web/scripts/check-sessions.mjs
```

The HTTP audit verifies nonce enforcement on responses, escaped markup,
declared and chunked upload boundaries, same-origin checks, foreign and
revoked sessions, and generic errors for malformed input. It scans stdout
and stderr from the four real mock processes in memory. It checks for
synthetic document and question text, inherited fake provider settings,
ephemeral service tokens, and browser session capabilities.

The rendering checks cover inert retrieved text and citation URL validation.
The session checks use a controlled clock for expiry and exercise the rolling
admission limits. The mock smoke exercises the question rate limit and
retained citations across sufficient, insufficient, and unavailable literature.

Chrome verification uses [the security scenario](../../apps/web/tests/security/browser.scenarios.js)
on the local demo, then on the saved turn in a second isolated browser context.
The [upload scenario](../../apps/web/tests/submitted-input-browser.scenarios.js)
at `/demo#reject` covers invalid inputs and proves that a valid PDF at exactly
2 MiB is accepted. The browser runs passed 13 security assertions and 12 upload
assertions. The build, HTTP audit, three smoke scenarios, 41 render checks,
51 preparation checks, 39 session checks, and 17 routing checks passed.

This evidence covers the finite local mock suite. Real provider behavior will
be evaluated with the B-005 integrations.
