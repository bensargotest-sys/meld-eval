# MELD Pre-Registration Document

**Status: LOCKED — committed before any test data collected**  
**Version: v3.0**  
**Date: 2026-02-21**  
**Tag: v0.0-pre-registration-v3**

This document freezes all hypotheses, metrics, and pass/fail thresholds before any experiment runs. Per the "garden of forking paths" principle (Gelman & Loken, 2013), any analysis not listed here is exploratory and must be labeled as such. Modifying hypotheses after seeing data is p-hacking. If a hypothesis must change post-registration, document the change with full justification and register it as a new hypothesis with a new version tag.

---

## Primary Hypotheses

**H1 — Giga Brain Quality**  
Three-model sequential consensus produces outputs rated higher than the best single-model output on ≥60% of 200 test questions by an independent LLM judge panel, after controlling for anchoring bias via response anonymisation. Lower bound of 95% bootstrap CI must be >50%.

Falsification criterion: lower bound of 95% CI ≤50%, or consensus preferred on <50% of questions.

**H2 — Anchoring Independence**  
In the anonymised sequential condition, the correction ratio (incorrect single → correct consensus) exceeds the subversion ratio (correct single → incorrect consensus) by factor ≥1.5. Semantic similarity between sequential responses <0.85 on ≥30% of questions.

Falsification criterion: correction/subversion ratio <1.5, OR semantic similarity ≥0.85 on >70% of questions (groupthink).

**H3 — Credit Zero-Sum**  
Sum of all node balances equals exactly zero after every transaction, for 100% of ledger entries across a 500-transaction stress test including 150 concurrent writes. Zero exceptions permitted.

Falsification criterion: any single violation of balance_sum ≠ 0 after a transaction.

**H4 — Latency Viability**  
End-to-end Giga Brain consensus completes in ≤15 seconds for 95th percentile of requests, after subtracting OpenRouter baseline overhead. Individual node-to-node requests ≤3 seconds at p95 under idle conditions.

Falsification criterion: p95 latency >15 seconds (adjusted), OR p95 single-node >3 seconds.

**H5 — Credit Sustainability**  
Under simulated 10-node load with heterogeneous personas including a strategic defaulter scenario, no node hits credit limit within first 1,000 transactions. Network Gini coefficient <0.6 and velocity >3.0 throughout. Sybil scenario detected and penalised within 100 transactions.

Falsification criterion: any node hits limit before tx 1000, OR Gini ≥0.6, OR Sybil undetected after 100 tx.

**H6 — Private Model Access**  
A fine-tuned Ollama model served via MELD produces domain-specific outputs categorically unavailable via any public API, verified by domain expert evaluation on 30 test queries.

Falsification criterion: public model achieves equivalent domain-specific performance, OR expert cannot distinguish MELD-served from public model output.

---

## Statistical Framework

**Sample size:** n=200 questions minimum (power analysis: 83% power at alpha=0.05, 10pp effect, Holm-Bonferroni corrected for 6 hypotheses). n=100 rejected — gives only 65% power.

**Multiple comparison correction:** Holm-Bonferroni across 6 hypotheses. Sort p-values p(1)≤...≤p(6). Reject H(i) if p(i) ≤ alpha/(6-i+1). Stop at first non-rejection.

**Confidence intervals:** 95% bootstrap CI, 10,000 resamples. Distribution-free. Paired bootstrap for within-subject comparisons.

**Reporting format:** "[Metric] on X% of questions (95% CI: Y%-Z%), n=200, Holm-Bonferroni corrected p=W."

---

## Pre-Test Requirements (must complete before H1-H6 testing)

**DeepSeek censorship screening:** All candidate questions must be run through DeepSeek alone before the question set is locked. Flag and remove responses that refuse, heavily hedge (>50% caveats), or return <20 words on questions expecting 200+. Budget 220-240 candidates to yield 200 clean questions. Document removal count.

**Negative controls:** Include 5 obviously-wrong responses (factual errors, logical contradictions) in T2 and T6. Judge panel must rate these as worst option in ≥95% of cases. If <95%, pause and investigate evaluation system calibration before proceeding.

**OpenRouter baseline:** Before T3 latency testing, measure OpenRouter round-trip overhead with 50 minimal test requests (1-token prompt, 1-token max output). Subtract mean overhead from all OpenRouter-routed measurements.

---

## Conditions (T2 and T6)

- **A — Independent:** Each model answers without prior context. Baseline.
- **B — Sequential-identified:** Models see prior responses with model labels.
- **C — Sequential-anonymised:** Models see prior responses, labels removed. (Primary condition for H1/H2.)
- **D — Self-consistency:** Best single model generates 3 responses, majority vote.
- **E — Sequential-adversarial:** Models must explicitly identify weaknesses in prior response before building on it.

---

## Judge Panel Rules

- 3 judge models from families NOT represented in the MELD network
- If MELD nodes use Grok, Gemini, Claude, Llama, DeepSeek — judges must be from different families (e.g. GPT-4o, Mistral, Command R)
- Position-swap protocol: every comparison evaluated in both orderings. ≥70% consistency required.
- Verbosity control: judge prompt must explicitly state "do not score response length as quality."
- Quality-per-word computed alongside absolute score.
- Inter-judge agreement: Fleiss kappa ≥0.4 required. If kappa <0.4, results are inconclusive.

---

## Tiered Claims

Results are only reported at the tier matching the evidence:

- **Tier 1 — Proven:** Internal controlled test, pre-registered, data published
- **Tier 2 — Demonstrated:** Internal test, not externally validated
- **Tier 3 — Hypothesised:** Not yet tested, or requires Phase 3

No claim crosses tiers without evidence. Negative findings are reported with equal prominence to positive findings.

---

## What This Document Does Not Cover

Analysis not listed above is exploratory. Label it clearly. It does not support Tier 1 or Tier 2 claims.
