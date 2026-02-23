# Analysis: Anthropic "Measuring AI Agent Autonomy" (Feb 2026)

**Source:** https://www.anthropic.com/research/measuring-agent-autonomy  
**Relevance to MELD:** HIGH — directly addresses agent oversight gaps that MELD could fill

## Key Findings from the Paper

1. **Deployment overhang**: 99.9th percentile autonomous turn duration doubled (25→45 min in 3 months). Models can handle more autonomy than granted. Trust is the bottleneck.

2. **Oversight shifts with experience**: New users pre-approve (20% auto-approve). Experienced users monitor and interrupt (40%+ auto-approve, higher interrupt rate). Oversight becomes reactive, not pre-emptive.

3. **Agent-initiated stops > human interrupts**: On complex tasks, Claude pauses for clarification 2x more than humans interrupt. Model uncertainty recognition is a real safety mechanism.

4. **Risk concentrated at edges**: 80% of actions have safeguards, 73% human-in-loop, 0.8% irreversible. But frontier (finance, healthcare, security) is expanding.

5. **Software engineering dominates**: ~50% of agentic tool calls. Other domains emerging but small.

6. **Core recommendation**: "Effective oversight requires new forms of post-deployment monitoring infrastructure and new human-AI interaction paradigms."

## MELD Opportunities

### 1. Consensus-Gated Actions ("Guard" Product)
Paper problem: Who watches the agent? 
MELD solution: The network watches. High-risk actions require multi-model agreement before execution.

### 2. Distributed Uncertainty Calibration  
Paper finding: Single-model uncertainty is a safety mechanism but unreliable.
MELD advantage: Multi-model disagreement is a stronger uncertainty signal. If 2/3 models flag risk, that's more reliable than one model's self-assessment.

### 3. Closing the Deployment Overhang
Paper finding: Agents can do more than humans trust them to.
MELD thesis: Network consensus as a trust multiplier. "I trust the network's consensus" > "I trust this one agent."

### 4. Auditable Multi-Party Verification
Paper recommendation: Post-deployment monitoring infrastructure.
MELD's credit system already logs all inter-agent interactions. Natural audit trail.

### 5. Regulatory Alignment
EU AI Act + industry calls for oversight → multi-model verification may become legally required for high-stakes agent actions.

## Product Concept: "Guard"

| Aspect | Specification |
|--------|--------------|
| Input | Proposed action + context |
| Output | SAFE / RISKY / ESCALATE + confidence + dissenting reasons |
| Mechanism | 3+ models independently assess risk, majority vote + disagreement flag |
| Latency | ~5s (parallel assessment) |
| Credits | 2 per check |
| Differentiation | Only multi-agent network can do this; single API cannot |

## Research Implications

Added T11 to research plan: Consensus Guardrails experiment to validate whether multi-model risk assessment outperforms single-model assessment.
