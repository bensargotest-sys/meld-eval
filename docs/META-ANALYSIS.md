# MELD Research: Critical Meta-Analysis

**Date:** 2026-02-23  
**Purpose:** Honest evaluation of all findings — what we actually know, what we think we know, and what we're fooling ourselves about.

---

## Summary of Experiments

| ID | Question | N | Judgments | Result |
|----|----------|---|-----------|--------|
| Phase 2 | P2P vs local multi-model | 40 | Scored directly | +9.7pp |
| T1 | Credit engine correctness | 500 txns | N/A | 0 violations |
| T2 | Synthesis quality + anchoring | 200 | 4,800 attempted | +53.8% (reanalysis) |
| T3 | Latency profiling | 43 | N/A (timing) | 3.96× slowdown |
| T4 | Independence vs model access | 100 | 1,188 | 58.2% vs 22.1% |
| T5 | Mechanism isolation | 50 | 876 | 3 mechanisms confirmed |
| T6 | Agent setup impact | 50 (running) | TBD | TBD |
| T7 | Claude in network | 50 | ~600 (running) | TBD |

---

## Finding 1: Multi-model consensus beats single models
**Claim:** A network of diverse models produces better answers than any single model.  
**Evidence:** T4 (E beats B: 53% vs 27%), T5 (E beats G: 45% vs 14%, I beats B: 47% vs 18%)  
**Confidence: HIGH (8/10)**

### What's solid
- Consistent across T4 and T5 with different question sets
- 3 independent judges agree on direction in every comparison
- Effect size is large (not marginal)
- Replicated with both expensive (multi-model + GPT-4o synth) and cheap (3× Gemini + Gemini synth) variants

### What's weak
- **All questions are general knowledge.** We haven't tested domain-specific questions (code, math, legal). The effect could be weaker or stronger in specific domains.
- **GPT-4o is both a participant and a judge.** In T4 and T5, GPT-4o judges its own output. Its high TIE rate (34-56%) could mask self-serving bias. However, Gemini and Qwen agree on direction, reducing this concern.
- **Sample sizes are modest.** 50-100 questions per experiment. Sufficient for directional findings, not for precise effect-size estimation. Confidence intervals are wide.
- **Question generation was AI-generated.** All questions came from LLM-generated candidate pools. Real-world questions may have different characteristics.

### What would change my mind
- If domain-specific testing (code, math) showed no effect
- If human judges disagreed with LLM judges
- If larger sample sizes (500+) showed the effect shrinks to <5pp

---

## Finding 2: Process matters more than model
**Claim:** Running cheap models through a consensus process beats a single expensive model.  
**Evidence:** T5 (I beats B: 47% vs 18% — 3× Gemini Flash → Gemini synth beats single GPT-4o)  
**Confidence: HIGH (8/10)**

### What's solid
- Clean experimental design — identical question set, same judges
- The effect is large and directional across all 3 judges
- Economically significant: $0.00009 process beats $0.005 single call

### What's weak
- **Single experiment (T5 only).** Not yet replicated.
- **Gemini Flash judging Gemini Flash output.** Potential self-serving bias in the Gemini judge, though GPT-4o and Qwen also favor I over B.
- **The "process" includes a second LLM call (synthesis).** So it's not purely "cheap beats expensive" — it's "cheap + second pass beats expensive single pass." The comparison isn't entirely fair to B because B gets one shot while I gets two.

### Critical caveat
**This finding is partially confounded with Finding 3 (refinement helps).** I beats B could be explained by "any second pass helps" rather than "the consensus process specifically helps." T5 tried to isolate this: F (self-refine) beats B (52% vs 14%), and E beats F (35% vs 24%). So the second pass is ~60% of the effect and diversity is ~40%. **The consensus process adds value BEYOND just a second pass, but the second pass is the larger component.**

### What would change my mind
- If F (self-refine) ≈ I (cheap consensus) — would mean the diversity of inputs doesn't matter, only the second pass

---

