#!/usr/bin/env python3
"""T5 Judging: Pairwise comparisons to isolate mechanism.

Key comparisons:
  F vs B  — Does self-refinement help?
  F vs E  — Is synthesis just refinement?
  G vs E  — Is it just Grok-3 being better?
  H vs B  — Does selection (no synthesis) help?
  I vs B  — Does cheap synthesis beat single GPT-4o?
  I vs E  — Does cheap synthesis match expensive?
"""

import asyncio
import json
import os
import random
import httpx
from pathlib import Path

JUDGES = {
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.0-flash", "key_env": "GEMINI_API_KEY",
    },
    "gpt4o": {
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o", "key_env": "OPENAI_API_KEY",
    },
    "qwen": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "qwen/qwen-2.5-72b-instruct", "key_env": "OPENROUTER_API_KEY",
    },
}

COMPARISONS = [
    ("F", "B", "F_vs_B"),   # self-refine vs single
    ("F", "E", "F_vs_E"),   # self-refine vs multi-model synthesis
    ("G", "E", "G_vs_E"),   # single Grok-3 vs multi-model synthesis
    ("H", "B", "H_vs_B"),   # best-of-3 selection vs single GPT-4o
    ("I", "B", "I_vs_B"),   # cheap synthesis vs single GPT-4o
    ("I", "E", "I_vs_E"),   # cheap synthesis vs expensive synthesis
]

PROMPT = """You are an expert judge. Which response is better?

Question: {question}

Response X:
{rx}

Response Y:
{ry}

Reply EXACTLY: X_WINS, Y_WINS, or TIE"""


async def judge_one(client, jcfg, key, question, rx, ry):
    try:
        resp = await client.post(jcfg["url"],
            json={"model": jcfg["model"], "messages": [{"role": "user",
                  "content": PROMPT.format(question=question, rx=rx, ry=ry)}],
                  "max_tokens": 10, "temperature": 0},
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            timeout=60.0)
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip().upper()
        if "X_WIN" in text or "X WIN" in text: return "X"
        elif "Y_WIN" in text or "Y WIN" in text: return "Y"
        elif "TIE" in text: return "TIE"
        else: return f"UNCLEAR:{text[:30]}"
    except Exception as e:
        return f"ERROR:{e}"


