# MELD Research Report: Where We Are

**Date:** 2026-02-22  
**Status:** T2 complete, results require rerun with fixes  

---

## 1. What Are We Testing?

**Core question:** Does a network of independent AI models produce measurably better output than a single model alone?

This matters because it's MELD's entire value proposition. If multi-model synthesis doesn't improve quality, there's no reason for agents to trade inference with each other.

---

## 2. What We've Done So Far

### Phase 2 — Exploratory (Feb 2026)
- 10 questions, 4 paths, hand-scored
- **Result: Independent MELD nodes = 72.2% vs local multi-model = 62.6% (+9.7pp)**
- ⚠️ Small sample, not pre-registered, researcher-scored

### T1 — Zero-Sum Ledger (Feb 21) ✅
- 500 transactions, 0 violations
- Credit engine proven correct under sequential, concurrent, and rapid-fire load
- Tag: `v0.1-T1-complete`

### T2 — Anchoring Bias Controlled Experiment (Feb 22) ⚠️
- 200 questions × 5 conditions = 1,000 responses collected (zero errors)
- 4,800 judge calls attempted
- **Result: Baseline wins, but the test has critical flaws (see Section 4)**

---

## 3. T2 Setup & Results

### The 5 Conditions

| Label | Method | How It Works |
|---|---|---|
| **A** | Solo baseline | GPT-4o-mini answers alone |
| **B** | Sequential Giga Brain | Grok-3 → Gemini → DeepSeek (each sees prior), then GPT-4o-mini synthesizes |
| **C** | Anchoring control | 3 models answer in parallel, shuffled + anonymized, GPT-4o-mini synthesizes |
| **D** | Independent parallel | 3 models answer independently, GPT-4o-mini synthesizes |
| **E** | Adversarial chain | Grok-3 answers → Gemini critiques → DeepSeek produces final (no synthesis step) |

### Scores (GPT-4o judge, 200 questions each)

| vs Baseline | Baseline Wins | Condition Wins | Inconsistent | Verdict |
|---|---|---|---|---|
| A vs **B** (Sequential) | 42 | 14 | 139 | Baseline +28 |
| A vs **C** (Anchoring) | 125 | 3 | 70 | Baseline +122 |
| A vs **D** (Independent) | 19 | 13 | 158 | **Near-tie** (Baseline +6) |
| A vs **E** (Adversarial) | 126 | 3 | 71 | Baseline +123 |

### Category Breakdown (GPT-4o judge, D vs A — the closest race)

| Category | A wins | D wins | Inconsistent |
|---|---|---|---|
| Reasoning (53 Qs) | 8 | 1 | 35 |
| Factual (48 Qs) | 5 | 3 | 39 |
| Creative (54 Qs) | 3 | **8** | 43 |
| Analysis (45 Qs) | 3 | 1 | 41 |

**D actually beats A on creative questions** (8 vs 3). The gap is reasoning.

---

## 4. Why These Results Are Inconclusive (Not Definitive)

### 🔴 Problem 1: 2 of 3 judges failed silently

| Judge | Status | Impact |
|---|---|---|
| GPT-4o | ✅ Working | 800 real judgments |
| Mistral Large | ❌ HTTP 400 (every call) | 800 fake "ties" |
| Cohere Command-R+ | ❌ HTTP 404 (every call) | 800 fake "ties" |

**Only 1 of 3 judges actually worked.** The test plan requires 3 independent judges with Fleiss kappa ≥ 0.4. We have 1 judge with no inter-rater reliability measure.

### 🔴 Problem 2: Synthesis bottleneck

The baseline (A) uses **GPT-4o-mini**. Conditions B, C, D also use **GPT-4o-mini** as the synthesis model. So we're testing:

> "Can GPT-4o-mini reading 3 other models' answers beat GPT-4o-mini answering directly?"

This is like testing whether a student writes better essays by reading three textbooks first — using the same student for both conditions. The synthesis model caps the output quality.

**The Phase 2 exploratory test didn't have this problem** because it scored the raw multi-model output, not a synthesis.

### 🟡 Problem 3: High inconsistency