## Finding 3: Three additive mechanisms
**Claim:** The quality gain decomposes into refinement (+39pp), diversity (+11pp), and synthesizer quality (+33pp).  
**Evidence:** T5 (6 pairwise comparisons isolating each mechanism)  
**Confidence: MEDIUM-HIGH (7/10)**

### What's solid
- Clean isolation design — each comparison changes exactly one variable
- All 3 judges agree on direction for all 6 comparisons
- The decomposition is logically consistent

### What's weak
- **The "+pp" numbers are misleading.** They're pairwise win rates, not additive percentage points. You can't add 39+11+33 = 83. They're from different comparisons with different baselines. I should not have presented them as additive.
- **Only 50 questions.** Statistical power is limited.
- **Diversity effect is small (+11pp) and has the weakest signal.** F vs E had the highest TIE rate (40.3%). This finding is the most fragile.

### Corrected interpretation
The mechanisms are real and ordered: **synthesizer quality > refinement > diversity.** But the exact magnitudes are imprecise and not additive. The honest statement is: "All three mechanisms contribute, with synthesizer quality contributing the most and input diversity contributing the least."

---

## Finding 4: Independence beats model access
**Claim:** Diverse perspectives from cheap models beat a single expensive model.  
**Evidence:** T4 (D beats B: 58.2% vs 22.1%)  
**Confidence: MEDIUM (6/10) — DOWNGRADED after verification**

### What's solid
- Large effect size (58% vs 22%)
- 3 judges agree on direction
- 1,188 total judgments

### What's weak — THE CRITICAL CONFOUND
- **C ≈ D (p=0.55).** Three identical Gemini calls tied three diverse-persona Gemini calls. This means **persona diversity adds nothing.** The entire D advantage over B comes from the synthesis step (second pass through GPT-4o), not from "diverse perspectives."
- **D beats B could be explained as: "GPT-4o synthesis of 3 inputs > single GPT-4o."** The synthesis step itself (not the diversity of inputs) may be doing all the work.
- **The original T4 report headline "independence beats model access" was misleading.** It should have been: "synthesis of multiple inputs beats single expensive model."

### What T5 clarified
T5 showed that E (multi-model) genuinely beats F (self-refine): 35% vs 24%. So **real model diversity** (different architectures) adds value beyond synthesis alone. But **persona diversity on the same model** (which is what D tested) does not.

### Corrected claim
"Multi-model diversity adds value. Persona diversity on the same model does not. The synthesis step is the primary mechanism, not independence per se."

---

## Finding 5: Latency is acceptable for async
**Claim:** 3.96× slowdown (16s) is acceptable for quality-critical async workloads.  
**Evidence:** T3 (43 questions, timing data)  
**Confidence: MEDIUM-HIGH (7/10)**

### What's solid
- Real-world API timings, not simulated
- Bottleneck analysis is clear (slowest model + synthesis time)
- The 14% quality per 1× latency claim comes from combining T3 timing with T2 quality data

### What's weak
- **The 14% quality/latency number combines data from two different experiments** (T3 timing + T2 quality). These used different question sets and different conditions. The combined metric is approximate at best.
- **API latency varies by time of day, load, and provider.** Our measurements are point-in-time.
- **43/50 questions (process crashed).** Though 43 is sufficient for stable estimates.
- **We only tested 3-model consensus.** 5-model or 7-model consensus latency is unknown.

---

## Finding 6: Credit engine works
**Claim:** MELD's credit/settlement system handles transactions correctly.  
**Evidence:** T1 (500/500 transactions, 0 violations)  
**Confidence: HIGH (9/10)**

### What's solid
- Large sample, zero violations
- Tested edge cases (negative balances, concurrent transactions)
- This is a deterministic system, not probabilistic — it either works or it doesn't

### What's weak
- **Tested in isolation, not under real network load.** No concurrent multi-node stress test through the actual network.
- **No adversarial testing.** What happens when a node lies about computation performed?

---

