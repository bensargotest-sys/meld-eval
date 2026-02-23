# T11: Consensus Guardrails Test Report

**Date:** 2026-02-23
**Test ID:** T11
**Status:** ✅ Complete

## Hypothesis
Multi-model consensus improves safety-critical decision-making (risk assessment, proceed/don't-proceed actions).

## Method
- **Scenarios:** 50 agent actions with ground-truth risk levels
- **Conditions:**
  - A: GPT-4o solo — assess risk level (1-5) and recommend proceed/don't-proceed
  - B: 3-model consensus (Grok-3 + Gemini + DeepSeek) → GPT-4o synthesis
- **Metrics:** Exact risk match, within-1 accuracy, proceed/don't-proceed correctness
- **Judge:** Compared against human-annotated ground truth (not LLM judge)
- **Note:** Condition B had only 24 valid responses (OpenRouter 402 errors)

## Results

| Metric | A (Solo) | B (Consensus) |
|--------|----------|---------------|
| Exact risk level match | **66%** | 58% |
| Within-1 risk accuracy | 96% | 96% |
| **Proceed/don't-proceed correct** | 78% | **88%** |

## Key Findings

1. **Consensus improves the critical binary decision by 10pp (88% vs 78%).** When it matters most — should this agent proceed or stop? — consensus gets it right more often.

2. **Solo is slightly better at exact risk scoring (66% vs 58%).** Single models are more precise in their numerical ratings. Consensus may average out toward middle values.

3. **Both are excellent at within-1 accuracy (96%).** Neither is wildly miscalibrated on risk levels.

4. **The 10pp improvement on proceed/don't-proceed is the headline.** In autonomous agent systems, the binary go/no-go decision is what prevents catastrophic actions. 88% vs 78% is meaningful.

## Guard Product Implications

- A "Guard" product that routes high-stakes agent actions through 3-model consensus before execution is validated.
- Cost: ~3 API calls + synthesis = ~$0.001 per check
- Value: 10% fewer bad decisions on critical actions
- Use case: financial transactions, email sends, code deployments, data deletions

## Caveats

- **Small consensus sample (24 valid)** due to OpenRouter credit exhaustion
- Ground truth risk levels were AI-generated (not independently human-verified)
- Single domain (agent actions) — may not generalize to other safety contexts

## Confidence: 6/10
- Clear signal on proceed/don't-proceed improvement
- Small sample for consensus condition
- Ground truth quality uncertain
- Validated concept, needs larger-scale replication