D vs A has **158/200 inconsistent** judgments (79%). This means when the judge sees the same pair in reversed order, it picks a different winner. That's not a meaningful signal — the differences are too subtle for the judge to reliably detect.

### 🟡 Problem 4: Response length bias

| Condition | Avg Response Length |
|---|---|
| A (Solo) | 2,863 chars |
| B (Sequential) | 3,771 chars |
| C (Anchoring) | 3,734 chars |
| D (Independent) | 3,529 chars |
| E (Adversarial) | 3,643 chars |

Multi-model responses are 23-32% longer. The judge prompt says "don't favor length" but GPT-4o may still have implicit length bias, which paradoxically could work *against* the multi-model conditions if the judge interprets length as padding.

---

## 5. What We Actually Learned

Despite the problems, some real signal:

1. **D (Independent parallel) is the most promising approach** — closest to baseline, wins on creative tasks. This aligns with Phase 2 exploratory findings.

2. **C and E are clearly worse** — strong, repeatable signal. Anchoring control and adversarial chains don't help. The anonymization in C may strip useful context. The critique chain in E may introduce errors.

3. **Sequential (B) has moderate overhead** — 3x the model calls for slightly worse results. Not worth it in current form.

4. **The synthesis step is the critical design decision** — it determines whether diverse inputs produce diverse outputs or get flattened.

---

## 6. What To Do Next

### Immediate Fixes (rerun T2 with corrections)

| Fix | What | Why |
|---|---|---|
| **Fix judges** | Replace Mistral/Cohere with working models (e.g., Claude Haiku, Gemini Pro) | Need 3 working judges for inter-rater reliability |
| **Remove synthesis bottleneck** | For condition D: judge each node's raw response against A, OR use a stronger synthesis model (GPT-4o, not mini) | Isolate whether the value comes from diverse models or from synthesis |
| **Add condition F** | "Best of 3" — run 3 independent models, judge picks the best single response (no synthesis) | Tests whether model diversity helps even without combining |

### Design Questions for AB

1. **Should baseline A use GPT-4o (not mini)?** Current test pits mini-synthesizing-3-models against mini-alone. If we use GPT-4o for both baseline and synthesis, we test at a higher quality tier.

2. **Should we test raw node responses?** Instead of synthesizing, just judge each node's individual response against baseline. If Grok-3 alone beats GPT-4o-mini, that tells us something different than "synthesis beats solo."

3. **What's the real use case?** 
   - If MELD is about *access to models you don't have* → test Grok-3 (via MELD) vs GPT-4o-mini (local). That's a different experiment.
   - If MELD is about *synthesis producing emergent quality* → fix the synthesis bottleneck and retest.
   - If MELD is about *both* → we need separate tests for each claim.

---

## 7. Overall MELD Research Status

| Test | Status | Result |
|---|---|---|
| Phase 2 Exploratory | ✅ Done | +9.7pp for independent nodes (promising but small sample) |
| T1 Zero-Sum Ledger | ✅ Passed | 500/500 txns, 0 violations |
| T2 Anchoring Bias | ⚠️ Flawed | Inconclusive — 2/3 judges failed, synthesis bottleneck |
| T3 Latency | 🔲 Not started | |
| T4 Credit Sustainability | 🔲 Not started | |
| T5 HMAC Auth | 🔲 Not started | |

**Bottom line:** The credit engine works (T1). The quality hypothesis is still open — Phase 2 said yes, T2 is inconclusive due to methodology issues. We need a clean rerun.

---

## 8. Files & Commits

| What | Location |
|---|---|
| T2 responses (1,000) | `meld-eval:experiments/P1_mechanism/T2_anchoring_control/results/responses.jsonl` |
| T2 judgments (2,400) | `meld-eval:experiments/P1_mechanism/T2_anchoring_control/results/judgments.jsonl` |
| T2 scores | `meld-eval:experiments/P1_mechanism/T2_anchoring_control/results/scores.json` |
| T2 response commit | `363d5f0` |
| T2 judging commit | `0289bed` |
| Phase 2 scores | `meld/research/phase2/results/scores.json` |
| T1 metrics | `meld/experiments/P1_mechanism/T1_zero_sum/metrics.json` |
| Test plan (v4) | `meld-eval:docs/test_plan.md` |
