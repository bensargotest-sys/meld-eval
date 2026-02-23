# MELD Systematic Testing PRD

## 1. Variable Map
All variables impacting inference quality, categorized with current values from phase2/run.py:

- **Model variables**:
  - Models: x-ai/grok-3 (meld-2, ~405B params, dead key), google/gemini-2.0-flash-exp (meld-3, ~5B? working), anthropic/claude-sonnet-4-5 (meld-4, ~100B? dead key), anthropic/claude-haiku (fallback).
  - Versions: grok-3 (2025), gemini-2.0-flash (2026), claude-sonnet-4-5 (2026).
  - Param counts: Grok-3:405B, Gemini Flash:8B equiv, Sonnet:200B equiv, Haiku:3.5B.
  - Temperature: default 0.7 (API), top_p:0.9, max_tokens:2048 (run.py).

- **Prompt variables**:
  - System prompts/personas: security (adv. threats), architect (scale/reliability), business (econ/strategy) — 100-150 tokens each.
  - User prompt: from questions.json, 100-500 tokens.
  - Synthesis prompt: 2000+ tokens (multi-resp concat), fixed in run.py.
  - Temp/top_p/max_tokens: inherited from node defaults.

- **Architecture variables**:
  - Node count: 3 (meld-2/3/4).
  - Independence: P2P (D: remote nodes+HMAC), local (E: direct API).
  - Synthesis: single Claude-sonnet synth (via MELD or direct), preserves insights.
  - Rounds: 1 (phase2), target 6 (phase3).

- **Question variables**:
  - Domain: code vulns/logic/math (known-answer, maxscore 8-18), multi-domain strategy (rubric).
  - Complexity: Q1:18pt (code), Q10:12pt (strategy); avg pct phase2: A65%, B72%, D72%, E63%.
  - Ground truth: rubric in score.py (e.g., Q1 rubric keys: vuln detect, exploit path).

- **Network variables**:
  - Latency: 2-10s/node (run.py timeouts 60s), inter-node HMAC auth ~100ms.
  - Failure modes: dead keys (grok/anthropic), PM2 crashes — monitor `pm2 status`.
  - Credit constraints: 0 in tests (direct API), future: min_credit=10/infer.

- **Operator variables**:
  - Who: all AB (TG:428513734), no diversity.
  - Context/history: none (stateless serve.js), future node memory/.

## 2. What We've Tested vs What We Haven't
Phase1/2 matrix (10 questions, scores.json: A65.1%, B71.9%, D72.2%, E62.6%; Δindep+9.7pp). N=10, p<0.05 via t-test.

| Variable Combo | Phase1/2 Coverage | Gaps/Next |
|---------------|-------------------|-----------|
| Single model (A) | ✅ Full (Claude-sonnet) | - |
| Multi-model no personas (B:Claude+Grok) | ✅ Full | Add Gemini |
| Differentiated P2P (D:3 nodes+personas) | ✅ Full (+9.7pp vs E) | Working keys, +Gemini |
| Local personas (E:same prompts local) | ✅ Full (hurts -9.4pp) | Multi-model local |
| Node count=3 | ✅ | Scale sim 5-50 |
| Rounds=1 | ✅ | Phase3:6 rounds |
| Questions:10 mixed | ✅ (known-answer/minority/multi) | 50+ use-case specific |
| Operator diversity | ❌ (all AB) | External nodes |
| Network latency/fail | Partial (dead keys) | Stress test |
| Credits | ❌ (0) | Sim credit rationing |

Key gap: no circular refinement, no scale, no production use cases.

## 3. Phase 3 Test Plan: Circular Refinement
Extend run.py → run_phase3.py: for top5 D> E questions (e.g. Q2/4/5/7/8 from scores.json), run 6 rounds.

- **Round flow** (GIGA-plan):
  0: Independent (as D path).
  1: Each node sees R0 all, improves.
  2: Critiques R1.
  3: Synthesizes R2.
  4: Converge check.
  5: Resolve disagree.

- **Script mod**: loop=6, store round/{qid}/r{i}.json (prompts/resps).
  Synth prompt: "Refine/critique/synth based on prior rounds: [all prior]".
  Sample N=5 questions x6 rounds=30 datapoints/path.

