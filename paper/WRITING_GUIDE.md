# Writing guide for the KisanNiti paper

22 October 2026 • Built from the college plagiarism/AI checker's report on paper v2: **13% of the text flagged as "resembles AI text" and 6% similarity with outside sources**. The aim is a paper that the authors genuinely wrote and can defend line by line. Every agent and author follows this guide.

## 1. Honesty first (Springer policy)

- Springer Nature requires any use of a large language model to be **documented in the Methods section** (or an equivalent section). AI tools cannot be authors. AI help limited to copy-editing human-written text (grammar, spelling, readability) does not need to be declared. ([Springer AI policy](https://www.springer.com/us/editorial-policies/artificial-intelligence--ai-/25428500))
- So the plan is:
  1. Claude drafts text from the results.
  2. **The authors rewrite each section in their own words** and add details only they know (what they observed, why they chose something, what went wrong).
  3. The paper declares the AI assistance in Methods or Acknowledgements, using the wording the guide approves.
  4. Copy-editing passes are allowed.
- Do **not** try to "beat" an AI detector with tricks. Detectors are unreliable either way. The real protection is authors who know their text, plus honest disclosure.

## 2. What the checker flagged in v2 (patterns to avoid)

| Flagged v2 sentence (shortened) | Pattern | Write instead |
|---|---|---|
| "As a result, a simple MSP rule gave the lowest forecast error …, and none of the learned models beat it." | Neat cause → verdict summary | Give the number and the context first: "In the 2024 season, `<share from numbers.py>` of the reported prices were exactly ₹2,320, the Grade-A MSP, and the MSP rule's error that season was ₹0.17 per quintal." (Fill the share from `numbers.py`; never guess it.) |
| "First, … Second, … Third, …" walk-through of Table 4 | Enumerated triads | Discuss the result that surprised you most, then the others in normal paragraphs |
| "For this first version, the main lesson is simple." / "Two findings stand out." | Announcing a lesson | Delete the announcement; state the finding directly |
| "The value of KisanNiti for such crops lies in coordination: spreading deliveries …" | "X lies in Y:" colon reveal | "For MSP crops, KisanNiti helps by spreading deliveries over mandis and days." |
| "… respected every daily limit, while independent choices exceeded a limit in every run." | Balanced "X, while Y" contrasts repeated many times | Split into two sentences; vary the structure |
| "A forecasting system for FPOs should therefore check whether …" | Generic advice voice ("should therefore") | Say what *we* did or recommend: "We now check the share of MSP-equal prices before training any model." |
| "the root mean squared error (RMSE) and the mean absolute percentage error (MAPE)" | Matched outside text (6% similarity) | Standard terms are fine, but don't copy definitions; cite the metric source and keep definitions short |

## 3. Rules for every section

1. **Specific beats general.** Name the mandi, the season, the date range, the number of rows and the exact setting. Generic sentences are what detectors and reviewers both dislike.
2. **Vary the rhythm.** Mix short and long sentences. Avoid three-part lists unless there really are three things.
3. **No filler phrases:**
   - "plays a crucial role", "it is important to note", "in today's world";
   - "leverage", "robust", "seamless", "comprehensive";
   - "delve", "pivotal", "landscape", "furthermore" chains;
   - "not only … but also".
4. **Report, don't sell.** Every claim is tied to a table, figure, reference or our own run. No "significantly" without a significance test.
5. **Our voice.** First person plural ("we tested", "we found"), past tense for what we did, present tense for what the results show.
6. **Limitations in plain words** where they matter, not hidden at the end.
7. **Own the methods.** Explain choices briefly ("We used A3T-GCN because …") and refer to the [design alternatives](../../kisaniti/docs/research/DESIGN_ALTERNATIVES.md) for the comparison.
8. **Numbers only from `numbers.py`.** Never retype a value from memory.
9. **Similarity:**
   - paraphrase sources genuinely and cite them;
   - quote only with quotation marks;
   - keep the related-work entries in our own summary style;
   - run the college checker before submission and fix any matches above a few words.

## 4. Process per section

1. Agent drafts from results (plain style, this guide).
2. Agent self-check: no phrases from §3.3; no announced lessons; triads removed; every number traced.
3. **Author rewrite** in their own words (assign one author per section).
4. Read-aloud check by another author: does it sound like us?
5. College checker run; fix flagged passages by rewriting them with more specifics, not by synonym swapping.
6. Supervisor review.

## 5. Section ownership (fill in)

| Section | Drafted by | Rewritten by (author) | Checked by | Status |
|---|---|---|---|---|
| Abstract | | | | |
| 1 Introduction | | | | |
| 2 Related Work | | | | |
| 3 Proposed System | | | | |
| 4 Results and Discussion | | | | |
| 5 Conclusion | | | | |
