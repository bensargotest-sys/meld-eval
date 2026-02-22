#!/usr/bin/env python3
"""
T2 — Anchoring Bias Controlled Experiment
200 questions × 5 conditions (A-E)

Conditions:
  A: Solo (single model, no network) — baseline
  B: Giga Brain standard sequential synthesis
  C: Giga Brain with anchoring control (randomized order, anonymized)
  D: Independent nodes, different models (parallel, then synthesize)
  E: Sequential-adversarial (critique → correction → extension)

Models called via OpenRouter to match MELD node models exactly.
This tests the METHODOLOGY (synthesis patterns), not the credit system.
"""

import json
import os
import sys
import time
import random
import hashlib
import urllib.request
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
RESULTS_DIR = "/root/meld-eval/experiments/P1_mechanism/T2_anchoring_control/results"
QUESTIONS_FILE = "/root/meld-eval/configs/test_sets/candidates_prescreened.jsonl"

# Models matching MELD nodes
NODE_MODELS = [
    {"id": "meld-2", "model": "x-ai/grok-3"},
    {"id": "meld-3", "model": "google/gemini-2.0-flash-001"},
    {"id": "meld-4", "model": "deepseek/deepseek-chat"},
]
SOLO_MODEL = "openai/gpt-4o-mini"
SYNTHESIS_MODEL = "openai/gpt-4o-mini"
N_QUESTIONS = 200

random.seed(42)

def load_questions():
    with open(QUESTIONS_FILE) as f:
        all_qs = [json.loads(line) for line in f if line.strip()]
    return random.sample(all_qs, min(N_QUESTIONS, len(all_qs)))

def qhash(q):
    return hashlib.sha256(q.encode()).hexdigest()[:12]

def call_model(model, messages, max_tokens=800, retries=2):
    for attempt in range(retries + 1):
        try:
            payload = json.dumps({
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
            }).encode()
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                }
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise

def condition_a(question):
    """Solo baseline — single model, no network."""
    t0 = time.time()
    r = call_model(SOLO_MODEL, [{"role": "user", "content": question}])
    return {"condition": "A", "response": r, "model": SOLO_MODEL, "ms": int((time.time()-t0)*1000)}

def condition_b(question):
    """Standard sequential Giga Brain — each sees prior response."""
    t0 = time.time()
    responses = []
    for node in NODE_MODELS:
        if not responses:
            r = call_model(node["model"], [{"role": "user", "content": question}])
        else:
            r = call_model(node["model"], [
                {"role": "user", "content": question},
                {"role": "assistant", "content": responses[-1]["response"]},
                {"role": "user", "content": f"Building on the previous analysis, provide your own perspective on this question."},
            ])
        responses.append({"node": node["id"], "model": node["model"], "response": r})

    synth = call_model(SYNTHESIS_MODEL, [{"role": "user", "content":
        f"Question: {question}\n\n" +
        "".join(f"--- {r['model']} ---\n{r['response']}\n\n" for r in responses) +
        "Synthesize the best answer combining insights from all analyses."
    }])
    return {"condition": "B", "individual": responses, "response": synth, "ms": int((time.time()-t0)*1000)}

def condition_c(question):
    """Anchoring control — parallel collection, randomized+anonymized synthesis."""
    t0 = time.time()
    responses = []
    for node in NODE_MODELS:
        r = call_model(node["model"], [{"role": "user", "content": question}])
        responses.append({"node": node["id"], "model": node["model"], "response": r})

    shuffled = responses.copy()
    random.shuffle(shuffled)

    synth = call_model(SYNTHESIS_MODEL, [{"role": "user", "content":
        f"Question: {question}\n\n" +
        "".join(f"--- Source {i+1} ---\n{r['response']}\n\n" for i, r in enumerate(shuffled)) +
        "Synthesize the best answer. Evaluate each source on its merits regardless of order."
    }])
    return {"condition": "C", "individual": responses, "order": [r["node"] for r in shuffled],
            "response": synth, "ms": int((time.time()-t0)*1000)}

def condition_d(question):
    """Independent parallel — truly parallel, then synthesize."""
    t0 = time.time()
    responses = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(call_model, n["model"], [{"role": "user", "content": question}]): n for n in NODE_MODELS}
        for fut in as_completed(futs):
            node = futs[fut]
            responses[node["id"]] = {"node": node["id"], "model": node["model"], "response": fut.result()}

    synth = call_model(SYNTHESIS_MODEL, [{"role": "user", "content":
        f"Question: {question}\n\nThree independent AI models answered without seeing each other's responses:\n\n" +
        "".join(f"--- {r['model']} ---\n{r['response']}\n\n" for r in responses.values()) +
        "Synthesize the best answer combining unique insights from each independent perspective."
    }])
    return {"condition": "D", "individual": list(responses.values()), "response": synth,
            "ms": int((time.time()-t0)*1000)}

