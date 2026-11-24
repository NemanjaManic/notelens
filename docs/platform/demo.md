# B-009 key-free demo rehearsal

## Start the Windows demo

Use the default local mock stack with synthetic inputs. The first rehearsal
used revision `06b3184117f5e73332f278e2e5aa95efbd48de71`. The rerun used the
B-009 built-in button fix on top of that revision. Both used a production
build on Windows with Python 3.13, Node 24 and npm 11.

From the repository root, install the locked dependencies and build:

```powershell
$env:NEXT_TELEMETRY_DISABLED = '1'
foreach ($service in @('scripts/project', 'services/rag', 'services/classifier', 'services/extraction')) {
  uv sync --locked --directory $service --python 3.13 --no-dev
  if ($LASTEXITCODE -ne 0) { throw "Locked dependency setup failed for $service." }
}
npm.cmd ci --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw 'Web dependency setup failed.' }
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Web build failed.' }
uv run --locked --offline --directory scripts/project python -B start_mock.py
```

Open the loopback demo URL printed by the launcher in a fresh Chrome session.
Keep the launcher open during the rehearsal. From a separate terminal, the
finite HTTP smoke runs its own stacks:

```powershell
uv run --locked --offline --directory scripts/project python -B smoke_mock.py
```

This profile uses local mock services and synthetic fixtures. It needs no
provider API keys, fitted model assets or literature corpus. Close the rehearsal
tabs and press Ctrl+C in the launcher terminal when finished.

## Browser rehearsal

1. Open the workspace and check that the page language is English. Verify the
   educational demonstration, not-a-doctor, no-real-personal-reports and
   server-memory retention notices. Check that the workspace identifies itself
   as running in mock mode.
2. Click **Chest pain report**. Verify that the browser POST returns HTTP 201
   and opens **Report overview** at `/demo?document=…` with the question controls.
   Ask the mixed question in step 5 from this report as well as from pasted text.
3. Paste this English synthetic fixture, choose **Synthetic example** as the
   input source, and click **Open pasted text**. For a text-based PDF check,
   export the same lines as selectable text and use **Open PDF**. The
   [browser scenarios](../../apps/web/tests/submitted-input-browser.scenarios.js)
   also generate the inputs for the actual forms.

   ```text
   This synthetic medical report describes a scheduled follow-up. The patient reports no new symptoms today.
   No chest pain.
   The care team recorded the examination findings.
   No chest pain.
   Colonoscopy is planned for next week.
   ```

4. Check that the prepared document, specialty, extraction and summary panels
   render in English. Choose **Document** and ask “What does the document say
   about chest pain?” Verify the evidence state and follow both document
   citations. They should keep the document identity and highlight separate
   occurrences of the same exact canonical quote. The offsets should describe
   the locations in the canonical document the app displays.
5. Choose **Both**, enter the same document question and set the literature
   question to “What is the synthetic demo topic?” Verify the document
   citations and the separately attributed synthetic literature title and URL.
   The literature URL is a fixture value under `example.invalid`.
6. Verify that an input outside the English-only policy receives an English
   error. Use a new anonymous browser session for further submissions after
   reaching the three-active-document limit.

## Observed results

| Check | Result |
| --- | --- |
| Production build and key-free HTTP smoke | Passed. The HTTP smoke covered report ownership, free-text routing, citations, history, limits and smoke stack shutdown. The separate production mock security check also passed. |
| English workspace and notices | Passed in Chrome. The educational demonstration, not-a-doctor, no-real-personal-reports, 60-minute retention and local-mock labels were visible. All 12 submitted-input browser scenarios passed, including English feedback for non-English and mixed-language documents. |
| Pasted text to mixed answer | Passed in Chrome. Submission returned HTTP 201 and the mixed question returned HTTP 200 with sufficient evidence. Both document links led to the correct occurrences of `No chest pain.` in the same canonical document. The literature evidence showed the title `Synthetic NoteLens Literature Example` and its separate fixture URL. |
| Text-based PDF to document answer | Passed in Chrome. The extracted report and attributed summary rendered. The document-only question showed sufficient evidence. Both cited occurrences highlighted separately with the exact canonical quote and code-point location. |
| Built-in example to mixed answer | Passed in Chrome after the fix. **Chest pain report** returned HTTP 201 and opened **Report overview**. The mixed question returned HTTP 200 with sufficient evidence. Both document citations highlighted their exact occurrences and the answer showed the separate synthetic literature title and URL. The owner could reopen the same report. |
| Built-in origin validation | Chrome sent the configured loopback origin and kept the no-referrer policy. All six direct HTTP checks for missing, null and foreign origins returned HTTP 403 with no session cookie or redirect, in both response modes. |

The first rehearsal found that the native navigation POST sent `Origin: null`
under the workspace's [no-referrer policy](../../apps/web/next.config.ts). The
[button](../../apps/web/src/components/builtin-example-button.tsx) now makes a
same-origin fetch and opens the report after the API returns its document ID.
The [server origin check](../../apps/web/src/lib/sessions/route.ts) still requires
the configured web origin. Existing HTTP callers retain the 303 response.

## Clean-main rehearsal

Replayed the button fix on `main` at `02cc96dad204bc3c29338e2486754ce1ad0ba372`
using Windows, Python 3.13.7, Node 24.22.1, npm 11.19.1 and headless Chrome 157.
The locked production build passed.

- The built-in button returned HTTP 201 and opened the owner’s report.
  Seven picker assertions and 18 mixed-answer assertions passed.
- The pasted-text mixed answer and the PDF document-only answer each passed
  18 assertions. The rerun verified English notices, the exact repeated
  highlights and separate literature attribution for mixed answers.
- All 12 submitted-input policy checks passed, including English feedback for
  non-English and mixed-language text.
- All six missing, null and foreign-origin requests returned HTTP 403 without
  issuing a session cookie or redirect. All four rehearsal listeners stopped.

The key-free browser rehearsal passed. B-009 formal acceptance depends on
B-005 and B-008 as listed in the [platform tasks](../../specs/002-platform/tasks.md).
Provider-backed behavior is outside this run.

## PR #32 reviewed-head rehearsal

On 23 November 2026, the Windows loopback mock rehearsal passed on PR #32's
reviewed head `7743fc87aafa94f42b6fd81e34a48612352da1f1` with Python 3.13.7,
Node 24.22.1, and headless Chrome 158. The production build and key-free HTTP
smoke passed.

- The built-in example and pasted synthetic text each produced a sufficient mixed
  answer. The selectable-text PDF produced a sufficient document-only answer.
  All three submissions returned HTTP 201 and all three questions returned HTTP 200.
- Chrome passed 73 assertions covering English controls and rejection messages,
  the educational-demo, not-a-doctor, no-real-personal-reports and retention notices,
  and the mock-profile label. Both mixed answers showed separate literature
  attribution, and each flow verified two exact document highlights.
- All four loopback listeners and the Chrome rehearsal session stopped. The
  built-in flow's trace also recorded an incidental `/favicon.ico` HTTP 404.

Receipt `B009-PR32-Chrome-rehearsal-7743fc8.json` has SHA-256
`e8542823dd6862079feee84f6744c90ac2518727974dc4e4f3e1b74b93d009df`.
The rehearsal used synthetic fixtures and made zero provider calls. Formal
B-009 acceptance is pending against the accepted B-005 configuration.
