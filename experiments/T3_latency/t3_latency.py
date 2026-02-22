#!/usr/bin/env python3
"""T3: Latency Profiling — MELD P2P consensus vs single-model inference.

Measures:
  A) Single model (Grok-3 direct) — baseline latency
  B) Single model (Gemini direct) — baseline latency
  C) Single model (DeepSeek direct) — baseline latency
  D) Fan-out to all 3 → synthesis (full P2P consensus pipeline)

For each of 50 questions, measures wall-clock time for each condition.
Outputs: results/t3_latency.jsonl with per-question timing data.
"""

import asyncio
import json
import time
import os
import sys
import httpx
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────
NODES = {
    "grok3": {
        "name": "meld-2",
        "url": "https://api.x.ai/v1/chat/completions",
        "model": "grok-3",
        "key_env": "XAI_API_KEY",
    },
    "gemini": {
        "name": "meld-3",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.0-flash",
        "key_env": "GEMINI_API_KEY",
    },
    "deepseek": {
        "name": "meld-4",
        "url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-chat",
        "key_env": "DEEPSEEK_API_KEY",
    },
}

SYNTHESIS_MODEL = "gpt-4o"
SYNTHESIS_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_KEY_ENV = "OPENAI_API_KEY"

MAX_TOKENS = 512
TIMEOUT = 60.0
NUM_QUESTIONS = 50

# ── Questions (diverse difficulty) ──────────────────────────────────────
QUESTIONS = [
    "What are the three most important factors in evaluating a startup's potential?",
    "Explain the difference between correlation and causation with a real-world example.",
    "What would happen to global trade if the Suez Canal was permanently closed?",
    "Write a haiku about artificial intelligence.",
    "What are the pros and cons of universal basic income?",
    "Explain quantum entanglement to a 10-year-old.",
    "What's the most underrated programming language and why?",
    "How would you design a city from scratch for 1 million people?",
    "What are the ethical implications of brain-computer interfaces?",
    "Explain the trolley problem and its relevance to self-driving cars.",
    "What would a post-scarcity economy look like?",
    "How does mRNA vaccine technology work?",
    "What are the strongest arguments for and against nuclear energy?",
    "Explain the concept of emergence in complex systems.",
    "What would first contact with an alien civilization look like realistically?",
    "How should we think about AI alignment?",
    "What's the best strategy for learning a new language as an adult?",
    "Explain the Byzantine Generals Problem and its relevance to blockchain.",
    "What are the most promising approaches to carbon capture?",
    "How would you explain the concept of infinity to someone who's never heard of it?",
    "What are the key differences between Eastern and Western philosophy?",
    "How does CRISPR gene editing work and what are its limitations?",
    "What would a world without money look like?",
    "Explain the difference between AI, ML, and deep learning.",
    "What are the most likely causes of the next global pandemic?",
    "How should we govern the development of AGI?",
    "What's the most efficient way to reduce global poverty?",
    "Explain the simulation hypothesis and its strongest critiques.",
    "What would happen if we discovered faster-than-light travel?",
    "How do you evaluate the credibility of a scientific study?",
    "What are the key principles of effective leadership?",
    "Explain how public key cryptography works.",
    "What would sustainable space colonization require?",
    "How does the placebo effect work and why is it important?",
    "What are the main challenges of building a fusion reactor?",
    "Explain the concept of opportunity cost with three examples.",
    "What would happen if the internet went down globally for a week?",
    "How should we balance privacy and security in the digital age?",
    "What are the most important unsolved problems in mathematics?",
    "Explain the difference between deductive and inductive reasoning.",
    "What would a perfect education system look like?",
    "How do neural networks actually learn?",
    "What are the key factors driving income inequality?",
    "Explain the observer effect in quantum mechanics.",
    "What would a world governed entirely by AI look like?",
    "How does the immune system distinguish self from non-self?",
    "What are the strongest arguments for space exploration?",
    "Explain the concept of diminishing returns in economics.",
    "What would happen if we could accurately predict the future?",
    "How should we think about consciousness in AI systems?",
]

# ── API call ────────────────────────────────────────────────────────────
async def call_model(client, url, model, api_key, question, max_tokens=MAX_TOKENS):
    """Call a single model, return (response_text, latency_ms, tokens)."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": question}],
        "max_tokens": max_tokens,
        "stream": False,
    }
    
    t0 = time.monotonic()
    try:
        resp = await client.post(url, json=body, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        latency_ms = (time.monotonic() - t0) * 1000
        
        text = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {})
        return text, latency_ms, tokens
    except Exception as e:
        latency_ms = (time.monotonic() - t0) * 1000
        return f"ERROR: {e}", latency_ms, {}


async def synthesize(client, question, responses, openai_key):
    """Synthesize multiple model responses into one answer."""
    prompt = f"""You are synthesizing multiple AI responses into one superior answer.

Question: {question}

Response from Grok-3:
{responses['grok3']}

Response from Gemini:
{responses['gemini']}

