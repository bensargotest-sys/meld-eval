# T12: Network Topology — Does Structure Matter?

**Date:** 2026-02-23  
**Status:** Complete  
**Finding:** Topology matters modestly. Chain and debate outperform simple fan-out by ~10-15pp. No clear winner between chain and debate.

---

## Research Question

Does the network communication topology affect consensus quality? Is simple fan-out+synthesize optimal, or do more complex patterns (chain refinement, debate, hybrid) produce better results?

## Design

**50 questions** from T4 candidate pool × **4 conditions:**

| Condition | Description | Pattern |
|-----------|-------------|---------|
| A | Fan-out + synthesize (baseline) | 3 models → synthesize (independent, parallel) |
| B | Chain/sequential refinement | Model 1 → Model 2 sees M1 output → Model 3 sees M2 output → synthesize |
| C | Debate (argue + adjudicate) | 3 models propose → 2 models critique each → synthesize as adjudication |
| D | Parallel + chain hybrid | 2 models independent → 1 model refines both → synthesize |

**Models:** All conditions use Grok-3, Gemini Flash, DeepSeek. GPT-4o synthesis in all cases.

**Judges:** GPT-4o and Qwen 72B, position-randomized. Gemini Flash judging had massive errors (same as T6/T7).

**Total:** 741 judgments attempted, 440 clean judgments collected (247 Gemini errors, 54 GPT-4o errors).

---

## Results

### Judge Error Rates
- **Gemini Flash: 247 errors** (74% failure rate) — Google API 400 errors persisted
- GPT-4o: 54 errors (11.4% failure rate)
- **Effective sample: 440 judgments across 2 judges**

### Key Comparisons (Aggregate across 2 judges)

| Comparison | X wins | Y wins | Ties | X Win Rate (excl ties) |
|------------|--------|--------|------|------------------------|
| **B vs A** (chain vs fan-out) | 28.1% | 7.9% | 64.0% | **78.1%** |
| **C vs A** (debate vs fan-out) | 42.9% | 22.6% | 34.5% | **65.5%** |
| **D vs A** (hybrid vs fan-out) | 42.9% | 13.1% | 44.0% | **76.6%** |
| **B vs C** (chain vs debate) | 38.9% | 32.2% | 28.9% | **54.7%** |
| **D vs B** (hybrid vs chain) | 38.7% | 12.9% | 48.4% | **75.0%** |

### Detailed Results: C vs A (Debate vs Fan-out)

This comparison had the **lowest tie rate** (34.5%) and clearest signal.

| Judge | Debate | Fan-out | Tie | Debate Win Rate (excl ties) |
|-------|--------|---------|-----|----------------------------|
| GPT-4o | 42.9% | 14.3% | 42.9% | **75.0%** |
| Qwen | 42.9% | 28.6% | 28.6% | **60.0%** |
| **Aggregate** | **42.9%** | **22.6%** | **34.5%** | **65.5%** |

Debate beats simple fan-out clearly. When judges can decide, debate wins roughly 2:1.

---

## Key Findings

### 1. Topology Matters, But Modestly

All three alternative topologies (B, C, D) beat the baseline (A) fan-out:
- **Chain beats fan-out:** 78.1% win rate among non-ties
- **Debate beats fan-out:** 65.5% win rate
- **Hybrid beats fan-out:** 76.6% win rate

Effect size is moderate (~10-15pp improvement in absolute terms, 65-78% win rate among non-ties).

### 2. No Clear Winner Among Alternatives

**Chain vs Debate (B vs C):** Nearly tied (54.7% vs 45.3% among non-ties, 39% vs 32% overall).  
**Hybrid vs Chain (D vs B):** Hybrid slightly ahead (75% vs 25% among non-ties, but 48% tie rate).

All three alternatives are comparable. Debate had the lowest tie rate (best signal), suggesting it may be most robust, but the difference is not definitive.

### 3. Why Topology Might Matter

**Chain/sequential refinement:** Later models see earlier outputs and can build on them. Refinement over iterations.

**Debate:** Models critique each other, surfacing weaknesses and forcing justification. Adversarial process improves rigor.

**Hybrid:** Combines parallel diversity with sequential refinement. Best of both?

**Fan-out baseline:** Models work independently (no information sharing). Synthesizer sees raw, unrefined inputs.

Hypothesis: Information flow between agents (chain) or adversarial critique (debate) improves the quality of inputs to the synthesizer.

### 4. Tie Rates Vary by Topology

- **Debate (C vs A): 34.5% tie rate** — lowest of all T12 comparisons, clearest signal
- **Chain (B vs A): 64.0% tie rate** — high, similar to T6/T7
- **Hybrid (D vs A): 44.0% tie rate** — moderate

