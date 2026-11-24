Hi Goran and Nemanja,

Milica approves one 26-case final pass with a NEW combined hard cap USD 0.58
(D USD 0.50 / A USD 0.08), zero retries or repair generations, stop on the first
unexpected error or the 60-minute global deadline, and preservation of all outputs,
errors, usage and reservations. Historical ledgers stay closed and unchanged.
D: 32 calls maximum, 64,000 input / 12,288 output tokens per call, 30 seconds.
A: 16 query embeddings (128 tokens each); 16 calls per question-parts/support/answer
stage, inputs 4096/20000/4096 per call and output 512 each; up to 48 token-count
requests if used; 30 seconds per provider HTTP operation. No corpus reembedding.
The maximum is 144 provider HTTP requests including optional counts, not 112
for the whole system. Final extraction F1 is explicitly unmeasured.

Goran is the designated proposed operator. Before paid dispatch please confirm
his authenticated readiness/model access and enforce the 3600-second watchdog.
Nemanja must provide the exact live A launcher and compatible enforced policy;
these were not included in the CQ-and-limits archive. Verify actual payload/account
rates and materialize the exact final reference/configuration hashes. The app
candidate is 9fc7c33; the counted offline B profile is already received.

The combined serial worst-case provider waits are 72 minutes at 30 seconds per
operation; therefore the 60-minute stop is binding and completion is not promised.
Do not restart a stopped run automatically. Return preserved partial outputs
and errors if it stops. The deadline hour is still unknown; this is not a promise
of completion before submission. No more scope approval needs to be requested
unless these bounds or exact selected configuration change.

D can then score saved outputs against separately held references. Until the
technical launch conditions are met, scope approval alone must not dispatch calls.
