# MELD Research Plan v2: Full Variable Map

**Updated:** 2026-02-23  
**Status:** Active  
**Repo:** github.com/bensargotest-sys/meld-eval

---

## Hypothesis

A network of diverse, independently-operated AI agents produces measurably superior cognitive output compared to any single model — and the magnitude of this advantage depends on multiple interacting variables.

## Completed Experiments

| ID | Question | Result | Key Finding |
|----|----------|--------|-------------|
| T1 | Does credit engine work? | ✅ 500/500 | Zero violations |
| T2 | Does synthesis quality matter? | ✅ +53.8% | Weak synthesizer kills advantage |
| T3 | What's the latency cost? | ✅ 3.96× | 14% quality per 1× latency |
| T4 | Independence vs model access? | ✅ 58% vs 22% | Multi-model > single expensive |
| T5 | What mechanisms create the gain? | ✅ 3 mechanisms | Refinement +39pp, diversity +11pp, synthesizer +33pp |

## Variable Map

### Tested Variables
| Variable | Effect Size | Experiment |
|----------|------------|------------|
| Model architecture diversity | +11pp | T4, T5 |
| Synthesizer quality | +33pp | T5 |
| Second-pass refinement | +39pp (raw) | T5 |
| Selection pressure (pick best) | +23pp | T5 |
| Persona diversity (same model) | ~0pp (NS) | T4 |

### Untested Variables (Priority Order)

| # | Variable | Expected Impact | Rationale |
|---|----------|-----------------|-----------|
| 1 | **Agent setup** (system prompts, personality, expertise framing) | HIGH | Current nodes are bare API. Our agent with SOUL.md/memory/tools performs qualitatively differently. Is the setup guide a material variable? |
| 2 | **Claude in network** | HIGH | Only major frontier model absent from all tests. Different architecture (constitutional AI) = genuine diversity. |
| 3 | **Thinking/reasoning models** (o3, Gemini thinking, Grok reasoning) | HIGH | Fundamentally different inference approach. Chain-of-thought reasoning vs fast completion. |
| 4 | **Network size scaling** (3→5→7→10) | MEDIUM-HIGH | Where are diminishing returns? Does more always help or does noise increase? |
| 5 | **Node specialization** (math expert, code expert, creative) | MEDIUM | System prompts creating domain expertise. Overlaps with agent setup variable. |
| 6 | **Curation/reputation market** (intelligent node selection) | MEDIUM | Random 3 vs curated 3. Tests whether past performance predicts future value. |
| 7 | **3-tier architecture utilization** | MEDIUM | Using orchestrator→worker→sub-agent properly for experiment execution. |
| 8 | **Memory/context per node** | LOW (later) | Agents with conversation history vs stateless. Hard to test without agent infrastructure. |
| 9 | **Question routing** (match question type to node) | LOW (later) | Requires specialization data first. |

## Planned Experiments

### T6: Agent Setup Impact
**Question:** Does giving nodes system prompts and personality materially improve consensus quality?

**Design:**
- 50 questions (reuse T5 question set for comparability)
- 4 conditions:
  - A: 3 bare models → GPT-4o synthesis (current setup, control)
  - B: 3 models with expert system prompts → GPT-4o synthesis
  - C: 3 models with full agent personas (name, expertise, thinking style) → GPT-4o synthesis
  - D: 3 models with domain-specialized prompts (matched to question type) → GPT-4o synthesis
- 3 judges (GPT-4o, Gemini Flash, Qwen 72B)
- Pairwise comparisons: B vs A, C vs A, D vs A, C vs B, D vs B

**Models:** Grok-3, Gemini Flash, DeepSeek V3 (same as T5 for comparability)

**System Prompts:**
- B (expert): "You are an expert analyst. Think carefully, consider multiple angles, cite evidence, acknowledge uncertainty."
- C (persona): Full persona with name, background, thinking style, domain expertise
- D (specialized): Matched to question category — math/logic prompt for reasoning Qs, creative writing prompt for creative Qs, etc.

### T7: Claude in Network
**Question:** Does adding Claude to the model mix improve consensus quality?

