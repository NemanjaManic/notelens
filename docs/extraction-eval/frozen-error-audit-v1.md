# Bounded frozen-output error audit

Six candidate development documents were audited without new provider calls.
There are 204 reference mentions and 185 predictions: 91 exact matches, 34
additional same-type overlap matches, 79 reference mentions without same-type
overlap and 60 predictions without same-type overlap. Overlap is diagnostic,
not proof of an equivalent clinical concept or a substitute for exact scoring.

All 11 rejected model entities failed occurrence resolution. Reordering the
model-supplied supporting evidence recovered zero unique additional mentions.
This does not establish that no other bug can exist. It finds no demonstrated
cheap adapter correction in the inspected path. Guessing repeated occurrences,
rewriting labels or trimming mentions to reference answers would not be a valid fix.

Decision: retain frozen runtime d41fa880177a7855bb92e57d98673b0a7a77d36b.
No runtime, prompt, reference or threshold changed. No new API cost or final-set
access occurred. Quality acceptance and independent semantic evidence remain open.
Prioritize the configured app receipt and final delivery evidence.

[Per-case audit](../../eval/reports/development/d011-frozen-error-audit-v1.json).
