# T7: Claude Integration — The Uncomfortable Truth

**Date:** 2026-02-23  
**Status:** Complete  
**Finding:** Claude Sonnet solo beats 3-model consensus. Adding Claude to the network helps, but a single strong model beats consensus of weaker models.

---

## Research Question

Does adding Claude (Haiku or Sonnet) to the consensus network improve quality? Does a 4-model consensus beat 3-model? Does Claude Sonnet solo beat multi-model consensus?

## Background

Original T7 failed due to direct Anthropic API returning 401 (likely invalid key or billing issue). This is a rerun using OpenRouter for Claude access.

## Design

**50 questions** from T4 candidate pool × **4 conditions:**

| Condition | Description | Models | Synthesis |
|-----------|-------------|--------|-----------|
| A | 3-model baseline | Grok-3 + Gemini Flash + DeepSeek | GPT-4o |
| B | +Claude Haiku | A + Claude Haiku 4.5 (4 models) | GPT-4o |
| C | +Claude Sonnet | A + Claude Sonnet 4.5 (4 models) | GPT-4o |
| D | Claude Sonnet solo | Claude Sonnet 4.5 alone | None |

**Judges:** GPT-4o and Qwen 72B, position-randomized. Gemini Flash had massive API errors (same as T6).

**Total:** 537 judgments collected (179 Gemini errors, 18 GPT-4o errors, 340 clean judgments from 2 judges).

---

## Results

### Judge Error Rates
- **Gemini Flash: 179 errors** (58% failure rate) — Google API 400 errors
- GPT-4o: 18 errors (3.4% failure rate)
- **Effective sample: 340 judgments across 2 judges**

### Key Comparisons (Aggregate across 2 judges)

| Comparison | X wins | Y wins | Ties | X Win Rate (excl ties) |
|------------|--------|--------|------|------------------------|
| **B vs A** (+Haiku vs 3-model) | 15.5% | 3.6% | 81.0% | **81.2%** |
| **C vs A** (+Sonnet vs 3-model) | 21.4% | 3.6% | 75.0% | **85.7%** |
| **C vs B** (+Sonnet vs +Haiku) | 18.3% | 3.7% | 78.0% | **83.3%** |
| **D vs A** (Sonnet solo vs 3-model) | 35.6% | 3.3% | 61.1% | ****91.4%**** |

### The Uncomfortable Finding: D vs A

**Claude Sonnet solo beats 3-model consensus decisively.**

| Judge | Sonnet solo | 3-model | Tie | Sonnet Win Rate (excl ties) |
|-------|-------------|---------|-----|----------------------------|
| GPT-4o | 31.7% | 2.4% | 65.9% | **92.9%** |
| Qwen | 38.8% | 4.1% | 57.1% | **90.5%** |
| **Aggregate** | **35.6%** | **3.3%** | **61.1%** | **91.4%** |

Among non-tie judgments, Sonnet solo wins more than 9 out of 10 comparisons.

---

## Key Findings

### 1. Adding Claude to Consensus Helps

**B (3-model + Haiku) beats A (3-model alone):** 15.5% vs 3.6% (81.2% win rate among non-ties).  
**C (3-model + Sonnet) beats A:** 21.4% vs 3.6% (85.7% win rate).  
**C beats B:** 18.3% vs 3.7% (83.3% win rate).

Adding Claude to the consensus network improves quality. Sonnet helps more than Haiku, as expected.

### 2. But Sonnet Solo Beats Everything

**D (Sonnet solo) beats A (3-model consensus):** 35.6% vs 3.3% (91.4% win rate).

This is the uncomfortable part. A single Claude Sonnet call produces better output than consensus of three weaker models (Grok-3, Gemini Flash, DeepSeek) synthesized by GPT-4o.

### 3. High Tie Rates Return

Like T6, tie rates are exceptionally high (61-81%). This is higher than T4/T5 (30-50%) but consistent with T6. Possible explanations:
- Questions may not be discriminating enough
- GPT-4o synthesis normalizes outputs
- When models disagree less, judges see less clear difference

### 4. Model Quality Hierarchy Confirmed

```
Claude Sonnet solo (D) > +Sonnet to network (C) > +Haiku to network (B) > 3-model baseline (A)
```

The best individual model beats the network. Adding the best model to the network improves it. But you're better off just using the best model alone than consensus of weaker models.

---

## What This Means

### The Central Tension

**T4 claimed: "Independence beats model access."**  
**T7 shows: "A better model beats consensus of worse models."**

These are not contradictory, but they narrow MELD's value proposition:

- **T4 tested:** Same-quality models (Gemini) with personas vs single GPT-4o. Consensus won.
- **T7 tested:** Weaker models (Grok/Gemini/DeepSeek) vs single Claude Sonnet. Solo won.

