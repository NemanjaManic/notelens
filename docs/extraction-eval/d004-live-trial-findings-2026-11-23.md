# D-004 bounded live trial findings — 2026-11-23

The encrypted local credential was usable by the server-side trial process.
One model-metadata GET succeeded. This did not establish working generation.
Both exact prepared synthetic requests were then attempted once at service
source `c174d9647b6689b7a9069bee87e1313e0f4feaca`, using `gpt-6-luna`,
512 output tokens each and zero retries. Neither produced reviewable output.

| Operation | Exact failing step | Observation |
| --- | --- | --- |
| Extraction | POST /v1/responses | Non-200 response; original transport discarded HTTP status/body. Service returned provider_unavailable. |
| Document answer | POST /v1/responses | HTTP 400, invalid_request_error, parameter input; request ID req_797995b4617a411da8d8ef9921f23485. |

The error parameter identifies where to investigate, not a proven root cause.
No successful response or usage was saved. Do not infer a quota failure, actual
billed amount, or validated output quality. The prepared request hashes and
sanitized evidence are in the [execution receipt](../../eval/reports/development/d004-live-trial-execution-v1.json).

The original D-004 receipt remains unchanged. Separate private execution receipts
and reservations were created. Known prior authorized requests were conservatively
reserved at their full token ceilings; the combined known worst-case reservation
is USD 0.0056454, below USD 0.10. This is not confirmed account billing and cannot
account for undisclosed executions. No balance is invented.

Zero approved inference requests remain. D must diagnose compatibility offline,
prepare any corrected request and show its new pins and bounded scope before
requesting fresh execution authorization. Changing input format is not yet a
verified fix. Never repeat either original request under the exhausted approval.

D-004 and D-005 stay open: there are no provider outputs to review for source
support, completeness, citations or English. Goran's configured app recheck must
wait for a reviewed service handoff; passing mock evidence remains separate.
Credentials and synthetic payloads/receipts stay outside Git; no credentials were
included in this report. Deployment acceptance and unseen final measurement remain
pending.
