# T4: Independence vs Access Test

**The Killer Question:** Is MELD's value from accessing better models (commoditized by OpenRouter) or from independent perspectives (defensible moat)?

## Hypothesis
If multi-agent consensus still wins when all nodes run the *same model* but with different operators/prompts/personas → independence is the value. If it doesn't win → it's just model access.

## Design

### Conditions (100 questions)
- **A (Baseline):** Single Gemini Flash call (baseline - cheapest, fastest)
- **B (Better Model):** Single GPT-4o call (access hypothesis)
- **C (Same Model, Same Prompt):** 3× Gemini Flash with identical system prompts → synthesize
- **D (Same Model, Different Prompts):** 3× Gemini Flash with diverse personas → synthesize
- **E (Different Models):** Grok-3, Gemini Flash, DeepSeek → synthesize (control from T2)

### Personas for Condition D
```json
{
  "analyst": "You are a rigorous analytical thinker. Break problems into components, evaluate evidence systematically, identify assumptions.",
  "creative": "You are a creative lateral thinker. Find unexpected connections, challenge conventional wisdom, explore edge cases.",
  "pragmatic": "You are a pragmatic operator. Focus on what works in practice, prioritize actionable insights, cut through theory."
}
```

### Judging
- 3 judges: GPT-4o, Gemini Flash, Qwen 72B (proven from T2 reanalysis)
- Pairwise comparisons: A vs D, B vs D, C vs D, D vs E
- Win rate metric

## Success Criteria
- **If D > C:** Independence adds value even with same model
- **If D ≈ B:** Independence matches "better model" access
- **If D < B but D > A:** Some value but weaker than just upgrading model
- **If C ≈ A:** Multiple calls to same model with same prompt = waste

## Key Insight
This isolates the independence variable by holding model constant. If D wins, MELD's value isn't "get GPT-4" (OpenRouter does that) — it's "get genuinely diverse perspectives from independent operators."

## Cost Estimate
- 100 questions × 5 conditions × ~500 tokens avg = 250K tokens inference (~$2)
- 100 × 4 comparisons × 3 judges × 1K tokens = 1.2M tokens judging (~$12)
- Total: ~$14

## Timeline
- Questions: Reuse T2 candidates (already screened)
- Collection: ~1 hour (parallel API calls)
- Judging: ~2 hours
- Total: ~3 hours

## Output
- `meld/research/T4_independence/results/responses.jsonl`
- `meld/research/T4_independence/results/judgments.jsonl`
- `meld/research/T4_independence/T4-REPORT.md`