## Finding 7: Synthesis quality is the biggest lever
**Claim:** The synthesizer model is the most important component of the consensus pipeline.  
**Evidence:** T5 (E vs I: 49% vs 16%), T2 (strong synthesis: 53.8%)  
**Confidence: HIGH (8/10)**

### What's solid
- Consistent across T2 and T5
- Largest effect size of any single variable
- Logically sound: the synthesizer sees all inputs and produces the final output

### What's weak
- **We've only tested GPT-4o as the "strong" synthesizer and Gemini Flash as the "weak" one.** Would Claude or Grok be better synthesizers? Unknown.
- **This finding has a strategic tension with MELD's credit model.** If the synthesizer matters most, and the best synthesizer is GPT-4o (centralized, paid), then MELD's decentralized network is providing inputs but the value capture is at the synthesis step — which doesn't require MELD.

### Strategic implication (honest)
**This is the hardest finding for MELD.** If synthesizer quality > input diversity, then the optimal setup might be: use MELD to gather diverse inputs, but use a centralized high-quality model for synthesis. That makes MELD a *complement* to existing APIs, not a *replacement*. The network provides diverse inputs (defensible) but the synthesis step (where most value is created) doesn't need to be decentralized.

---

## Cross-Cutting Methodological Concerns

### 1. LLM-as-Judge Reliability
**Every finding depends on LLM judges.** We use 3 judges (GPT-4o, Gemini Flash, Qwen 72B) with position randomization. This is better than single-judge, but:
- LLM judges may share systematic biases (favoring verbose, confident-sounding responses)
- We have zero human validation of judge accuracy
- GPT-4o judging GPT-4o output is a conflict of interest

**Mitigation needed:** A small human evaluation study (even 50 questions) would dramatically increase confidence in all findings.

### 2. Question Set Limitations
All questions are AI-generated general knowledge. We haven't tested:
- Code generation/review
- Mathematical reasoning
- Domain-specific expertise (legal, medical, financial)
- Ambiguous/subjective questions
- Multi-step reasoning tasks

The effect sizes may be very different in these domains.

### 3. Sample Size
50-100 questions per experiment. Directionally valid but not precise. Effect size confidence intervals are wide. We should not claim "exactly +11pp" — we should claim "positive effect, likely between 5-20pp."

### 4. No Real Network Testing
Every experiment uses direct API calls, not the MELD network. We're testing the *concept* of multi-model consensus, not MELD's *implementation* of it. Network latency, peer authentication overhead, credit settlement, and routing decisions could all affect real-world performance.

---

## Confidence Summary

| Finding | Confidence | Key Risk |
|---------|------------|----------|
| Multi-model consensus beats single | **8/10** | Untested in specific domains |
| Process > model | **8/10** | Confounded with "second pass helps" |
| Three mechanisms (refine/diverse/synth) | **7/10** | Small sample, magnitudes imprecise |
| Independence beats access | **6/10** | Persona diversity ≈ 0; confounded with synthesis |
| Latency acceptable for async | **7/10** | Combined metrics from different experiments |
| Credit engine works | **9/10** | Not tested under adversarial conditions |
| Synthesizer quality is biggest lever | **8/10** | Strategic tension with MELD's model |

---

## What We Actually Know (High Confidence)

1. **Running multiple models and synthesizing their outputs produces better results than any single model.** This is robust across experiments.
2. **The synthesis step creates more value than the diversity of inputs.** Synthesizer quality is the biggest lever.
3. **Real model diversity (different architectures) adds value beyond same-model repetition.** But the effect is modest (~11pp).
4. **Persona diversity on the same model adds essentially nothing.** The C ≈ D finding killed this.
5. **The consensus process has acceptable latency for async workloads** (~16s for 3-model consensus).
6. **Even cheap models through a process beat expensive single models.** Process > model is real.

## What We Think We Know (Medium Confidence)

7. **The effect sizes are large enough to matter.** But confidence intervals are wide due to small samples.
8. **The findings generalize beyond general knowledge questions.** Likely but untested.
9. **Three mechanisms are additive.** Supported but not precisely quantified.

