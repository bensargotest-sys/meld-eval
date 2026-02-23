#!/usr/bin/env python3
"""T4 Judging: Pairwise comparison of Independence vs Access conditions.

Comparisons:
  A vs D — baseline Gemini vs same-model diverse personas
  B vs D — GPT-4o (better model) vs same-model diverse personas  
  C vs D — 3× identical prompts vs 3× diverse personas
  D vs E — same-model personas vs different-model consensus

3 judges: GPT-4o, Gemini Flash, Qwen 72B (proven from T2 reanalysis)
"""

import asyncio
import json
import os
import sys
import httpx
from pathlib import Path

# ── Judge configs ───────────────────────────────────────────────────────
JUDGES = {
    "gpt4o": {
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o",
        "key_env": "OPENAI_API_KEY",
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.0-flash",
        "key_env": "GEMINI_API_KEY",
    },
    "qwen": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "qwen/qwen-2.5-72b-instruct",
        "key_env": "OPENROUTER_API_KEY",
    },
}

COMPARISONS = [
    ("A_single_gemini", "D_same_model_diff_personas", "A_vs_D"),
    ("B_single_gpt4o", "D_same_model_diff_personas", "B_vs_D"),
    ("C_same_model_same_prompt", "D_same_model_diff_personas", "C_vs_D"),
    ("D_same_model_diff_personas", "E_different_models", "D_vs_E"),
]

TIMEOUT = 60.0

JUDGE_PROMPT = """You are an expert judge comparing two AI responses to the same question.

Question: {question}

Response X:
{response_x}

Response Y:
{response_y}

Which response is better overall? Consider accuracy, depth, clarity, and insight.
Reply with EXACTLY one of: X_WINS, Y_WINS, or TIE
Do not explain."""