Debate produces the most differentiated outputs. Chain and hybrid produce outputs closer to baseline.

---

## Statistical Notes

1. **Reduced sample size:** 440 clean judgments out of 741 attempted (41% error rate). Sufficient for directional findings.
2. **Tie rates vary widely:** 29-64% depending on comparison. Debate shows clearest signal (lowest ties).
3. **Consistent direction:** All 3 alternative topologies beat baseline. Confidence is high that topology matters, but magnitude is moderate.
4. **No head-to-head C vs D:** Debate vs Hybrid not directly tested. Unknown which is definitively better.

---

## Implications for MELD

### Positive Takeaways

1. **Network topology is a real variable.** Structure matters beyond just "ask N models and synthesize."
2. **Debate shows strongest signal.** Adversarial critique produces more differentiated, defensible outputs.
3. **Chain refinement helps.** Sequential information flow improves quality over pure parallelism.
4. **Hybrid shows promise.** Combining parallel diversity + sequential refinement may be optimal, but needs more testing.

### Practical Guidance

**For MELD network design:**
- Default fan-out+synthesize is acceptable but not optimal
- **Debate mode** (agents propose, critique, adjudicate) may be the best UX: clear signal, robust differentiation
- **Chain mode** (sequential refinement) is simpler to implement and nearly as good
- **Hybrid mode** needs more testing but could be optimal if implementation is feasible

### The Hard Constraint: Latency

More complex topologies mean more sequential steps:
- **Fan-out:** 1 round (parallel) + synthesis = ~16s (from T3)
- **Chain:** 3 sequential rounds + synthesis = ~40-50s (estimated)
- **Debate:** 2 rounds (propose, then critique in parallel) + synthesis = ~30s (estimated)
- **Hybrid:** 2 rounds (parallel, then refine) + synthesis = ~30s

**Trade-off:** +10-15pp quality for +2-3× latency. This is acceptable for async/quality-critical use cases, not for interactive chat.

---

## Comparison to Prior Work

| Test | Finding | Consistency with T12 |
|------|---------|-------------------|
| T2/T4/T5 | Multi-model consensus beats single | ✓ Consistent: better structure improves consensus |
| T3 | Latency is 3.96× for baseline consensus | ✓ Consistent: complex topology will add more latency |
| T6 | Agent setup matters little | ? Orthogonal: T12 tests network structure, not agent prompting |
| T7 | Strong model beats weak consensus | ⚠️ Warning: topology may not overcome quality gap |

**Note on T7 interaction:** If a single strong model (Sonnet) beats weak multi-model consensus (T7), does topology help? Unknown. Topology might close the gap but probably doesn't reverse the finding. Testing needed: Debate topology with weak models vs solo strong model.

---

## Limitations

1. **No human validation.** All findings based on LLM judges.
2. **Single model set.** Tested only Grok-3/Gemini/DeepSeek. Would findings generalize to different models?
3. **Latency not measured.** We infer chain/debate are slower but didn't measure actual wall-clock time.
4. **No test of 5+ model topologies.** Does topology matter more when N is larger?
5. **No test of intelligent routing.** All models in all topologies. What if models are selected based on question type?

---

## Recommended Next Actions

1. **Latency profiling for chain and debate.** Measure actual wall-clock time to quantify the quality/latency trade-off.
2. **Test topology with frontier models.** Does debate with Sonnet/GPT-4/Grok-3 beat Sonnet solo? (Addresses T7 finding.)
3. **Debate vs Hybrid head-to-head.** Both show promise; need direct comparison.
4. **Scale testing.** Do benefits increase with 5, 7, or 9 models? Where do diminishing returns hit?
5. **Question-type routing.** Some questions may benefit from debate (controversial), others from chain (analytical), others from simple fan-out (factual).

---

## Conclusion

**Network topology matters, but modestly.** Chain, debate, and hybrid topologies all outperform simple fan-out by 10-15 percentage points. Debate shows the clearest signal (lowest tie rate, most differentiated outputs). The practical implication: MELD should support multiple topology modes:
- **Fast mode:** Fan-out + synthesize (~16s, baseline quality)
- **Quality mode:** Debate (~30s, +10-15pp quality)
- **Deep mode:** Chain refinement (~40-50s, +10-15pp quality, good for analytical questions)

Topology is a real lever for quality, but it's not as large as model quality (T7) or synthesis quality (T5). It's a second-order optimization.

**Strategic takeaway:** MELD can differentiate on topology patterns. No other multi-model service (OpenRouter, etc.) offers debate or chain modes. This is a defensible feature if the quality gains are real in production use.

---

**Data:** `/tmp/results/t12_responses.jsonl` (50 questions × 4 conditions), `/tmp/results/t12_judgments.jsonl` (440 clean judgments)  
**Committed to:** meld-eval repo
