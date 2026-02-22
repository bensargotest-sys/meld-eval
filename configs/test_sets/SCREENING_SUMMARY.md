# T2 Candidate Question Screening Summary

**Date:** 2026-02-22
**Screener:** scripts/deepseek_screen.py (DeepSeek via OpenRouter)

## Results

| Metric | Count |
|---|---|
| Total candidates generated | 230 |
| Removed by screening | 0 |
| Final clean count | **230** |

## Category Breakdown

| Category | Count |
|---|---|
| Reasoning | 58 |
| Factual Knowledge | 57 |
| Creative/Synthesis | 58 |
| Analysis | 57 |

## Removal Reasons Breakdown

None — all 230 candidates passed DeepSeek screening with no refusal patterns, no heavy hedging, and no truncated responses detected.

## Screening Criteria

- Refusal pattern matching (7 patterns)
- Response length check (min 20 words)
- Heavy hedging detection (>50% caveat sentences)

## Notes

- All questions are safe for multi-model evaluation
- No questions were censored or produced degraded responses from DeepSeek
- Ready for human review before T2 execution