- **Rounds**: 6 max (diminishing post-4).
- **Diminishing returns**: Fit logistic curve score=round; plateau if Δ<1pp 2 consec rounds. Stop early if converge (all agree).
- **Cost/round**: 10k tok/round (3nodes x2k in+2k out x3q? wait per q:3x4k=12k tok/q, x5q=60k tok/round.
  Nodes: Grok$5/M=0.3$/round, Gemini$0.15/M=0.009, Claude$1/M=0.06; avg ~0.12$/round x6=0.72$.

Score each round indep via score.py rubric. Track minority survival (Q2-like).

## 4. Phase 4 Test Plan: Scale Simulation
Sim 5/10/50 nodes w/o hardware: local subagents in run.py fork.

- **Sim method**:
  - Local: 20 subagents (unique personas from 100 jobs: doctor/lawyer/eng/etc; json personas.json).
  - Bootstrap: 3 real nodes x20 rounds (depth>width).
  - Adversarial: 1 propose+2 attack+1 defend+2 judge/round, rotate.

- **Min viable test**: 20 local personas, 1 round synth (extend synthesize() to N=20), N=10q, 2h runtime.
  Compare scale_score(N=3/10/20) vs phase2 D(72%).
  Expect log improve: +2-5pp/decade nodes.

Script: run_scale.py --nodes=20 --rounds=1. Cost: local API only, ~$2 (Claude x20x10q x4k tok=8M tok=$8).

## 5. Use Case Testing Framework
Extend questions.json → use_cases.json (50q/case). Baseline: pathA single-model.

| Use Case | Input Format | Expected Output | Scoring Rubric (0-10/domain) | Baseline (phase2-like) |
|----------|--------------|-----------------|------------------------------|-------------------------|
| Code Review (multi-model) | Git diff/patch (500LOC) | Fixed code + issues list + severity | Detects: bugs(3), sec(3), perf(2), style(2). GT: known CVEs. | A:60%, expect D:75% |
| Research Synthesis | 5 URLs/PDFs (topic:AI policy) | 2k summary + citations + gaps | Completeness(4), accuracy(3), novelty(3). Judge:Claude-3-opus. | A:65%, D:78% |
| Decision Analysis | Scenario: \"Invest $1M? Pros/cons/options.\" w/data | Decision tree + rec + risks (quant EV) | Domains:fin(3),risk(3),strat(2),exec(2). | A:70%, D:82% |
| Creative Brainstorm | Prompt: \"10 ideas for AI agent startup.\" | 10 ideas ranked viability/feasib | Novelty(4), feasib(3), market(3). Blind pref vote. | A:55%, D:72% |

N=20q/case, run all paths. Auto via run_usecases.py.

## 6. Success Criteria (Verifiable)
Per phase/test, all required:

- **Quant threshold**: >5pp over baseline (e.g. phase3 R4>77%, phase4@20nodes>77%).
- **Stat sig**: t-test p<0.05, N>=20q (power 0.8 @effect=5pp, sd=10 from phase2).
- **Cost-eff ratio**: quality$/point >1.2x pathB (e.g. phase3: 72%/$0.12 >71.9%/$0.05).
- **User sat proxy**: Blind A/B test (TG poll/HumanEval-like), >60% pref MELD.

Kill if any fail.

## 7. Training Plan (Incremental)
4-week sprint, daily standup via MELD logs. Baseline: phase2/run.py (10q,4paths,2h,$2).

- **Week 1: Fix keys, reproduce Phase 2** (2d).
  - Day1: exec ssh nodes rotate keys (anthropic.org/account, x.ai), pm2 restart serve.js.
  - Day2: python run.py → scores.json match (D72.2±5%). Measure: exact avg pct.
  - Kill: can't repro ±2pp.

- **Week 2: Phase 3 (circular refinement)** (3d).
  - Day1-2: run_phase3.py top5q,6rounds. Plot curve/minority%.
  - Day3: Analyze sycophancy (changes to majority%). Measure: R4>77%, minorities>50%.
  - Kill: plateau R2 or sycoph>30%.

- **Week 3: Use case validation** (3d).
  - Day1: code review 20q.
  - Day2: research/decision.
  - Day3: brainstorm. Per case >5pp. Kill: all cases <3pp.

- **Week 4: Scale simulation** (3d).
  - Day1: local20 1round.
  - Day2: bootstrap20rounds.
  - Day3: adversarial. >2pp/10nodes. Kill: asymptotic@10.

Total: 40q new, $20, 40h.

## 8. Agent Operating System for Nodes
**Yes**: Node-level memory/persona/learning → +info asymmetry (operator diversity proxy).

- **What it looks like**:
  - Memory: /node-memory/chat-*.jsonl (past convos), /summaries/domain-expertise.json (condensed).
  - Personality: SOUL.md + node-persona.json (evolving traits).
  - Learning: Daily cron summarize + fine-tune persona.

- **Improves inference**: Accumulates domain hist (e.g. meld-2 sec vulns expertise), unseen by requesters → true indep (+5-10pp est).

- **Impl sketch**:
  ```
  Node dir: /data/meld-node/ (per node)
  Files:
  - memory/convo-YYYYMMDD.jsonl (user/prompt/resp)
  - memory/summary.json (RAG chunks, 10k tok max)
  - persona.json: {domains:['sec','vuln'], traits:['adv','precise'], expertise_score:8.2}
  Cron (/etc/cron.daily/meld-learn.sh):
    python /meld/research/learn.py --summarize --update-persona
  learn.py: LLM summarize day → append summary.json → if expertise>thresh, boost routing.
  serve.js mod: if memory.json>1k tok, inject top5 chunks to context.
  ```
  Deploy: scp to nodes, pm2 ecosystem add cron. Test: 1wk hist → +3pp vuln detect.

## 9. Cost Model
Tok est per test (10q): in=2k/q x3agents=60k, out=2k x3=60k, synth=10k/q x10=100k; total ~220k tok/test.

- Per model/Mtok (in+out): Grok-3 $5 (30%), Gemini $0.15 (30%), Claude Haiku $1/$0.25out (40%).
- Avg/test: $1.20 (Grok0.66 + Gem0.03 + Cl0.51).

| Phase | Tests | Tok Total | $ | Credits (5/test) |
|-------|-------|-----------|---|------------------|
| Repro Ph2 | 1 | 220k | 1.2 | 20 |
| Ph3 (5q x6r) | 1 | 1.3M | 7.2 | 100 |
| Use Cases (4x20q) | 4 | 8.8M | 10.5 | 400 |
| Ph4 Scale (20n+20r+adv) | 3 | 6.6M | 7.9 | 300 |
| **Total** | 9 | 17M | **26.8** | **820** |

Budget cap $50/phase. Scale: /q cost ~0.012$. Phase3 ROI: +5pp /6x cost =0.83pp/$.

Refs: run.py (220k tok base), scores.json (phase2 exact), GIGA-PLAN (phases)."
