# Session 2026-02-23: MELD Research — T5 Complete + Variable Mapping

**Date:** 2026-02-23 09:30–11:30 UTC  
**Participants:** AB, OpenClaw Agent (Claude Opus 4.6)

---

## T5 Mechanism Isolation — Results

T5 completed: 50 questions × 6 conditions, 876 pairwise judgments, 3 judges (GPT-4o, Gemini Flash, Qwen 72B).

### Conditions
- B: GPT-4o single (control)
- E: 3 models (Grok-3 + Gemini + DeepSeek) → GPT-4o synthesis
- F: GPT-4o → GPT-4o self-refine (two-pass same model)
- G: Grok-3 single
- H: 3 models → GPT-4o picks best (selection, no synthesis)
- I: 3× Gemini → Gemini synthesis (cheap everything)

### Results
| Comparison | Winner | Win% | Loser% | TIE% |
|-----------|--------|------|--------|------|
| F vs B | F (self-refine) | 52.4% | 13.6% | 34.0% |
| F vs E | E (multi-synth) | 35.4% | 24.3% | 40.3% |
| G vs E | E (multi-synth) | 45.2% | 13.7% | 41.1% |
| H vs B | H (best-of-3) | 41.2% | 18.2% | 40.5% |
| I vs B | I (cheap-synth) | 46.7% | 18.2% | 35.0% |
| I vs E | E (multi-synth) | 49.3% | 16.2% | 34.6% |

### Three Additive Mechanisms Isolated
1. **Refinement** (second pass): ~39pp gain
2. **Input diversity** (different model architectures): ~11pp additional
3. **Synthesizer quality** (strong vs weak synthesizer): ~33pp additional

### Key Finding
3× cheap Gemini Flash with synthesis beats single GPT-4o (47% vs 18%). **Process > model.**

---

## T4 Verification — Correction Applied

During T4 deep verification, a critical confound was found:
- C (3× identical) ≈ D (3× diverse personas): p=0.55 NS
- **Persona diversity alone doesn't help** — it's the synthesis step that creates value
- E >> D still holds: multi-model consensus beats same-model consensus
- T5 confirmed and explained this: the three mechanisms are refinement, diversity, and synthesizer quality

---

## Strategic Discussion: Productization & Untested Variables

### Product Packaging Concept (Agent's Proposal)

| Product | What it does | Nodes | Latency | Credits |
|---------|-------------|-------|---------|---------|
| Flash | Best single model from network | 1 (curated) | ~4s | 1 |
| Circuit | 3-model consensus, fast synthesis | 3 fast | ~16s | 5 |
| Giga Brain | 5+ models, thinking models, strong synthesis | 5+ incl. reasoning | ~60s | 20 |
| Specialist | Domain-routed (code, math, creative) | 3 specialized | ~20s | 8 |

Node operators don't need to know which product they're serving. They serve inference, earn credits. MELD's coordination layer handles packaging.

### AB's Key Insight: We're Testing Models, Not Agents

Current MELD nodes are bare inference passthrough:

| Node | Model | System Prompt | Memory | Tools | Agent Setup |
|------|-------|--------------|--------|-------|-------------|
| meld-2 | Grok-3 | ❌ | ❌ | ❌ | Bare API |
| meld-3 | Gemini Flash | ❌ | ❌ | ❌ | Bare API |
| meld-4 | DeepSeek V3 | ❌ | ❌ | ❌ | Bare API |
| meld-5 | Llama 3.2 3B | ❌ | ❌ | ❌ | Bare API |

vs. the orchestrating agent:

| Component | Status |
|-----------|--------|
| Claude Opus 4.6 | ✅ |
| SOUL.md, USER.md | ✅ |
| 6-layer memory system | ✅ |
| Full toolkit | ✅ |
| 3-tier architecture (orchestrator → worker → sub-agents) | ✅ |

