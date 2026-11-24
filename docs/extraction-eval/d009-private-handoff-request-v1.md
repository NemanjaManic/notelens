# D-009 restricted final package request — ready to send

Hi Sara and Goran,

The 26 final QA cases are the versions reconciled in
`d007-final-qa-metadata-status-v5.json` (SHA-256
945ec966e33b7221c95bd83e4dbb37531eef365fdb8d04b933f2a498e87ea247):
eight F-DOC, eight F-LIT, eight F-MIX and two F-OOS cases. The approved identities
are 25 v1 cases and F-DOC-06 v2, with both reviewer-receipt sets. Please keep the
full cases, source texts, questions and answer keys in restricted custody.

Goran, please return your configured D-005 app receipt with exact app/service
SHAs, profile and results for document identity, exact highlights, partial gaps
and insufficient versus out-of-scope behavior. Please flag any failing step.

The broader D-011 pilot failed its quality gate, so the joint final run is not
yet authorized. D will remediate and remeasure the service. Before final execution,
we also need the recorded eligibility disposition for the technical-note exposure
of F-DOC-01/02/03; please do not declare all 26 fully unseen without resolving it.

Once quality/app/eligibility gates and the joint freeze are approved, please use
the exact restricted case inventory for the bounded final run. Keep runtime
source/question inputs separate from gold answers, annotations and relevance
labels. Provide the authorized scorer, through the approved private route:

- Final inventory with each case ID, version, source-family/group IDs and all
  source/case hashes, plus corresponding review receipts.
- Separately pinned final references and saved predictions for extraction/document
  QA, retrieval and answer-risk scoring. Extraction final ground truth must be
  separate from the D-013 development references.
- Selected service/model/prompt/corpus/index/retriever identities, raw provider
  envelopes, usage, execution receipts and independently justified correctness
  labels; include technical failures instead of excluding them.
- A checksum manifest and the named operator/freeze approvals.

The prepared scorer format and unapproved candidate are in
`eval/config/d009-final-freeze-candidate-v1.json`; missing final hashes are
deliberately unfilled. Please confirm package readiness and the handoff date
without sending final texts or answer keys into this chat.

Thanks,
Milica

This is a locally prepared message. The agent has not sent it or contacted anyone.
