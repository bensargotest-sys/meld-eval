#!/usr/bin/env python3
"""T5: Mechanism Isolation — What actually creates the quality gain?

Conditions:
  B: GPT-4o single (control)
  E: Multi-model → GPT-4o synthesis (control)
  F: GPT-4o → GPT-4o self-refine
  G: Grok-3 single
  H: 3× different models → judge picks best (no synthesis)
  I: 3× Gemini → Gemini synthesis (cheap everything)
"""

import asyncio
import json
import os
import sys
import httpx
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


async def call_api(client, url, model, api_key, messages, max_tokens=MAX_TOKENS):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    body = {"model": model, "messages": messages, "max_tokens": max_tokens, "stream": False}
    try:
        resp = await client.post(url, json=body, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"


async def synthesize(client, question, responses, api_key, url=GPT4O_URL, model=GPT4O_MODEL):
    parts = "\n\n".join(f"Response {i+1}:\n{r}" for i, r in enumerate(responses))
    prompt = f"Synthesize these responses into one superior answer.\n\nQuestion: {question}\n\n{parts}\n\nProvide a single, superior synthesis."
    return await call_api(client, url, model, api_key, [{"role": "user", "content": prompt}])


async def pick_best(client, question, responses, api_key):
    """Judge picks the best of 3 responses (no synthesis)."""
    parts = "\n\n".join(f"Response {i+1}:\n{r}" for i, r in enumerate(responses))
    prompt = f"""Pick the single best response to this question. Output ONLY the full text of the best response, nothing else.

Question: {question}

{parts}

Best response:"""
    return await call_api(client, GPT4O_URL, GPT4O_MODEL, api_key, [{"role": "user", "content": prompt}])


async def run():
    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "t5_responses.jsonl"

    gemini_key = os.environ["GEMINI_API_KEY"]
    openai_key = os.environ["OPENAI_API_KEY"]
    xai_key = os.environ["XAI_API_KEY"]
    deepseek_key = os.environ["DEEPSEEK_API_KEY"]

    questions = [json.loads(l)["question"] for l in open("/tmp/t4_questions.jsonl")][:NUM_QUESTIONS]
    print(f"T5 Mechanism Isolation — {len(questions)} questions × 6 conditions")
    print(f"Output: {out_path}\n")

    async with httpx.AsyncClient() as client:
        for i, question in enumerate(questions):
            print(f"[{i+1}/{len(questions)}] {question[:60]}...")
            row = {"q_idx": i, "question": question}

            # B: GPT-4o single
            row["B"] = await call_api(client, GPT4O_URL, GPT4O_MODEL, openai_key,
                                      [{"role": "user", "content": question}])
            print(f"  B (GPT-4o): {len(row['B'])} chars")

            # F: GPT-4o self-refine (two-pass)
            first_pass = row["B"]  # reuse B as first pass
            refine_prompt = f"""Here is a question and your previous answer. Improve it — make it more accurate, thorough, and insightful.

Question: {question}

Your previous answer:
{first_pass}

Improved answer:"""
            row["F"] = await call_api(client, GPT4O_URL, GPT4O_MODEL, openai_key,
                                      [{"role": "user", "content": refine_prompt}])
            print(f"  F (self-refine): {len(row['F'])} chars")

            # G: Grok-3 single
            row["G"] = await call_api(client, GROK_URL, GROK_MODEL, xai_key,
                                      [{"role": "user", "content": question}])
            print(f"  G (Grok-3): {len(row['G'])} chars")

            # Get 3 model responses for E and H
            t_grok = call_api(client, GROK_URL, GROK_MODEL, xai_key,
                              [{"role": "user", "content": question}])
            t_gem = call_api(client, GEMINI_URL, GEMINI_MODEL, gemini_key,
                             [{"role": "user", "content": question}])
            t_ds = call_api(client, DEEPSEEK_URL, DEEPSEEK_MODEL, deepseek_key,
                            [{"role": "user", "content": question}])
            r_grok, r_gem, r_ds = await asyncio.gather(t_grok, t_gem, t_ds)
            multi_responses = [r_grok, r_gem, r_ds]
            row["E_raw"] = multi_responses

            # E: Multi-model → GPT-4o synthesis
            row["E"] = await synthesize(client, question, multi_responses, openai_key)
            print(f"  E (multi-model synth): {len(row['E'])} chars")

            # H: Best-of-3 selection (no synthesis)
            row["H"] = await pick_best(client, question, multi_responses, openai_key)
            print(f"  H (best-of-3): {len(row['H'])} chars")

            # Get 3 Gemini responses for I
            t1 = call_api(client, GEMINI_URL, GEMINI_MODEL, gemini_key,
                          [{"role": "user", "content": question}])
            t2 = call_api(client, GEMINI_URL, GEMINI_MODEL, gemini_key,
                          [{"role": "user", "content": question}])
            t3 = call_api(client, GEMINI_URL, GEMINI_MODEL, gemini_key,
                          [{"role": "user", "content": question}])
            gem_responses = list(await asyncio.gather(t1, t2, t3))

            # I: 3× Gemini → Gemini synthesis (cheap everything)
            row["I"] = await synthesize(client, question, gem_responses, gemini_key,
                                        url=GEMINI_URL, model=GEMINI_MODEL)
            print(f"  I (cheap synth): {len(row['I'])} chars")

            with open(out_path, "a") as f:
                f.write(json.dumps(row) + "\n")

        print(f"\n✅ T5 collection complete: {out_path}")


if __name__ == "__main__":
    asyncio.run(run())
