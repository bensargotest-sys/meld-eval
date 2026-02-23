# T9: Scaling Curve Test Report

**Date:** 2026-02-23
**Test ID:** T9
**Status:** ✅ Complete (reduced sample due to OpenRouter 402)

## Hypothesis
More models in consensus = better quality. What's the optimal number?

## Method
- **Questions:** 50 (12-15 fully clean due to OpenRouter credit exhaustion)
- **Conditions:**
  - A: GPT-4o solo (baseline)
  - B: 2-model consensus → GPT-4o synthesis
  - C: 3-model consensus → GPT-4o synthesis
  - D: 4-model consensus → GPT-4o synthesis
  - E: 5-model consensus → GPT-4o synthesis
- **Judge:** GPT-4o-mini, 99 judgments
- **Note:** OpenRouter 402 errors after ~15 clean questions cut the experiment short

## Results

| Comparison | Finding |
|-----------|---------|
| Any consensus vs solo | **Consensus wins** |
| 3 models vs 2 models | Modest improvement |
| 4 models vs 3 models | **No measurable improvement (ties)** |
| 5 models vs 4 models | **No measurable improvement (ties)** |

## Key Findings

1. **Any consensus beats solo.** Even 2 models + synthesis outperforms a single model.

2. **3 models is the sweet spot.** Going from 2→3 shows improvement. Going from 3→4→5 shows nothing.

3. **Diminishing returns hit fast.** C, D, and E are essentially tied. Adding more models beyond 3 adds latency and cost without quality improvement.

4. **Network implication:** MELD doesn't need massive networks. 3 diverse frontier models is sufficient. Quality of participants matters more than quantity.

## Caveats

- **Very small clean sample (12-15 questions)** — OpenRouter credit exhaustion truncated the experiment
- Results are directionally clear but lack statistical power
- Only tested with GPT-4o synthesis — different synthesizers might benefit from more inputs

## Confidence: 5/10
- Clear directional signal (3 > 2 > 1, but 4 ≈ 5 ≈ 3)
- Very small sample size
- Single synthesis model tested
- Consistent with theoretical expectations (diversity of ~10 model families creates a natural ceiling)

## Strategic Implication
MELD's product tiers should optimize for 3-model consensus as the default. "Giga Brain" (5+ models) may not justify the additional cost and latency.
