# Agent evidence review: A-QA-02 and A-QA-03

**Reviewed:** 2026-11-20
**Reviewer:** Codex coding agent
**Review type:** Evidence-based agent review; not human review or team approval.
**Inputs:** The user-supplied five-passage A-004 packet and A's retained actual partial-answer packet.
**Scope:** The supplied passages only. These judgments do not establish facts outside that scope.

All ten full-passage SHA-256 values in the supplied A-QA-02/A-QA-03 packet were recomputed and matched. The actual A-QA-02 answer's `[0, 373)` citation hash also matches its passage slice.

## A-QA-02

Question: “What causes COVID-19, and how long can an infected person transmit it to others?”

| Requested fact | Verdict | Passage evidence |
| --- | --- | --- |
| Cause of COVID-19 | Supported | Rank 1, *COVID-19 (Coronavirus Disease 2019)*: “This virus is a coronavirus called SARS-CoV-2.” |
| Duration of COVID-19 contagiousness | Missing | None of the five passages gives a COVID-19 transmission duration. Rank 4's “People who have an RSV infection are usually contagious for 3 to 8 days” concerns RSV. Rank 3's statement that pertussis bacteria are gone after three weeks concerns whooping cough. Neither supplies a COVID-19 duration. |

**Overall coverage: Partial.** The cause is supported; the requested duration is missing from this passage set.

### Review of the retained actual answer

The retained answer says, “COVID-19 is caused by SARS-CoV-2, a coronavirus.” Its rank-1 citation points to `[0, 373)` of the supplied 450-code-point passage. Recomputing the SHA-256 from the packet gives `08e5a3e23d4d4663e25da5375c021f3c76f4709d7c3821b1e7cef306b8e02917`, matching the answer record. The full supplied passage hash matches `0112704bed90f50771993b331904aabe1bd8263ebc30b98eca5e3661fcc3861c`.

The claim is supported by the cited passage. The response is appropriately partial and its warning accurately identifies the missing duration. It does not borrow the RSV or whooping-cough durations. The answer-review rubric dimensions are all assessed as meeting for this partial response: source support, required facts available in scope, extra facts, uncertainty and context, evidence gaps, scope and safety, and clarity and English. Coverage is **partly answerable** and the response action is **partial answer**. No critical error is identified.

This is a Codex agent assessment, not a human rating. The checkout already contained A's earlier agent assessment, so this review was not blinded. It is one reviewed output and is not a calibrated answer-risk result or D-008 human-review completion.

## A-QA-03

Question: “What was the incidence of trigeminal neuralgia in Serbia in 2025, in new cases per 100,000 people?”

| Requested fact | Verdict | Passage evidence |
| --- | --- | --- |
| Trigeminal neuralgia incidence in Serbia in 2025, per 100,000 people | Missing | None of the five passages reports a Serbian 2025 incidence rate or a new-cases-per-100,000 statistic. Rank 1 says “TN usually affects people over 50, especially women,” which is a demographic description, not the requested rate. |

**Overall coverage: None.** The supplied passages provide no requested statistic. The available local abstention is an authored fixture, not an actual generated answer, so no answer-quality rating is assigned to it.

## Limits

The review confirms support only against the supplied passage text and its recorded hashes. The pinned corpus JSONL was unavailable, so this does not verify the passage artifact against the complete corpus. The review also does not replace independent human review, source-owner adjudication, or the remaining development/final QA selection.
