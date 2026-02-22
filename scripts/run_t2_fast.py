#!/usr/bin/env python3
"""
T2 — Anchoring Bias Controlled Experiment (FAST parallel version)
200 questions × 5 conditions (A-E)
Parallelizes across questions AND across conditions within each question.
"""

import json
import os
import sys
import time
import random
import hashlib
import urllib.request
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
RESULTS_DIR = "/root/meld-eval/experiments/P1_mechanism/T2_anchoring_control/results"
QUESTIONS_FILE = "/root/meld-eval/configs/test_sets/candidates_prescreened.jsonl"

NODE_MODELS = [
    {"id": "meld-2", "model": "x-ai/grok-3"},
    {"id": "meld-3", "model": "google/gemini-2.0-flash-001"},
    {"id": "meld-4", "model": "deepseek/deepseek-chat"},
]
SOLO_MODEL = "openai/gpt-4o-mini"
SYNTHESIS_MODEL = "openai/gpt-4o-mini"
N_QUESTIONS = 200

# Rate limiting: max concurrent OpenRouter calls
MAX_CONCURRENT = 15
semaphore = threading.Semaphore(MAX_CONCURRENT)
save_lock = threading.Lock()

random.seed(42)

def load_questions():
    with open(QUESTIONS_FILE) as f:
        all_qs = [json.loads(line) for line in f if line.strip()]
    return random.sample(all_qs, min(N_QUESTIONS, len(all_qs)))

def qhash(q):
    return hashlib.sha256(q.encode()).hexdigest()[:12]

def call_model(model, messages, max_tokens=800, retries=3):
    for attempt in range(retries + 1):
        try:
            with semaphore:
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
                with urllib.request.urlopen(req, timeout=90) as resp:
                    data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt + random.random())
                continue
            raise

def condition_a(question):
    t0 = time.time()
    r = call_model(SOLO_MODEL, [{"role": "user", "content": question}])
    return {"condition": "A", "response": r, "model": SOLO_MODEL, "ms": int((time.time()-t0)*1000)}

def condition_b(question):
    t0 = time.time()
    responses = []
    for node in NODE_MODELS:
        if not responses:
            r = call_model(node["model"], [{"role": "user", "content": question}])
        else:
            r = call_model(node["model"], [
                {"role": "user", "content": question},
                {"role": "assistant", "content": responses[-1]["response"]},
                {"role": "user", "content": "Building on the previous analysis, provide your own perspective."},
            ])
        responses.append({"node": node["id"], "model": node["model"], "response": r})
    synth = call_model(SYNTHESIS_MODEL, [{"role": "user", "content":
        f"Question: {question}\n\n" +
        "".join(f"--- {r['model']} ---\n{r['response']}\n\n" for r in responses) +
        "Synthesize the best answer combining insights from all analyses."
    }])
    return {"condition": "B", "individual": responses, "response": synth, "ms": int((time.time()-t0)*1000)}

def condition_c(question):
    t0 = time.time()
    # Parallel collection
    responses = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(call_model, n["model"], [{"role": "user", "content": question}]): n for n in NODE_MODELS}
        for fut in as_completed(futs):
            node = futs[fut]
            responses.append({"node": node["id"], "model": node["model"], "response": fut.result()})
    random.shuffle(responses)
    synth = call_model(SYNTHESIS_MODEL, [{"role": "user", "content":
        f"Question: {question}\n\n" +
        "".join(f"--- Source {i+1} ---\n{r['response']}\n\n" for i, r in enumerate(responses)) +
        "Synthesize the best answer. Evaluate each source on its merits regardless of order."
    }])
    return {"condition": "C", "individual": responses, "order": [r["node"] for r in responses],
            "response": synth, "ms": int((time.time()-t0)*1000)}

