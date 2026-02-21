# MELD Systematic Test Plan

**Version: 3.0**  
**Updated: 2026-02-21**  
**Pre-registration tag: v0.0-pre-registration-v3**

See `pre_registration.md` for frozen hypotheses and statistical framework.

---

## Phase 1 — Mechanism Validation (Internal)

All Phase 1 tests must pass before Phase 2 begins. Results are Tier 1 (Proven under controlled conditions) with caveat: single-operator validation.

**Prerequisite:** SQLite branch deployed to all nodes, auto-discovery live.

### T1 — Zero-sum ledger integrity

500 transactions: 200 sequential, 150 concurrent (50 triplets at 3s overlap), 150 rapid-fire (10/second). Run before and after infrastructure migration — both must pass. Any violation: stop all tests, alert human, restore backup.

Pass: sum(all_balances) == 0 after every transaction, 0 exceptions.

Data format:
```json
{"test":"T1","tx_id":1,"timestamp":"...","sum":0,"balances":{"meld-2":150,"meld-3":-80,"meld-4":-70},"pass":true}
```

### T2 — Anchoring bias controlled experiment

200 questions, 5 conditions (A-E), negative control (5 obviously-wrong responses). Requires human approval of question set before running.

Metrics: correction ratio, subversion ratio, semantic similarity, quality-per-word, negative control calibration.

### T3 — Latency profiling

Measure OpenRouter baseline first (50 samples). Then: single-node direct API (p95 ≤3s), single-node via OpenRouter (p95 ≤3s + overhead), full Giga Brain (p95 ≤15s adjusted). Three load conditions: idle, 3 concurrent, 10 concurrent.

### T4 — Credit sustainability

Base: 10 nodes, heterogeneous personas, 1000 tx, track Gini and velocity.  
Strategic defaulter: node consumes to limit, goes offline <10min, rejoins. Must be detected within 3 cycles.  
Sybil: 1 operator, 5 agents, asymmetric flow. Document whether detected or note as known limitation.

### T5 — HMAC authentication

100 attack attempts: missing HMAC, invalid signatures, tampered payload, replay attacks. Pass: 0% acceptance.

---

## Phase 2 — Value Validation (Shareable)

Results are Tier 2 (Demonstrated internally). All Phase 2 results presented with explicit caveat: single-operator, not externally validated.

### T6 — Giga Brain quality benchmark

Primary investor-facing test. 200 questions (post-DeepSeek screening), 5 conditions, 3 independent judge models, position-swap, verbosity normalisation, negative controls, Fleiss kappa ≥0.4.

Pass: ≥60% win rate, lower bound of 95% CI >50%, Holm-Bonferroni corrected.

### T7 — Private model access

30 domain-specific queries, fine-tuned Ollama model via MELD vs public APIs. Domain expert evaluation. Pass: ≥25/30 queries where MELD-served model produces categorically different output.

### T8 — Context window lending

20 long-document questions (>50K tokens). Pass: large-context node references final 25% of document on ≥16/20 questions; small-context model fails on ≥16/20.

### T9 — Fleet capacity pooling

5x load spike. Pass: MELD routing p95 <120% of baseline; saturated single node >300% of baseline.

---

## Phase 3 — Emergent Intelligence (External Operators Required)

Cannot begin without ≥3 nodes controlled by genuinely independent operators. Results are Tier 1 — the highest claim level.

T10: External operator consensus quality  
T11: Network growth effects (5+ nodes, diverse models)  
T12: Adversarial resilience (1 adversarial node in 5+)  
T13: Long-term sustainability (≥3 months multi-operator data)

---

## Git Convention

| Tag | When |
|---|---|
| v0.0-pre-registration-v3 | Before any test data collected — THIS COMMIT |
| v0.1-T1-complete | After T1 passes |
| v0.2-T2-complete | After T2 results |
| v0.3-P1-complete | After human review of all Phase 1 |
| v0.4-P2-complete | After T6-T9 |
| v1.0-external-validation | After first Phase 3 external operator test |

Commit convention: `exp-TN-pre: freeze config` before execution, `exp-TN-results: [one-line finding]` after.

---

## Known Limitations (Disclose Proactively)

- Single operator controls all nodes — cannot distinguish network effects from operator-controlled behaviour until Phase 3
- Researcher-selected questions — may not generalise to diverse real-world queries
- DeepSeek censorship removes a class of questions — document count and list in appendix
- OpenRouter version instability — log exact model checkpoint for each test run
- LLM-as-judge may have systematic style biases — human expert validation in Phase 3
- Sequential order effects — anonymisation controls identity sycophancy but not positional bias
- Credit sustainability is simulated — real economic incentives not present until Phase 3
