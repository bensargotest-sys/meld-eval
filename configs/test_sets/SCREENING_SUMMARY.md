# T2 Question Screening Summary

**Date:** 2026-02-22
**Screener:** scripts/deepseek_screen.py (via fast_screen.py, 10 threads)
**Model:** deepseek/deepseek-chat via OpenRouter

## Results

| Metric | Count |
|---|---|
| Total candidates generated | 230 |
| Passed screening | 230 |
| Removed by screening | 0 |

## Removal Reasons Breakdown

None — all 230 candidates passed DeepSeek screening.

## Category Distribution (Final Clean Set)

| Category | Count |
|---|---|
| Reasoning | 58 |
| Factual Knowledge | 57 |
| Creative/Synthesis | 58 |
| Analysis | 57 |

## Screening Criteria

- **Refusal patterns**: 7 known DeepSeek refusal phrases
- **Too short**: responses under 20 words flagged
- **Heavy hedging**: >50% caveat sentences flagged

## Notes

- 0% censorship rate indicates question set avoids sensitive/political topics
- Questions are diverse across 4 categories with balanced distribution
- Ready for human review before T2 execution
- Do NOT run these through MELD nodes until approved