def condition_e(question):
    """Sequential-adversarial: critique → correction → extension."""
    t0 = time.time()
    chain = []

    r1 = call_model(NODE_MODELS[0]["model"], [{"role": "user", "content": question}])
    chain.append({"node": NODE_MODELS[0]["id"], "model": NODE_MODELS[0]["model"], "role": "initial", "response": r1})

    r2 = call_model(NODE_MODELS[1]["model"], [{"role": "user", "content":
        f"Original question: {question}\n\nA previous model gave this answer:\n{r1}\n\n"
        f"Your task:\n1. Identify specific weaknesses, errors, or gaps\n"
        f"2. Correct any errors\n3. Extend with additional insights\n"
        f"Structure: CRITIQUE: ... CORRECTION: ... EXTENSION: ..."
    }])
    chain.append({"node": NODE_MODELS[1]["id"], "model": NODE_MODELS[1]["model"], "role": "critique", "response": r2})

    r3 = call_model(NODE_MODELS[2]["model"], [{"role": "user", "content":
        f"Original question: {question}\n\nFirst answer:\n{r1}\n\nCritique and extension:\n{r2}\n\n"
        f"Review both. Identify remaining weaknesses. Produce the definitive final answer."
    }])
    chain.append({"node": NODE_MODELS[2]["id"], "model": NODE_MODELS[2]["model"], "role": "final", "response": r3})

    return {"condition": "E", "chain": chain, "response": r3, "ms": int((time.time()-t0)*1000)}

CONDITIONS = [
    ("A", condition_a),
    ("B", condition_b),
    ("C", condition_c),
    ("D", condition_d),
    ("E", condition_e),
]

def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    questions = load_questions()

    cats = {}
    for q in questions:
        cats[q.get("category", "?")] = cats.get(q.get("category", "?"), 0) + 1
    print(f"Loaded {len(questions)} questions: {json.dumps(cats)}")

    all_results = []
    started = datetime.utcnow().isoformat()
    errors = {c: 0 for c in "ABCDE"}
    ok = {c: 0 for c in "ABCDE"}

    for i, qobj in enumerate(questions):
        q = qobj["question"]
        cat = qobj.get("category", "?")
        qid = qhash(q)
        result = {"qid": qid, "qi": i, "question": q, "category": cat, "conditions": {}, "ts": datetime.utcnow().isoformat()}

        print(f"[{i+1}/{len(questions)}] {cat}: {q[:60]}...", flush=True)

        for label, func in CONDITIONS:
            try:
                r = func(q)
                result["conditions"][label] = r
                ok[label] += 1
                print(f"  {label} ✓ {r['ms']}ms", flush=True)
            except Exception as e:
                result["conditions"][label] = {"condition": label, "error": str(e)}
                errors[label] += 1
                print(f"  {label} ✗ {e}", flush=True)
            time.sleep(0.2)

        all_results.append(result)

        # Incremental save every 5 questions
        if (i + 1) % 5 == 0:
            with open(f"{RESULTS_DIR}/responses_partial.jsonl", "w") as f:
                for r in all_results:
                    f.write(json.dumps(r) + "\n")
            print(f"  >>> Saved {i+1}/{len(questions)}", flush=True)

    # Final save
    with open(f"{RESULTS_DIR}/responses.jsonl", "w") as f:
        for r in all_results:
            f.write(json.dumps(r) + "\n")

    metrics = {
        "test": "T2", "n_questions": len(questions), "n_conditions": 5,
        "started_at": started, "completed_at": datetime.utcnow().isoformat(),
        "ok": ok, "errors": errors, "categories": cats,
        "solo_model": SOLO_MODEL, "synthesis_model": SYNTHESIS_MODEL,
        "node_models": [n["model"] for n in NODE_MODELS],
    }
    with open(f"{RESULTS_DIR}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n{'='*60}")
    print(f"T2 COMPLETE: {len(questions)} questions × 5 conditions")
    print(f"OK: {ok}")
    print(f"Errors: {errors}")
    print(f"Results: {RESULTS_DIR}/responses.jsonl")

if __name__ == "__main__":
    main()
