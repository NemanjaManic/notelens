# Tutor session question guard

The interactive web question endpoint admits at most five questions during one
server-issued browser session, shared across that session's documents. The sixth
new question returns HTTP 429 before service dispatch. This is a question quota,
not a count of individual provider requests or a USD spending cap. Starting a new
session obtains a separate quota; this feature does not provide an account-wide
budget or protection against a user creating additional sessions.

For the same document, resubmitting the same question returns HTTP 409 before
service dispatch. Comparison ignores letter case and repeated whitespace and
retains the document and literature branch identity. The guard stores SHA-256
identifiers in session memory, not an additional copy of question bodies.
Concurrent submissions continue to allow only one pending question per session.

Admission reserves a slot before any await or downstream dispatch. Failed or
cancelled admitted work still consumes its slot. Clearing chat history, deleting
a document or replacing it does not refund slots. Session expiry removes these
identifiers with the existing in-memory session. This does not implement answer
caching or persist quotas across process restarts.

The default is interactive protection, including when bounded services are
configured manually. The managed bounded evaluation launcher explicitly selects
`NOTELENS_QUESTION_PROFILE=final-evaluation` so the frozen final workload retains
its existing rate and run-budget controls. That exception requires the server
bounded-evaluation profile; a browser header or request body cannot select it.
Do not use the final-evaluation profile for unrestricted interactive tutor use.

This change does not enable paid providers, grant new spending authorization,
alter D-009 caps, or start a final attempt. An integrated application change
requires a new app commit pin before any subsequent pinned evaluation launch.