Response from DeepSeek:
{responses['deepseek']}

Synthesize these into a single, superior response that captures the best insights from all three. Be concise but thorough."""

    return await call_model(
        client, SYNTHESIS_URL, SYNTHESIS_MODEL, openai_key, prompt, max_tokens=MAX_TOKENS
    )


# ── Main ────────────────────────────────────────────────────────────────
async def run():
    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "t3_latency.jsonl"
    
    # Load API keys
    keys = {}
    for node_id, node in NODES.items():
        key = os.environ.get(node["key_env"])
        if not key:
            print(f"ERROR: {node['key_env']} not set")
            sys.exit(1)
        keys[node_id] = key
    
    openai_key = os.environ.get(OPENAI_KEY_ENV)
    if not openai_key:
        print(f"ERROR: {OPENAI_KEY_ENV} not set")
        sys.exit(1)

    print(f"T3 Latency Profiling — {NUM_QUESTIONS} questions × 4 conditions")
    print(f"Output: {out_path}")
    print()

    async with httpx.AsyncClient() as client:
        results = []
        
        for i, question in enumerate(QUESTIONS[:NUM_QUESTIONS]):
            print(f"[{i+1}/{NUM_QUESTIONS}] {question[:60]}...")
            row = {"q_idx": i, "question": question}
            
            # Condition A/B/C: Single model calls (sequential to avoid rate limits)
            for node_id, node in NODES.items():
                text, lat, tokens = await call_model(
                    client, node["url"], node["model"], keys[node_id], question
                )
                row[f"single_{node_id}_ms"] = round(lat, 1)
                row[f"single_{node_id}_text"] = text[:200]
                row[f"single_{node_id}_tokens"] = tokens
                print(f"  {node_id}: {lat:.0f}ms")
            
            # Condition D: Fan-out + synthesis
            t0 = time.monotonic()
            
            # Fan-out (parallel)
            fan_tasks = {}
            for node_id, node in NODES.items():
                fan_tasks[node_id] = call_model(
                    client, node["url"], node["model"], keys[node_id], question
                )
            
            fan_results = {}
            fan_latencies = {}
            for node_id, task in fan_tasks.items():
                text, lat, tokens = await task
                fan_results[node_id] = text
                fan_latencies[node_id] = lat
            
            fan_wall_ms = (time.monotonic() - t0) * 1000  # wait, this is wrong — need actual parallel
            
            # Redo fan-out properly with gather
            t0 = time.monotonic()
            
            async def _call(nid):
                n = NODES[nid]
                return nid, await call_model(client, n["url"], n["model"], keys[nid], question)
            
            fan_out = await asyncio.gather(*[_call(nid) for nid in NODES])
            fan_wall_ms = (time.monotonic() - t0) * 1000
            
            responses = {}
            for nid, (text, lat, tokens) in fan_out:
                responses[nid] = text
                row[f"fanout_{nid}_ms"] = round(lat, 1)
            
            row["fanout_wall_ms"] = round(fan_wall_ms, 1)
            
            # Synthesis
            synth_text, synth_ms, synth_tokens = await synthesize(
                client, question, responses, openai_key
            )
            
            row["synthesis_ms"] = round(synth_ms, 1)
            row["total_consensus_ms"] = round(fan_wall_ms + synth_ms, 1)
            row["synthesis_text"] = synth_text[:200]
            
            total = fan_wall_ms + synth_ms
            fastest_single = min(
                row["single_grok3_ms"],
                row["single_gemini_ms"],
                row["single_deepseek_ms"]
            )
            row["slowdown_ratio"] = round(total / fastest_single, 2)
            
            print(f"  consensus: {fan_wall_ms:.0f}ms fan-out + {synth_ms:.0f}ms synth = {total:.0f}ms total ({row['slowdown_ratio']}x)")
            
            results.append(row)
            
            # Write incrementally
            with open(out_path, "a") as f:
                f.write(json.dumps(row) + "\n")
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        avg_single = {nid: sum(r[f"single_{nid}_ms"] for r in results)/len(results) for nid in NODES}
        avg_consensus = sum(r["total_consensus_ms"] for r in results) / len(results)
        avg_slowdown = sum(r["slowdown_ratio"] for r in results) / len(results)
        
        for nid, avg in avg_single.items():
            print(f"  {nid} avg: {avg:.0f}ms")
        print(f"  consensus avg: {avg_consensus:.0f}ms")
        print(f"  avg slowdown: {avg_slowdown:.1f}x")
        
        # Write summary
        summary = {
            "type": "summary",
            "n_questions": len(results),
            "avg_single_ms": {nid: round(v, 1) for nid, v in avg_single.items()},
            "avg_consensus_ms": round(avg_consensus, 1),
            "avg_slowdown": round(avg_slowdown, 2),
            "fastest_single_avg_ms": round(min(avg_single.values()), 1),
        }
        with open(out_path, "a") as f:
            f.write(json.dumps(summary) + "\n")
        
        print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    asyncio.run(run())
