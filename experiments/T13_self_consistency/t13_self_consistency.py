#!/usr/bin/env python3
"""T13: Self-Consistency vs Network Consensus

Does sampling the same model multiple times match multi-model consensus?
This is the strongest counter-argument to MELD: "just call GPT-4o 3 times."

Conditions:
  A: GPT-4o single (temp=0, deterministic baseline)
  B: GPT-4o × 3 (temp=1) → GPT-4o synthesis
  C: GPT-4o × 3 (temp=1) → GPT-4o picks best (selection)
  D: 3 different models (temp=0) → GPT-4o synthesis (MELD pattern)
  E: GPT-4o × 3 (temp=0) → GPT-4o synthesis (are deterministic outputs even different?)
"""

import asyncio, json, os, sys, httpx
from pathlib import Path

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
GEMINI_MODEL = "gemini-2.0-flash"
GPT4O_URL = "https://api.openai.com/v1/chat/completions"
GPT4O_MODEL = "gpt-4o"
GROK_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-3"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

MAX_TOKENS = 512
TIMEOUT = 60.0
NUM_QUESTIONS = 50


async def call_api(client, url, model, api_key, messages, max_tokens=MAX_TOKENS, temperature=None):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    body = {"model": model, "messages": messages, "max_tokens": max_tokens, "stream": False}
    if temperature is not None:
        body["temperature"] = temperature
    try:
        resp = await client.post(url, json=body, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"


async def synthesize(client, question, responses, api_key):
    parts = "\n\n".join(f"Response {i+1}:\n{r}" for i, r in enumerate(responses))
    prompt = f"Synthesize these responses into one superior answer.\n\nQuestion: {question}\n\n{parts}\n\nProvide a single, superior synthesis."
    return await call_api(client, GPT4O_URL, GPT4O_MODEL, api_key,
                          [{"role": "user", "content": prompt}], temperature=0)


async def pick_best(client, question, responses, api_key):
    parts = "\n\n".join(f"Response {i+1}:\n{r}" for i, r in enumerate(responses))
    prompt = f"""Pick the single best response. Output ONLY the full text of the best response, nothing else.

Question: {question}

{parts}

Best response:"""
    return await call_api(client, GPT4O_URL, GPT4O_MODEL, api_key,
                          [{"role": "user", "content": prompt}], temperature=0)


async def run():
    out_dir = Path("/tmp/results")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "t13_responses.jsonl"
    if out_path.exists():
        done = sum(1 for _ in open(out_path))
        print(f"Resuming from question {done}")
    else:
        done = 0

    keys = {
        "gemini": os.environ["GEMINI_API_KEY"],
        "openai": os.environ["OPENAI_API_KEY"],
        "xai": os.environ.get("XAI_API_KEY"),
        "deepseek": os.environ["DEEPSEEK_API_KEY"],
    }

    questions = [json.loads(l)["question"] for l in open("/tmp/t4_questions.jsonl")][:NUM_QUESTIONS]
    print(f"T13 Self-Consistency vs Network — {len(questions)} questions × 5 conditions")

    async with httpx.AsyncClient() as client:
        for i, question in enumerate(questions):
            if i < done:
                continue
            print(f"[{i+1}/{len(questions)}] {question[:60]}...")
            row = {"q_idx": i, "question": question}
            msgs = [{"role": "user", "content": question}]

            # A: GPT-4o single, temp=0
            row["A"] = await call_api(client, GPT4O_URL, GPT4O_MODEL, keys["openai"], msgs, temperature=0)
            print(f"  A (single t=0): {len(row['A'])} chars")

            # B: GPT-4o × 3, temp=1, synthesized
            t1 = call_api(client, GPT4O_URL, GPT4O_MODEL, keys["openai"], msgs, temperature=1)
            t2 = call_api(client, GPT4O_URL, GPT4O_MODEL, keys["openai"], msgs, temperature=1)
            t3 = call_api(client, GPT4O_URL, GPT4O_MODEL, keys["openai"], msgs, temperature=1)
            b_resps = list(await asyncio.gather(t1, t2, t3))
            row["B"] = await synthesize(client, question, b_resps, keys["openai"])
            row["B_diversity"] = len(set(r[:50] for r in b_resps))  # crude diversity check
            print(f"  B (3×t=1 synth): {len(row['B'])} chars, diversity={row['B_diversity']}/3")

            # C: GPT-4o × 3, temp=1, pick best
            row["C"] = await pick_best(client, question, b_resps, keys["openai"])
            print(f"  C (3×t=1 pick): {len(row['C'])} chars")

            # D: 3 different models, temp=0, synthesized (MELD pattern)
            t_grok = call_api(client, GROK_URL, GROK_MODEL, keys["xai"], msgs, temperature=0)
            t_gem = call_api(client, GEMINI_URL, GEMINI_MODEL, keys["gemini"], msgs, temperature=0)
            t_ds = call_api(client, DEEPSEEK_URL, DEEPSEEK_MODEL, keys["deepseek"], msgs, temperature=0)
            d_resps = list(await asyncio.gather(t_grok, t_gem, t_ds))
            row["D"] = await synthesize(client, question, d_resps, keys["openai"])
            row["D_diversity"] = len(set(r[:50] for r in d_resps))
            print(f"  D (multi-model synth): {len(row['D'])} chars, diversity={row['D_diversity']}/3")

            # E: GPT-4o × 3, temp=0, synthesized (are they even different?)
            t1 = call_api(client, GPT4O_URL, GPT4O_MODEL, keys["openai"], msgs, temperature=0)
            t2 = call_api(client, GPT4O_URL, GPT4O_MODEL, keys["openai"], msgs, temperature=0)
            t3 = call_api(client, GPT4O_URL, GPT4O_MODEL, keys["openai"], msgs, temperature=0)
            e_resps = list(await asyncio.gather(t1, t2, t3))
            row["E"] = await synthesize(client, question, e_resps, keys["openai"])
            row["E_diversity"] = len(set(r[:50] for r in e_resps))
            print(f"  E (3×t=0 synth): {len(row['E'])} chars, diversity={row['E_diversity']}/3")

            with open(out_path, "a") as f:
                f.write(json.dumps(row) + "\n")

    print(f"\n✅ T13 collection complete: {out_path}")


if __name__ == "__main__":
    asyncio.run(run())
