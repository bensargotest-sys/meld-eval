# Domain Generalizability Test Report

**Date:** 2026-02-23
**Test ID:** Domain V2
**Status:** ✅ Complete

## Hypothesis
Multi-model consensus advantage holds across specialized domains (code, math, analysis), not just general knowledge.

## Method
- **Questions:** 50 (20 code, 20 math, 10 analysis)
- **Conditions:**
  - A (Solo): GPT-4o single model
  - B (Consensus): 3-model consensus (Grok-3 + Gemini Flash + DeepSeek) → GPT-4o synthesis
- **Judge:** GPT-4o-mini, 0 errors, 2 swapped judgments per question (100 total)
- **APIs:** All direct (no OpenRouter dependency)

## Results

| Domain | N | Consensus Wins | Solo Wins | Tie | Consensus Win Rate |
|--------|---|---------------|-----------|-----|-------------------|
| **Analysis** | 20 | **19 (95.0%)** | 1 (5.0%) | 0 (0%) | 95.0% |
| **Math** | 40 | **23 (57.5%)** | 2 (5.0%) | 15 (37.5%) | 57.5% |
| **Code** | 40 | **20 (50.0%)** | 8 (20.0%) | 12 (30.0%) | 50.0% |
| **Overall** | 100 | **62 (62.0%)** | 11 (11.0%) | 27 (27.0%) | 62.0% |

### Judge Agreement (swap consistency)
- Code: 90%
- Math: 85%
- Analysis: 90%

## Key Findings

1. **Consensus wins in ALL domains.** Zero domains where solo outperforms consensus. This generalizes beyond general knowledge.

2. **Analysis is a blowout (95%).** Open-ended analytical questions benefit most from diverse perspectives. Multiple models catch different angles, and synthesis combines them effectively.

3. **Math has more ties (37.5%).** Mathematical problems tend toward single correct answers — when both get it right, it's a tie. But consensus still wins 57.5% vs 5% solo.

4. **Code shows solo's best performance (20% wins).** Single models can nail clean implementations. But consensus still wins 2.5x more often than solo (50% vs 20%).

5. **Solo almost never wins outright.** Even in code (solo's best domain), consensus wins 2.5x more. In math and analysis, solo wins ≤5%.

## Strategic Implications

- **"Works for code too"** is a strong pitch addition — developers are the primary audience for AI agents.
- **Analysis/strategy tasks** are the highest-value consensus use case (95% win rate).
- **Math/code tasks** still benefit but with diminishing marginal gains — many problems have a single right answer that any good model can find.
- The results suggest **consensus is most valuable when problems are open-ended** and benefit from multiple perspectives.

## Confidence: 7/10
- Strong directional signal across all domains
- Moderate sample size (50 questions)
- Single judge model (GPT-4o-mini)
- No human validation yet