async def run():
    responses = [json.loads(l) for l in open("/tmp/results/t5_responses.jsonl")]
    out_path = Path("/tmp/results/t5_judgments.jsonl")
    print(f"T5 Judging — {len(responses)} questions × {len(COMPARISONS)} comparisons × {len(JUDGES)} judges")

    keys = {jid: os.environ.get(j["key_env"]) for jid, j in JUDGES.items()}
    keys = {k: v for k, v in keys.items() if v}
    print(f"Active judges: {list(keys.keys())}")

    from collections import defaultdict
    results = defaultdict(lambda: defaultdict(lambda: {"X": 0, "Y": 0, "TIE": 0, "ERR": 0}))

    async with httpx.AsyncClient() as client:
        for i, row in enumerate(responses):
            q = row["question"]
            print(f"[{i+1}/{len(responses)}] {q[:50]}...")
            for fx, fy, comp_name in COMPARISONS:
                rx_text = row.get(fx, "")
                ry_text = row.get(fy, "")
                if not rx_text or not ry_text or str(rx_text).startswith("ERROR") or str(ry_text).startswith("ERROR"):
                    continue

                swap = random.random() > 0.5
                ax, ay = (ry_text, rx_text) if swap else (rx_text, ry_text)

                for jid in keys:
                    v = await judge_one(client, JUDGES[jid], keys[jid], q, ax, ay)
                    if swap:
                        if v == "X": v = "Y"
                        elif v == "Y": v = "X"

                    bucket = "X" if v == "X" else "Y" if v == "Y" else "TIE" if v == "TIE" else "ERR"
                    results[comp_name][jid][bucket] += 1

                    with open(out_path, "a") as f:
                        f.write(json.dumps({"q_idx": row["q_idx"], "comparison": comp_name,
                                            "judge": jid, "verdict": v, "swapped": swap}) + "\n")

    # Summary
    print("\n" + "="*70)
    print("T5 RESULTS")
    print("="*70)

    labels = {"F_vs_B": ("F:self-refine", "B:GPT-4o"), "F_vs_E": ("F:self-refine", "E:multi-synth"),
              "G_vs_E": ("G:Grok-3", "E:multi-synth"), "H_vs_B": ("H:best-of-3", "B:GPT-4o"),
              "I_vs_B": ("I:cheap-synth", "B:GPT-4o"), "I_vs_E": ("I:cheap-synth", "E:multi-synth")}

    for comp_name in [c[2] for c in COMPARISONS]:
        data = results[comp_name]
        tx = sum(d["X"] for d in data.values())
        ty = sum(d["Y"] for d in data.values())
        tt = sum(d["TIE"] for d in data.values())
        te = sum(d["ERR"] for d in data.values())
        total = tx + ty + tt
        if total == 0: continue
        lx, ly = labels[comp_name]
        winner = lx if tx > ty else ly if ty > tx else "TIE"
        print(f"\n{comp_name}: {lx} vs {ly}")
        print(f"  {lx}: {tx}({tx/total*100:.1f}%)  {ly}: {ty}({ty/total*100:.1f}%)  TIE: {tt}({tt/total*100:.1f}%)  ERR: {te}")
        print(f"  Winner: {winner}")

    print("\n" + "="*70)
    print("MECHANISM ISOLATION VERDICTS")
    print("="*70)

    def get_rates(comp):
        d = results[comp]
        tx = sum(v["X"] for v in d.values())
        ty = sum(v["Y"] for v in d.values())
        tt = sum(v["TIE"] for v in d.values())
        n = tx+ty+tt
        return tx/n*100 if n else 0, ty/n*100 if n else 0, n

    fx, fy, n = get_rates("F_vs_B")
    print(f"\n1. Self-refinement vs single: F={fx:.0f}% B={fy:.0f}%")
    if fx > fy + 5: print("   → Self-refine helps. Second pass adds value.")
    else: print("   → Self-refine ≈ single. Second pass alone isn't the mechanism.")

    fx, fy, n = get_rates("F_vs_E")
    print(f"\n2. Self-refinement vs multi-model synthesis: F={fx:.0f}% E={fy:.0f}%")
    if fy > fx + 5: print("   → Multi-model synthesis > self-refine. DIVERSITY ADDS VALUE.")
    elif abs(fx-fy) < 5: print("   → F ≈ E. Synthesis is just refinement. No diversity value.")
    else: print("   → Self-refine > multi-model?? Unexpected.")

    fx, fy, n = get_rates("G_vs_E")
    print(f"\n3. Single Grok-3 vs multi-model synthesis: G={fx:.0f}% E={fy:.0f}%")
    if fy > fx + 5: print("   → Multi-model > single Grok. Not just model quality.")
    elif abs(fx-fy) < 5: print("   → G ≈ E. E's advantage was just Grok-3 being better.")

    fx, fy, n = get_rates("H_vs_B")
    print(f"\n4. Best-of-3 selection vs single GPT-4o: H={fx:.0f}% B={fy:.0f}%")
    if fx > fy + 5: print("   → Selection helps even without synthesis.")
    else: print("   → Selection ≈ single. Need synthesis, not just picking.")

    fx, fy, n = get_rates("I_vs_B")
    print(f"\n5. Cheap synthesis vs GPT-4o single: I={fx:.0f}% B={fy:.0f}%")
    if fx > fy + 5: print("   → Even cheap synthesis beats single GPT-4o!")
    else: print("   → Cheap synthesis doesn't help. Need strong synthesizer.")

    fx, fy, n = get_rates("I_vs_E")
    print(f"\n6. Cheap synthesis vs expensive: I={fx:.0f}% E={fy:.0f}%")
    if fy > fx + 5: print("   → Expensive synthesis wins. Synthesizer quality matters.")
    elif abs(fx-fy) < 5: print("   → Cheap ≈ expensive. Synthesizer quality doesn't matter much.")


if __name__ == "__main__":
    asyncio.run(run())
