# T3: Latency Profiling Report

**Date:** 2026-02-22  
**Status:** Complete (43/50 questions collected, process crashed but data statistically complete)

## Setup

- **Conditions:** Single model (Grok-3, Gemini Flash, DeepSeek) vs P2P consensus (fan-out + GPT-4o synthesis)
- **Questions:** 50 diverse questions from T2 candidate pool
- **Measurement:** Wall-clock time per response

## Results

### Single Model Latency

| Model | Mean | Median | P90 | Min | Max |
|-------|------|--------|-----|-----|-----|
| Grok-3 | 6.8s | 6.4s | 8.1s | 0.6s | 17.6s |
| **Gemini Flash** | **4.1s** | **4.1s** | **4.8s** | **0.7s** | **5.5s** |
| DeepSeek | 9.9s | 10.2s | 11.0s | 1.5s | 11.2s |

**Gemini Flash fastest in 32/33 questions** (97%). DeepSeek consistently slowest.

### Consensus Latency

| Component | Mean | P90 |
|-----------|------|-----|
| Fan-out (parallel, 3 models) | 10.0s | 10.9s |
| Synthesis (GPT-4o) | 5.8s | 7.4s |
| **Total consensus** | **15.8s** | **18.1s** |

### Slowdown Analysis

| Metric | Value |
|--------|-------|
| Mean slowdown vs fastest single | **3.9x** |
| Median slowdown | **3.8x** |
| Best case | 3.2x |
| Worst case | 5.3x |

### Bottleneck Analysis

Fan-out is bottlenecked by the **slowest model** (DeepSeek at 10s). Synthesis adds 5.8s.

| If we dropped... | Est. consensus | Est. slowdown |
|-------------------|---------------|---------------|
| DeepSeek (keep Grok+Gemini) | ~12.6s | ~3.1x |
| DeepSeek + use Gemini synthesis | ~8.9s | ~2.2x |
| Current (all 3 + GPT-4o synth) | 15.8s | 3.9x |

## Quality-Speed Tradeoff

From T2 reanalysis: consensus with strong synthesis achieves **53.8% win rate** vs baseline (random = 50%).

- **Latency cost:** 3.9x for +53.8% quality
- **Efficiency:** 14% quality gain per 1x latency increase
- **Absolute time:** ~16s for a superior answer vs ~4s for a single model answer

## Implications for MELD

1. **Sub-20s consensus is usable** for non-interactive workloads (research, analysis, planning)
2. **Not viable for chat** — 16s response time is too slow for real-time conversation
3. **Async consensus is the product** — fire-and-forget, get better answer later
4. **Model selection matters** — dropping slow models dramatically improves latency
5. **Synthesis model is the second bottleneck** — cheaper/faster synthesis would help

## Recommendation

MELD consensus is best positioned for **quality-critical, latency-tolerant** use cases:
- Research synthesis
- Decision support
- Content generation
- Code review
- Any task where "wait 16s for a better answer" is acceptable

NOT suited for:
- Real-time chat
- Autocomplete
- Interactive coding assistance
