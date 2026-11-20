# Development evidence-gap proposals

These seven English questions target three topics in the prepared MedlinePlus corpus. Each pair has a supported control and a question that requests a more specific fact. The acute bronchitis follow-up combines both parts in one question. The jaundice and carpal tunnel controls reuse facts from the earlier public smoke questions, making these paired checks suitable for development.

| Topic at rank one | Full coverage | No coverage in the top five | Partial coverage |
| --- | --- | --- | --- |
| Jaundice | EG-01 asks what causes the discoloration. | EG-02 asks for the percentage of newborns in Serbia with first-week jaundice in 2025. The summary mentions first-week jaundice generally. | |
| Acute Bronchitis | EG-03 asks for a common cause. | EG-04 asks for a difference in cough duration by tobacco-smoke exposure. Related passages describe exposure and cough duration without comparing the two groups. | EG-07 asks both questions. The cause is supported and the duration comparison remains a gap. |
| Carpal Tunnel Syndrome | EG-05 asks which nerve is compressed. | EG-06 asks for a diagnostic nerve conduction time cutoff in milliseconds. A passage mentions electrical tests without giving a numerical cutoff. | |

The target topic ranked first in all seven local BM25 results. The Member A coding agent assigned three full, one partial and three no-coverage labels from the returned passages on 2026-11-18. The [proposal record](evidence-gap-proposals.json) contains the exact questions, ordered candidates, part-level notes and canonical evidence spans. A missing label applies to the recorded top five. Independent review is pending. The cases are separate from the [existing development proposals](../qa-proposals.json) and are excluded from final evaluation and corpus ingestion.

With the prepared corpus and the locked RAG environment available, replay the rankings and verify the quote hashes at their recorded Unicode code-point spans.

```powershell
uv run --locked --offline --directory services/rag python ../../docs/rag/evaluation/verify_evidence_gap_proposals.py
```

The verifier checks the recorded BM25 settings, candidate order, rank-one topic, span bounds, quote hashes and consistency between part labels and case coverage. Semantic support remains a reviewer judgment. This diagnostic uses local BM25 only and makes zero provider calls. It supplies examples for evidence calibration under A-004 without selecting a runtime threshold.