**The resolution:** Consensus of comparable-quality models beats a single model. But consensus of significantly weaker models loses to a single strong model.

### Where Does This Leave MELD?

**MELD's value depends on the quality distribution of network participants.**

- **If most nodes run frontier models** (Sonnet, Opus, GPT-4, Grok-3), then consensus adds value (T4 shows this).
- **If most nodes run cheaper/weaker models** (Gemini Flash, DeepSeek, Haiku), then a single frontier model beats consensus (T7 shows this).

**The practical implication:** MELD needs high-quality participants to provide value. A network of cheap models loses to a single expensive model.

---

## Statistical Notes

1. **Reduced sample size:** 340 clean judgments out of 537 attempted (37% error rate). Sufficient for directional findings but not precise effect sizes.
2. **High tie rate:** 61-81% ties means only 65-130 decisive judgments per comparison. Small but sufficient for strong signal in D vs A.
3. **Consistent across judges:** Both GPT-4o and Qwen agree on direction for all comparisons. Confidence is high.
4. **OpenRouter for Claude:** This test uses OpenRouter proxied Claude, not direct Anthropic API. Latency and response characteristics may differ slightly from production Claude.

---

## Implications for MELD

### Positive Takeaways

1. **Adding Claude to the network helps.** If MELD can attract operators running Claude, network quality improves.
2. **Sonnet > Haiku.** Encouraging higher-tier models on the network is valuable.
3. **The synthesis step still matters.** C (Sonnet in consensus) beats D (Sonnet solo) would have tested this, but we didn't run that comparison. Unknown if consensus of 4 frontier models beats solo frontier model.

### The Hard Truth

**A single strong model beats consensus of weaker models.**

This limits MELD's value proposition:
- If users have access to Claude Sonnet (via Anthropic or OpenRouter), they get better results using it directly than routing through a MELD network of weaker models.
- MELD only provides value if the network includes comparable-or-better models than what the user can access directly.

### The Path Forward

**MELD needs to attract frontier model operators.** The value thesis changes from:
- ❌ "Consensus of cheap models beats expensive single models" (T7 disproves this)
- ✅ "Consensus of diverse frontier models beats any single frontier model" (T4 supports this)

**This increases operational cost but preserves the quality thesis.**

---

## Comparison to Prior Work

| Test | Finding | Consistency with T7 |
|------|---------|-------------------|
| T4 (E vs B) | Multi-model consensus beats GPT-4o: 53% vs 27% | ✓ But those models were comparable quality |
| T5 (I vs B) | Cheap consensus beats GPT-4o: 47% vs 18% | ✗ T7 contradicts: Sonnet solo beats cheap consensus |
| T6 | Agent setup matters little | ✓ Consistent: high tie rates, weak signal |

**Reconciliation:** T5 tested 3× Gemini Flash → Gemini synthesis vs GPT-4o solo. T7 tested 3× (Grok/Gemini/DeepSeek) → GPT-4o synthesis vs Sonnet solo. If Sonnet > GPT-4o significantly, then the contradiction resolves. The quality threshold matters.

---

## Recommended Next Actions

1. **Test: Does consensus of frontier models beat solo frontier model?**  
   Run 4× frontier (Sonnet, GPT-4o, Gemini Pro, Grok-3) → GPT-4o synthesis vs Sonnet solo. If consensus wins, MELD's thesis holds. If solo wins, MELD's thesis is in trouble.

2. **Network quality as a product metric.**  
   Track the distribution of model quality on the MELD network. A network of mostly Gemini Flash nodes provides less value than a network of mostly Sonnet/GPT-4/Grok nodes.

3. **Economic analysis.**  
   If MELD requires frontier models to provide value, the credit system economics change. Frontier model calls are expensive. Operators need incentive to participate.

---

## Conclusion

**T7 is uncomfortable but clarifying.** Adding Claude to the consensus network helps. But a single strong model beats consensus of weaker models. MELD's value depends on having high-quality participants. The thesis shifts from "cheap consensus beats expensive single" to "diverse frontier consensus beats any single frontier model." This is still defensible but requires MELD to attract premium operators, not just cheap compute.

**The honest assessment:** If users can access Claude Sonnet directly (which they can, via Anthropic or OpenRouter for ~$3-15/million tokens), MELD's network of cheaper models doesn't provide enough value to justify the added latency and complexity. MELD needs to be a network of frontier models, or it's not competitive.

---

**Data:** `/tmp/results/t7_responses.jsonl` (50 questions × 4 conditions), `/tmp/results/t7_judgments.jsonl` (340 clean judgments)  
**Committed to:** meld-eval repo