def condition_d(question):
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
    t0 = time.time()
    chain = []
    r1 = call_model(NODE_MODELS[0]["model"], [{"role": "user", "content": question}])
    chain.append({"node": NODE_MODELS[0]["id"], "model": NODE_MODELS[0]["model"], "role": "initial", "response": r1})
    r2 = call_model(NODE_MODELS[1]["model"], [{"role": "user", "content":
        f"Original question: {question}\n\nA previous model answered:\n{r1}\n\n"
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

CONDITIONS = [("A", condition_a), ("B", condition_b), ("C", condition_c), ("D", condition_d), ("E", condition_e)]

def run_one_question(i, qobj):
    q = qobj["question"]
    cat = qobj.get("category", "?")
    qid = qhash(q)
    result = {"qid": qid, "qi": i, "question": q, "category": cat, "conditions": {}, "ts": datetime.now(timezone.utc).isoformat()}

    # Run A, C, D in parallel (independent). B, E are sequential so run after.
    parallel_conds = [("A", condition_a), ("C", condition_c), ("D", condition_d)]
    sequential_conds = [("B", condition_b), ("E", condition_e)]

    # Parallel batch
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(func, q): label for label, func in parallel_conds}
        for fut in as_completed(futs):
            label = futs[fut]
            try:
                r = fut.result()
                result["conditions"][label] = r
            except Exception as e:
                result["conditions"][label] = {"condition": label, "error": str(e)}

    # Sequential batch
    for label, func in sequential_conds:
        try:
            r = func(q)
            result["conditions"][label] = r
        except Exception as e:
            result["conditions"][label] = {"condition": label, "error": str(e)}

    ok = sum(1 for c in result["conditions"].values() if "error" not in c)
    err = 5 - ok
    print(f"[{i+1}/{N_QUESTIONS}] {cat}: {q[:50]}... {ok}/5 ok", flush=True)
    return result

def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    questions = load_questions()
    cats = {}
    for q in questions:
        cats[q.get("category", "?")] = cats.get(q.get("category", "?"), 0) + 1
    print(f"Loaded {len(questions)} questions: {json.dumps(cats)}", flush=True)
    print(f"Max concurrent API calls: {MAX_CONCURRENT}", flush=True)
    print(f"Parallelizing: A/C/D concurrent per question, 5 questions at a time", flush=True)

    all_results = [None] * len(questions)
    started = datetime.now(timezone.utc).isoformat()
    completed_count = 0

    # Process 5 questions at a time
    BATCH_SIZE = 5
    for batch_start in range(0, len(questions), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(questions))
        batch = list(range(batch_start, batch_end))

        with ThreadPoolExecutor(max_workers=BATCH_SIZE) as pool:
            futs = {pool.submit(run_one_question, i, questions[i]): i for i in batch}
            for fut in as_completed(futs):
                idx = futs[fut]
                try:
                    all_results[idx] = fut.result()
                except Exception as e:
                    all_results[idx] = {"qi": idx, "error": str(e)}
                completed_count += 1

        # Save after each batch
        with save_lock:
            with open(f"{RESULTS_DIR}/responses_partial.jsonl", "w") as f:
                for r in all_results:
                    if r is not None:
                        f.write(json.dumps(r) + "\n")
        print(f">>> Batch saved: {completed_count}/{len(questions)} complete", flush=True)

    # Final save
    final_results = [r for r in all_results if r is not None]
    with open(f"{RESULTS_DIR}/responses.jsonl", "w") as f:
        for r in final_results:
            f.write(json.dumps(r) + "\n")

    ok = {c: 0 for c in "ABCDE"}
    errors = {c: 0 for c in "ABCDE"}
    for r in final_results:
        for c in "ABCDE":
            cond = r.get("conditions", {}).get(c, {})
            if "error" in cond:
                errors[c] += 1
            elif cond:
                ok[c] += 1

    metrics = {
        "test": "T2", "n_questions": len(final_results), "n_conditions": 5,
        "started_at": started, "completed_at": datetime.now(timezone.utc).isoformat(),
        "ok": ok, "errors": errors, "categories": cats,
        "solo_model": SOLO_MODEL, "synthesis_model": SYNTHESIS_MODEL,
        "node_models": [n["model"] for n in NODE_MODELS],
        "parallelism": {"max_concurrent_api": MAX_CONCURRENT, "batch_size": BATCH_SIZE},
    }
    with open(f"{RESULTS_DIR}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n{'='*60}", flush=True)
    print(f"T2 COMPLETE: {len(final_results)} questions × 5 conditions", flush=True)
    print(f"OK: {ok}", flush=True)
    print(f"Errors: {errors}", flush=True)

if __name__ == "__main__":
    main()
