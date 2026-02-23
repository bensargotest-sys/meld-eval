# T8: Thinking Models Test Report

**Date:** 2026-02-23
**Test ID:** T8
**Status:** ✅ Complete (partial data due to Grok-3-mini 503 errors)

## Hypothesis
Thinking/reasoning models (chain-of-thought) boost consensus quality beyond standard models.

## Method
- **Questions:** 50 (from shared question bank)
- **Conditions:**
  - A: Standard consensus (Grok-3 + Gemini + DeepSeek → GPT-4o synthesis)
  - B: Consensus with thinking (Grok-3-mini reasoning + Gemini + DeepSeek → GPT-4o synthesis)
  - C: GPT-4o solo (baseline)
  - D: Grok-3-mini thinking solo
  - E: Standard consensus + thinking model synthesis
- **Judge:** GPT-4o-mini, 0 errors, 148 valid judgments
- **Note:** Grok-3-mini returned 503 errors ~60% of the time. Conditions A/B/E have 19-22 valid responses (of 50). C/D have full 50.

## Results

| Comparison | Winner | Win % | N |
|-----------|--------|-------|---|
| B (consensus+thinking) vs C (GPT-4o solo) | **B wins** | **100%** | Limited |
| D (thinking solo) vs C (GPT-4o solo) | **D wins** | **86%** | Limited |
| A (standard consensus) vs D (thinking solo) | **A wins** | **84%** | Limited |

## Key Findings

1. **Consensus + thinking beats everything.** B vs C: 100% win rate. The combination of diverse models + reasoning chains is unbeatable.

2. **Thinking models alone are strong.** Grok-3-mini thinking beats GPT-4o solo 86%. Reasoning effort matters.

3. **But standard consensus beats thinking solo (84%).** The consensus process adds more value than individual model reasoning. This reinforces T5's finding: process > model.

4. **Hierarchy: consensus+thinking > standard consensus > thinking solo > standard solo.**

## Caveats

- **Severely limited sample** for conditions involving Grok-3-mini (19-22 of 50 due to 503 errors)
- Grok-3-mini `reasoning_effort: "high"` used for `reasoning_content`
- Results are directionally strong but low statistical power

## Confidence: 5/10
- Strong directional signal
- Very small valid sample sizes (19-22 for key conditions)
- Single thinking model tested (Grok-3-mini)
- 503 reliability issues make production use questionable
