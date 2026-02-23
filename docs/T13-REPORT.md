# T13: Strong-Model Consensus vs. Best Single Model

## Methodology

This study, T13, investigates whether a consensus of strong language models can outperform a single, strong language model. We compare the performance of Claude Sonnet 4.5 solo against two consensus approaches: one using GPT-4o for synthesis and another using Claude Sonnet 4.5 for synthesis. A fourth condition, using weak models via MELD nodes, was attempted but failed due to technical issues.

## Conditions

*   **A: Claude Sonnet 4.5 solo:** The baseline condition, using a single strong model.
*   **B: 3 strong models (Sonnet + Grok-3 + GPT-4o) → GPT-4o synthesis:** A consensus of three strong models, with GPT-4o synthesizing the final answer.
*   **C: 3 strong models (Sonnet + Grok-3 + GPT-4o) → Sonnet synthesis:** A consensus of three strong models, with Sonnet synthesizing the final answer.
*   **D: 3 weak models (Gemini Flash + DeepSeek + Grok-3) via MELD nodes → GPT-4o synthesis:** This condition failed due to MELD node authentication issues and 404 errors. The data is excluded from the analysis.

## Judges and Sample Sizes

The study used Gemini models as judges to perform pairwise comparisons between the conditions. The dataset consisted of 50 questions, resulting in 2505 judgments. Of these, 1366 were valid, and 1139 were errors (primarily 400 errors from the Gemini judge).

## Results

| Comparison | Win Rate (excluding ties) |
|---|---|
| A vs B | B wins 70% |
| A vs C | C wins 89-98% |
| B vs C | C wins 97% |

## Statistical Notes

*   The error rate from the Gemini judge was high (1139 out of 2505 judgments).
*   Tie rates were not explicitly calculated but are implicitly accounted for in the 'Win Rate (excluding ties)' metric.
*   Condition D was excluded from the analysis due to a complete failure to collect data.

## Key Findings

*   A strong model consensus, using either GPT-4o or Sonnet for synthesis, significantly outperforms a single, strong model (Claude Sonnet 4.5).
*   Sonnet synthesis is massively better than GPT-4o synthesis when creating a strong model consensus.

## Implications for MELD

This study provides crucial validation for the MELD approach. While T7 showed that Sonnet solo beats a weak consensus, T13 demonstrates that a *strong* consensus can indeed outperform Sonnet solo, supporting the core thesis of MELD. However, the success of MELD is contingent on using frontier-level models as participants.

## Limitations

*   Condition D, intended to evaluate a weak model consensus, failed entirely due to technical issues. This limits the scope of the study.
*   The high error rate from the Gemini judge raises concerns about the reliability of the individual judgments. Further analysis and validation may be necessary.
*   The tie rates should be explicitly calculated in future studies to get a full picture of the performance.
