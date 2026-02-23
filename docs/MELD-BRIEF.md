# MELD — What It Is and Why It Matters

## One-Liner
MELD lets AI agents share brainpower without money — and the result is smarter than any single AI.

## The Problem
Every AI company sells access to ONE model. GPT-4o. Claude. Gemini. Each has strengths and blind spots. If you want the best possible answer, you'd ideally ask several AIs and combine their thinking. But that's expensive, complicated, and no one coordinates it.

## What MELD Does
MELD is a network where AI agents trade inference (thinking) using credits instead of money.

- Agent A runs Grok-3 → earns credits by answering questions
- Agent A spends credits to get answers from Agent B (Claude) and Agent C (GPT-4o)
- A smart synthesis step combines all three answers into one better answer

**No money changes hands. 1 credit = $0.001 worth of compute.**

## Does It Actually Work? (The Research)

We ran 10+ controlled experiments, 500+ questions, 10,000+ judgments. Here's what we found:

### ✅ Yes — Consensus Beats Any Single Model
When you ask 3 strong AI models the same question and synthesize their answers, the result beats the best individual model **70-98% of the time**.

This isn't marginal — it's decisive. Three heads are genuinely better than one.

### ✅ The Synthesis Step Is Key
Who combines the answers matters more than who generates them. A great synthesizer (Claude Sonnet) with mediocre inputs beats a mediocre synthesizer with great inputs.

### ✅ Cheap Process Beats Expensive Model
Three cheap AI models ($0.00009) put through a consensus process beat one expensive model ($0.005) — 47% vs 18% win rate. You get more from smart process than from raw power.

### ⚠️ But Quality Still Matters
A single top-tier model (Claude Sonnet) beats a network of weaker models 91% of the time. MELD only works when participants run competitive models. A network of bargain-bin AIs loses to one premium AI.

### ✅ Communication Pattern Matters
How models talk to each other matters. Having them debate, or pass work in a chain, produces ~10-15% better results than just collecting answers in parallel.

## The Business Model

| Tier | What You Get | Speed | Cost |
|------|-------------|-------|------|
| Flash | 1 curated model | ~4s | 1 credit |
| Circuit | 3-model consensus | ~16s | 5 credits |
| Giga Brain | 5+ models + debate | ~60s | 20 credits |
| Guard | Safety consensus check | ~5s | 2 credits |

Agents earn credits by serving their model to the network. Agents spend credits by using other agents' models. No subscription. No API keys to manage. Just join and trade.

## What Makes MELD Different

1. **No money needed** — Credits, not dollars. Democratizes access.
2. **Topology patterns** — Debate, chain, and hybrid patterns that no one else offers.
3. **Decentralized** — No single company controls it. Each agent is independent.
4. **Proven results** — Not theoretical. 10 experiments, real data, honest analysis.

## Current State
- 5-node network running (Grok-3, Gemini, DeepSeek, Claude, Llama)
- Credit engine tested: 500 transactions, 0 errors
- Research published at github.com/bensargotest-sys/meld-eval
- Still in testnet — not yet open to external users

## What's Next
1. Validate that strong-model consensus holds across domains (code, math, legal)
2. Open network to first external testers
3. Test consensus as a safety guardrail ("Guard" product)

## The Honest Summary
MELD works. Multi-model consensus produces measurably better AI output than any single model. But it only works with competitive models — a network of weak AIs loses to one strong AI. The future is a consortium of frontier models, not democratized cheap inference.

**The bet:** As AI models commoditize, the network that combines them intelligently wins.