**Every test so far measured model-vs-model, not agent-vs-agent.** The agent setup (system prompts, personality, memory, tools) is a massive untested variable.

### Models Tested vs Not Tested

| Model | In Network? | In Tests? | Notes |
|-------|-------------|-----------|-------|
| Gemini Flash | ✅ meld-3 | ✅ T2-T5 | Cheap baseline |
| Grok-3 | ✅ meld-2 | ✅ T3-T5 | Strong single |
| DeepSeek V3 | ✅ meld-4 | ✅ T3-T5 | Mid-tier |
| GPT-4o | ❌ direct API | ✅ T2-T5 | Synthesizer + single baseline |
| Llama 3.2 3B | ✅ meld-5 | ❌ | Never in experiments |
| **Claude (any)** | **❌** | **❌** | **Never tested** |
| Thinking models | ❌ | ❌ | Never tested |
| Qwen 72B | ❌ OpenRouter | Judging only | Judge, not participant |

### Full Variable Map

| Variable | Tested? | Expected Impact | Priority |
|----------|---------|-----------------|----------|
| Model architecture diversity | ✅ T4, T5 | HIGH (+11pp) | Done |
| Synthesizer quality | ✅ T5 | HIGHEST (+33pp) | Done |
| Refinement/second pass | ✅ T5 | MEDIUM (+39pp raw) | Done |
| Selection pressure | ✅ T5 | MEDIUM (+23pp) | Done |
| **Agent setup (system prompts, personality)** | ❌ | LIKELY HIGH | HIGH |
| **Claude in network** | ❌ | LIKELY HIGH | HIGH |
| **Thinking/reasoning models** | ❌ | LIKELY HIGH | HIGH |
| **Network size (3 vs 5 vs 7+)** | ❌ | UNKNOWN | MEDIUM |
| **Node specialization** | ❌ | LIKELY MEDIUM | MEDIUM |
| **Curation/reputation market** | ❌ | LIKELY MEDIUM | MEDIUM |
| **Memory/context per node** | ❌ | UNKNOWN | LOW |
| **Question routing** | ❌ | LIKELY HIGH | LOW (later) |

### Proposed Next Experiments
1. **T6: Agent setup impact** — same 3 models, bare API vs with system prompts/personas
2. **T7: Add Claude to network** — 4-model consensus including Claude
3. **T8: Thinking model in consensus** — one reasoning model in the mix
4. **T9: Network size scaling** — 3 vs 5 vs 7 models, diminishing returns
5. **T10: Intelligent node selection** — random vs curated, tests curation market thesis

### Curation Market Analysis
- Would NOT invalidate existing test results (tests measured raw consensus mechanics)
- Sits on top as a selection layer
- T5 already showed selection (H) beats single models
- Curation market = selection at network scale
- Creates flywheel: better curation → better results → more users → more quality data → better curation

### Long-Term Value Ranking
1. Synthesizer quality — biggest lever, whoever controls synthesis controls value
2. Model diversity — naturally grows with network
3. Thinking models — untested but likely transformative
4. Curation market — amplifier, creates flywheel
5. Network size — more nodes = more diversity, but only if genuinely different

### 3-Tier Architecture Usage (Self-Critique)
Agent acknowledged not using the full 3-tier architecture effectively. Experiments have been single-threaded Python scripts from /tmp. Should be:
- Sub-agents for parallel experiment arms
- Worker tier (Gemini Flash) for data processing/judging
- Opus for design and synthesis only

---

## Commits
- `d2d23df` — T5 data + scripts to meld-eval
- `ccbc3de` — All research docs to meld-eval/docs/
- `50b28f6` — T2 report to meld-eval/docs/

## Files Created/Updated
- `meld/research/T5-REPORT.md` — Full T5 analysis
- `meld/research/COMBINED-RESEARCH-REPORT.md` — All experiments consolidated
- `memory/2026-02-22.md` — Updated with T5 results