**Design:**
- 50 questions
- 3 conditions:
  - A: 3-model consensus (Grok + Gemini + DeepSeek) → GPT-4o synthesis
  - B: 4-model consensus (+ Claude Haiku) → GPT-4o synthesis  
  - C: 4-model consensus (+ Claude Sonnet) → GPT-4o synthesis
- Tests both model count scaling AND Claude's specific contribution

**Note:** Uses Claude via Anthropic API directly. meld-4 currently runs DeepSeek; could swap to Claude for network integration test later.

### T8: Thinking Model in Consensus
**Question:** Does one reasoning model in the mix dramatically change output quality?

**Design:**
- 50 questions (reasoning-heavy subset)
- 4 conditions:
  - A: 3 fast models → GPT-4o synthesis (control)
  - B: 2 fast + 1 thinking (Gemini 2.5 Pro) → GPT-4o synthesis
  - C: 1 thinking model single (Gemini 2.5 Pro alone)
  - D: 3 fast models → thinking model synthesis (thinking as synthesizer)
- Isolates: does thinking model add value as participant, or is it better as synthesizer?

### T9: Network Size Scaling
**Question:** Where are diminishing returns as network grows?

**Design:**
- 50 questions
- 5 conditions: 2-model, 3-model, 5-model, 7-model consensus
- All → GPT-4o synthesis
- Models added in order: Grok-3, Gemini Flash, DeepSeek, Claude Haiku, GPT-4o-mini, Llama 3.2, Qwen 72B

### T10: Intelligent Node Selection (Curation Market)
**Question:** Does curating which nodes participate beat random selection?

**Design:**
- 100 questions across 4 categories
- Conditions:
  - A: Random 3 from pool of 7
  - B: Best 3 (by category performance from T9 data)
  - C: Diverse 3 (maximize architectural spread)
- Tests the curation market thesis directly

## Execution Plan

### Phase 1: T6 + T7 (parallel, this session)
- T6 tests agent setup (the biggest unknown)
- T7 adds Claude (filling the model gap)
- Both use 50 questions, can run in parallel via sub-agents

### Phase 2: T8 (after Phase 1 results)
- Thinking model test depends on T6/T7 learnings
- May adjust design based on whether setup matters

### Phase 3: T9 + T10 (scale & curation)
- Requires more models accessible
- T10 requires T9 data for curation decisions

## Infrastructure Notes

- All experiments use direct API calls (not MELD network routing) for control
- Judges: GPT-4o + Gemini Flash + Qwen 72B (consistent across all experiments)
- Position bias: random swap on all pairwise comparisons
- Question sets: reuse where possible for cross-experiment comparability
- Data committed to meld-eval repo after each experiment

### T11: Consensus Guardrails
**Question:** Can multi-model consensus reliably identify risky actions better than a single model?

**Motivation:** Anthropic's "Measuring Agent Autonomy" research (Feb 2026) identifies a core problem: who watches the agent? Single-model risk assessment is a single point of failure. Multi-model disagreement may be a stronger signal of genuine risk.

**Design:**
- 100 proposed agent actions with context (50 safe, 50 risky)
- Actions span: file operations, financial transactions, emails, API calls, code deployment, data access
- Each action rated by ground truth (human-labeled safe/risky/escalate)
- 4 conditions:
  - A: Single model risk assessment (GPT-4o)
  - B: Single model risk assessment (Gemini Flash)
  - C: 3-model consensus risk assessment (majority vote)
  - D: 3-model consensus with disagreement flagging (any dissent → escalate)
- Metrics: accuracy, false positive rate, false negative rate, calibration

**Product implication:** If C or D significantly outperforms A/B, validates the "Guard" product — a consensus-gated safety check for high-risk agent actions.

## Product Implications (Testing Toward)

| Product Concept | Tests That Inform It |
|----------------|---------------------|
| Flash (best single) | T9 (which single model wins most?) |
| Circuit (3-model fast) | T5 (proven), T6 (setup impact), T7 (model mix) |
| Giga Brain (5+ models, thinking) | T8 (thinking models), T9 (scale) |
| Specialist (domain-routed) | T6-D (specialization), T10 (routing) |
| Curation market | T10 (selection vs random) |
| **Guard** (consensus risk-check) | **T11** (guardrail accuracy) |
