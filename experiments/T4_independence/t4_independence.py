#!/usr/bin/env python3
"""T4: Independence vs Access — Does same-model diverse perspectives beat better single model?

Conditions:
  A: Single Gemini Flash (baseline)
  B: Single GPT-4o (better model access)
  C: 3× Gemini Flash identical prompts → synthesize (no independence)
  D: 3× Gemini Flash diverse personas → synthesize (independence with same model)
  E: Grok-3 + Gemini + DeepSeek → synthesize (different models, from T2)

If D > B → independence is more valuable than model access (MELD's moat)
If D < B → just upgrading models is better (OpenRouter commoditizes this)
If C ≈ A → multiple identical calls add no value
"""

import asyncio
import json
import os
import sys
import httpx
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_KEY_ENV = "GEMINI_API_KEY"

GPT4O_URL = "https://api.openai.com/v1/chat/completions"
GPT4O_MODEL = "gpt-4o"
OPENAI_KEY_ENV = "OPENAI_API_KEY"

GROK_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-3"
XAI_KEY_ENV = "XAI_API_KEY"

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_KEY_ENV = "DEEPSEEK_API_KEY"

PERSONAS = {
    "analyst": "You are a rigorous analytical thinker. Break problems into components, evaluate evidence systematically, identify assumptions.",
    "creative": "You are a creative lateral thinker. Find unexpected connections, challenge conventional wisdom, explore edge cases.",
    "pragmatic": "You are a pragmatic operator. Focus on what works in practice, prioritize actionable insights, cut through theory."
}

MAX_TOKENS = 512
TIMEOUT = 60.0
NUM_QUESTIONS = 100

# ── Load questions from T2 candidates ───────────────────────────────────
def load_questions(path="/tmp/t4_questions.jsonl"):
    """Load first NUM_QUESTIONS from T2 candidate set."""
    questions = []
    with open(path) as f:
        for line in f:
            if len(questions) >= NUM_QUESTIONS:
                break
            data = json.loads(line)
            questions.append(data["question"])
    return questions


# ── API calls ───────────────────────────────────────────────────────────
async def call_openai_compat(client, url, model, api_key, system_prompt, user_prompt, max_tokens=MAX_TOKENS):
    """Call OpenAI-compatible endpoint."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": False,
    }
    
    try:
        resp = await client.post(url, json=body, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        return text
    except Exception as e:
        return f"ERROR: {e}"


async def synthesize(client, question, responses, synthesis_key):
    """Synthesize multiple responses."""
    parts = [f"Response {i+1}:\n{r}\n" for i, r in enumerate(responses)]
    prompt = f"""Synthesize these responses into one superior answer.

Question: {question}

{''.join(parts)}

Provide a single, superior synthesis that captures the best insights from all responses."""

    return await call_openai_compat(
        client, GPT4O_URL, GPT4O_MODEL, synthesis_key, None, prompt, max_tokens=MAX_TOKENS
    )


# ── Main ────────────────────────────────────────────────────────────────
async def run():
    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "t4_responses.jsonl"
    
    # Load API keys
    gemini_key = os.environ.get(GEMINI_KEY_ENV)
    openai_key = os.environ.get(OPENAI_KEY_ENV)
    xai_key = os.environ.get(XAI_KEY_ENV)
    deepseek_key = os.environ.get(DEEPSEEK_KEY_ENV)
    
    if not all([gemini_key, openai_key, xai_key, deepseek_key]):
        print("ERROR: Missing API keys")
        sys.exit(1)
    
    questions = load_questions()
    print(f"T4 Independence Test — {len(questions)} questions × 5 conditions")
    print(f"Output: {out_path}\n")

    async with httpx.AsyncClient() as client:
        for i, question in enumerate(questions):
            print(f"[{i+1}/{len(questions)}] {question[:60]}...")
            row = {"q_idx": i, "question": question}
            
            # Condition A: Single Gemini Flash
            resp_a = await call_openai_compat(
                client, GEMINI_URL, GEMINI_MODEL, gemini_key, None, question
            )
            row["A_single_gemini"] = resp_a
            print(f"  A (Gemini): {len(resp_a)} chars")
            
            # Condition B: Single GPT-4o
            resp_b = await call_openai_compat(
                client, GPT4O_URL, GPT4O_MODEL, openai_key, None, question
            )
            row["B_single_gpt4o"] = resp_b
            print(f"  B (GPT-4o): {len(resp_b)} chars")
            
            # Condition C: 3× Gemini Flash, same prompt (no persona)
            tasks_c = [
                call_openai_compat(client, GEMINI_URL, GEMINI_MODEL, gemini_key, None, question)
                for _ in range(3)
            ]
            resps_c = await asyncio.gather(*tasks_c)
            synth_c = await synthesize(client, question, resps_c, openai_key)
            row["C_same_model_same_prompt"] = synth_c
            row["C_raw"] = resps_c
            print(f"  C (3× Gemini identical): {len(synth_c)} chars")
            
            # Condition D: 3× Gemini Flash, different personas
            tasks_d = []
            for persona_name, persona_sys in PERSONAS.items():
                tasks_d.append(
                    call_openai_compat(client, GEMINI_URL, GEMINI_MODEL, gemini_key, persona_sys, question)
                )
            resps_d = await asyncio.gather(*tasks_d)
            synth_d = await synthesize(client, question, resps_d, openai_key)
            row["D_same_model_diff_personas"] = synth_d
            row["D_raw"] = resps_d
            print(f"  D (3× Gemini personas): {len(synth_d)} chars")
            
            # Condition E: Different models (Grok-3, Gemini, DeepSeek)
            task_grok = call_openai_compat(client, GROK_URL, GROK_MODEL, xai_key, None, question)
            task_gemini = call_openai_compat(client, GEMINI_URL, GEMINI_MODEL, gemini_key, None, question)
            task_deepseek = call_openai_compat(client, DEEPSEEK_URL, DEEPSEEK_MODEL, deepseek_key, None, question)
            
            resps_e = await asyncio.gather(task_grok, task_gemini, task_deepseek)
            synth_e = await synthesize(client, question, resps_e, openai_key)
            row["E_different_models"] = synth_e
            row["E_raw"] = resps_e
            print(f"  E (Grok+Gemini+DeepSeek): {len(synth_e)} chars")
            
            # Write incrementally
            with open(out_path, "a") as f:
                f.write(json.dumps(row) + "\n")
        
        print(f"\n✅ Collection complete: {out_path}")
        print(f"Next: Run judging on these {len(questions)} responses")


if __name__ == "__main__":
    asyncio.run(run())