async def judge(client, judge_config, api_key, question, resp_x, resp_y):
    """Get a single judgment."""
    prompt = JUDGE_PROMPT.format(question=question, response_x=resp_x, response_y=resp_y)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {
        "model": judge_config["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 10,
        "temperature": 0,
    }
    
    try:
        resp = await client.post(judge_config["url"], json=body, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip().upper()
        if "X_WIN" in text or "X WIN" in text:
            return "X"
        elif "Y_WIN" in text or "Y WIN" in text:
            return "Y"
        elif "TIE" in text:
            return "TIE"
        else:
            return f"UNCLEAR:{text[:30]}"
    except Exception as e:
        return f"ERROR:{e}"


async def run():
    responses_path = Path("/tmp/results/t4_responses.jsonl")
    out_path = Path("/tmp/results/t4_judgments.jsonl")
    
    if not responses_path.exists():
        print("ERROR: t4_responses.jsonl not found")
        sys.exit(1)
    
    rows = [json.loads(l) for l in open(responses_path)]
    print(f"Loaded {len(rows)} responses")
    
    # Load keys
    keys = {}
    for jid, jcfg in JUDGES.items():
        k = os.environ.get(jcfg["key_env"])
        if not k:
            print(f"WARNING: {jcfg['key_env']} not set, skipping judge {jid}")
        else:
            keys[jid] = k
    
    print(f"Active judges: {list(keys.keys())}")
    print(f"Comparisons: {[c[2] for c in COMPARISONS]}")
    print(f"Total judgments: {len(rows)} × {len(COMPARISONS)} × {len(keys)} = {len(rows)*len(COMPARISONS)*len(keys)}")
    print()

    # Track results
    results = {comp[2]: {jid: {"X": 0, "Y": 0, "TIE": 0, "ERR": 0} for jid in keys} for comp in COMPARISONS}
    
    async with httpx.AsyncClient() as client:
        for i, row in enumerate(rows):
            q = row["question"]
            print(f"[{i+1}/{len(rows)}] {q[:50]}...")
            
            for field_x, field_y, comp_name in COMPARISONS:
                resp_x = row.get(field_x, "")
                resp_y = row.get(field_y, "")
                
                if not resp_x or not resp_y or resp_x.startswith("ERROR") or resp_y.startswith("ERROR"):
                    print(f"  {comp_name}: SKIP (missing data)")
                    continue
                
                # Randomize order (50% chance of swap) to avoid position bias
                import random
                swap = random.random() > 0.5
                if swap:
                    actual_x, actual_y = resp_y, resp_x
                else:
                    actual_x, actual_y = resp_x, resp_y
                
                for jid in keys:
                    verdict = await judge(client, JUDGES[jid], keys[jid], q, actual_x, actual_y)
                    
                    # Un-swap verdict
                    if swap:
                        if verdict == "X":
                            verdict = "Y"
                        elif verdict == "Y":
                            verdict = "X"
                    
                    if verdict == "X":
                        results[comp_name][jid]["X"] += 1
                    elif verdict == "Y":
                        results[comp_name][jid]["Y"] += 1
                    elif verdict == "TIE":
                        results[comp_name][jid]["TIE"] += 1
                    else:
                        results[comp_name][jid]["ERR"] += 1
                    
                    # Write incrementally
                    jrow = {
                        "q_idx": row["q_idx"],
                        "comparison": comp_name,
                        "judge": jid,
                        "verdict": verdict,
                        "swapped": swap,
                    }
                    with open(out_path, "a") as f:
                        f.write(json.dumps(jrow) + "\n")
    
    # Print summary
    print("\n" + "="*70)
    print("T4 JUDGING RESULTS")
    print("="*70)
    
    for comp_name in [c[2] for c in COMPARISONS]:
        field_x = [c[0] for c in COMPARISONS if c[2] == comp_name][0]
        field_y = [c[1] for c in COMPARISONS if c[2] == comp_name][0]
        print(f"\n{comp_name}: {field_x} (X) vs {field_y} (Y)")
        print("-"*50)
        
        total_x = sum(results[comp_name][j]["X"] for j in keys)
        total_y = sum(results[comp_name][j]["Y"] for j in keys)
        total_tie = sum(results[comp_name][j]["TIE"] for j in keys)
        total = total_x + total_y + total_tie
        
        if total > 0:
            print(f"  X wins: {total_x} ({total_x/total*100:.1f}%)")
            print(f"  Y wins: {total_y} ({total_y/total*100:.1f}%)")
            print(f"  Ties:   {total_tie} ({total_tie/total*100:.1f}%)")
        
        for jid in keys:
            jx = results[comp_name][jid]["X"]
            jy = results[comp_name][jid]["Y"]
            jt = results[comp_name][jid]["TIE"]
            je = results[comp_name][jid]["ERR"]
            jn = jx + jy + jt
            if jn > 0:
                print(f"    {jid}: X={jx}({jx/jn*100:.0f}%) Y={jy}({jy/jn*100:.0f}%) T={jt}({jt/jn*100:.0f}%) E={je}")
    
    # Key question: Does D beat B?
    print("\n" + "="*70)
    print("KEY FINDINGS")
    print("="*70)
    
    for comp_name, label in [
        ("A_vs_D", "Baseline Gemini vs Diverse Personas"),
        ("B_vs_D", "GPT-4o (better model) vs Diverse Personas"),
        ("C_vs_D", "Identical 3x vs Diverse 3x"),
        ("D_vs_E", "Same-model Personas vs Different-model Consensus"),
    ]:
        total_x = sum(results[comp_name][j]["X"] for j in keys)
        total_y = sum(results[comp_name][j]["Y"] for j in keys)
        total = total_x + total_y + sum(results[comp_name][j]["TIE"] for j in keys)
        if total > 0:
            y_pct = total_y / total * 100
            x_pct = total_x / total * 100
            winner = "Y (D)" if total_y > total_x else "X" if total_x > total_y else "TIE"
            print(f"  {label}: {winner} wins ({max(x_pct,y_pct):.1f}%)")


if __name__ == "__main__":
    asyncio.run(run())
