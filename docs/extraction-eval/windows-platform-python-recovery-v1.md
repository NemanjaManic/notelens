# Windows platform interpreter recovery

Diagnosis: Code Integrity events 3077 and 3033 explicitly reject the platform
venv Python under signing policy 0283ac0f-fff1-49ae-ada1-8a933130cad6.
Event 3118 records Smart App Control blocking. Authenticode reports NotSigned.
This is an executable trust block before Python starts, not a missing pip package
or a Next.js application failure. A PowerShell execution-policy change does not
repair executable signing and is not recommended here.

## Approved recovery

An authorized Windows administrator must inspect the recorded executable hash
and choose an approved Python 3.13 distribution/install route or approve the
reviewed binary through the applicable policy process. Recreate the platform's
service-local environments from unchanged committed uv.lock files using that
approved route. Do not replace binaries opportunistically, run the denied checks
through another interpreter, disable Smart App Control or alter signing policy
without authorized administration. A working D interpreter alone does not prove
that the denied platform interpreter or its runtime has been approved.

After approval, first verify the platform interpreter can print its version.
Then repeat the default mock smoke, security audit, separate pinned e61140d
D-005 app check and readiness check. Keep indexed RAG separate until its locked
indexing extra is installed. Record the approved runtime version, exact platform
SHA, outcome and failing step. No existing web pass or live generation is implied.

## Ready message to the Windows administrator

Please review the Python execution block for NoteLens. Code Integrity events
3077/3033 and Smart App Control event 3118 identify a signing-policy rejection.
Blocked executable: repo-d009-platform/services/extraction/.venv/Scripts/python.exe.
SHA-256: 9c5369e46d1cf545aac3ceee792327c299b91e6c9b3f9496051709a60cd39dae.
Please confirm the approved Python 3.13 installation route and restore the locked
service environments, or approve the reviewed executable through your normal
policy process. We need no disabling of security controls and no credentials in
reply. Please provide runtime/setup status so we can rerun the key-free web checks.