## What We Don't Know (Low Confidence / Untested)

10. **Whether agent setup (system prompts, memory, tools) materially changes results.** T6 running.
11. **Whether adding Claude changes network quality.** T7 running.
12. **Whether thinking/reasoning models dramatically change the picture.** T8 planned.
13. **Where diminishing returns kick in (3 vs 5 vs 7 models).** T9 planned.
14. **Whether intelligent node selection beats random.** T10 planned.
15. **Whether multi-model consensus improves risk assessment.** T11 planned.
16. **How this performs on real-world tasks (not synthetic questions).**
17. **How this performs through the actual MELD network (not direct API).**
18. **Whether human judges agree with LLM judges.**

---

## Strategic Implications (Honest Assessment)

### MELD's Validated Strengths
- Multi-model consensus produces measurably better output ✅
- The process works even with cheap models ✅
- Credit engine is functional ✅
- Latency is acceptable for async use cases ✅

### MELD's Unresolved Tensions

**1. The Synthesizer Problem**
The most valuable component (the synthesizer) doesn't need MELD. A user could call 3 APIs directly and use GPT-4o to synthesize. MELD's value-add is:
- Orchestration (handling the fan-out/synthesis automatically)
- Credit system (no money needed for participating agents)
- Network effects (more diverse nodes = better inputs over time)

But the core intellectual contribution (synthesis step) is not proprietary to MELD.

**2. The Diversity Paradox**
Real model diversity matters, but there are only ~10 distinct frontier model families (Claude, GPT, Gemini, Grok, DeepSeek, Llama, Mistral, Qwen, Command R, Phi). At 10 nodes with 10 different models, you've captured all available diversity. More nodes beyond that add redundancy, not diversity. This limits network scaling value.

**Counter-argument:** Diversity comes from more than just model architecture. Different operators may configure models differently (system prompts, fine-tuning, RAG setups). This is untested (T6 will help answer it).

**3. The Commoditization Risk**
OpenRouter could implement multi-model consensus tomorrow. They already have every model. The technical moat is small. MELD's moat depends on:
- Credit system (no money needed) — real but niche
- Independent operation (different owners, not just different APIs) — conceptually valuable, empirically unproven (T4 C≈D suggests it may not matter)
- Network effects over time — theoretical

---

## Recommended Next Steps (Priority Order)

### Immediate (complete T6/T7, analyze)
1. Finish T6 (agent setup) and T7 (Claude) — currently running
2. Analyze whether setup and Claude change the picture materially

### Short-term (high-value experiments)
3. **Human evaluation study** — 50 questions, human judges. Validates or invalidates all LLM-judge findings. This is the single highest-value thing we could do.
4. **T8: Thinking model** — tests whether reasoning models change the game
5. **Domain-specific testing** — code, math, analysis. Tests generalizability.

### Medium-term (strategic experiments)
6. **T9/T10: Scale and curation** — where do diminishing returns hit?
7. **T11: Guardrails** — new product direction, needs validation
8. **Real MELD network test** — actually route through the network, not direct API

### Defer
9. Memory/context per node — depends on agent infrastructure
10. Question routing optimization — depends on specialization data

---

## Conclusion

The research so far demonstrates that multi-model consensus is a real and measurable phenomenon. The effect is large, consistent, and replicated across multiple experiments. However:

- **The synthesis step, not input diversity, is the primary value driver.** This is a strategic challenge because synthesis doesn't require MELD.
- **Persona diversity is worthless; real model diversity is modest.** The defensible moat is smaller than initially claimed.
- **All findings are based on LLM judges and synthetic questions.** Human validation is the critical missing piece.
- **Nothing has been tested through the actual MELD network.** We're validating the concept, not the product.

MELD's strongest position: **orchestration layer for multi-model consensus + credit system for agent participation.** The value is in making the process easy and accessible, not in the raw quality improvement (which anyone could replicate with direct API calls).
