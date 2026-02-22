#!/usr/bin/env python3
"""
T2 Judging Pipeline — Pairwise evaluation with 3 judges and position-swap.

For each question, compare each condition (B/C/D/E) against baseline (A).
Each comparison is judged by 3 models, each with position-swap = 6 judgments per pair.
Total: 200 questions × 4 pairs × 3 judges × 2 swaps = 4,800 judge calls.

With 20 concurrent API calls, ~4s per call = ~16 min estimated.
"""

import json
import os
import sys
import time
import random
import re
import urllib.request
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
RESULTS_DIR = "/root/meld-eval/experiments/P1_mechanism/T2_anchoring_control/results"
RESPONSES_FILE = f"{RESULTS_DIR}/responses.jsonl"
JUDGMENTS_FILE = f"{RESULTS_DIR}/judgments.jsonl"
SCORES_FILE = f"{RESULTS_DIR}/scores.json"

JUDGE_MODELS = [
    "openai/gpt-4o",
    "mistralai/mistral-large-latest",
    "cohere/command-r-plus",
]

# Compare each condition against baseline A
COMPARISONS = [("A", "B"), ("A", "C"), ("A", "D"), ("A", "E")]

MAX_CONCURRENT = 20
semaphore = threading.Semaphore(MAX_CONCURRENT)
save_lock = threading.Lock()

JUDGE_PROMPT = """You are evaluating two responses to a question. Determine which is better.

IMPORTANT RULES:
- Do NOT favor longer responses. A concise, accurate answer beats a padded one.
- Evaluate: accuracy, reasoning quality, completeness, clarity, insight.
- If truly equal, say "tie".

Question:
{question}

Response A:
{response_a}

Response B:
{response_b}

Respond with JSON only:
{{"winner": "A" or "B" or "tie", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""


def call_judge(judge_model, question, resp_a, resp_b, retries=3):
    prompt = JUDGE_PROMPT.format(question=question, response_a=resp_a, response_b=resp_b)
    for attempt in range(retries + 1):
        try:
            with semaphore:
                payload = json.dumps({
                    "model": judge_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                }).encode()
                req = urllib.request.Request(
                    "https://openrouter.ai/api/v1/chat/completions",
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                    }
                )
                with urllib.request.urlopen(req, timeout=45) as resp:
                    data = json.loads(resp.read())
                raw = data["choices"][0]["message"]["content"]
                # Try to parse JSON from response (may have markdown wrapping)
                json_match = re.search(r'\{[^{}]*\}', raw)
                if json_match:
                    return json.loads(json_match.group())
                return {"winner": "tie", "confidence": 0.0, "reasoning": raw, "parse_error": True}
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt + random.random())
                continue
            return {"winner": "error", "confidence": 0.0, "reasoning": str(e), "error": True}


def judge_pair(question, resp_a, resp_b, judge_model, label_a, label_b):
    """Judge with position swap. Returns normalized winner (label_a or label_b or tie)."""
    # Normal order
    r1 = call_judge(judge_model, question, resp_a, resp_b)
    # Swapped order
    r2 = call_judge(judge_model, question, resp_b, resp_a)

    # Normalize r2 (swap winner back)
    if r2.get("winner") == "A":
        r2["winner"] = "B"
    elif r2.get("winner") == "B":
        r2["winner"] = "A"

    # Map A/B to condition labels
    def map_winner(w):
        if w == "A": return label_a
        if w == "B": return label_b
        return "tie"

    w1 = map_winner(r1.get("winner", "tie"))
    w2 = map_winner(r2.get("winner", "tie"))
    consistent = w1 == w2

    if consistent:
        final = w1
    else:
        final = "inconsistent"

    return {
        "judge": judge_model,
        "normal": {**r1, "mapped_winner": w1},
        "swapped": {**r2, "mapped_winner": w2},
        "consistent": consistent,
        "final_winner": final,
    }


def process_one_question(qi, qdata):
    """Run all comparisons × all judges for one question."""
    q = qdata["question"]
    conditions = qdata["conditions"]
    results = []

    for label_a, label_b in COMPARISONS:
        cond_a = conditions.get(label_a, {})
        cond_b = conditions.get(label_b, {})
        resp_a = cond_a.get("response", "")
        resp_b = cond_b.get("response", "")

        if not resp_a or not resp_b:
            continue

        # Run 3 judges in parallel
        judge_results = []
        with ThreadPoolExecutor(max_workers=3) as pool:
            futs = {pool.submit(judge_pair, q, resp_a, resp_b, jm, label_a, label_b): jm for jm in JUDGE_MODELS}
            for fut in as_completed(futs):
                jm = futs[fut]
                jr = fut.result()
                judge_results.append(jr)

        results.append({
            "qi": qi,
            "qid": qdata.get("qid", ""),
            "category": qdata.get("category", ""),
            "comparison": f"{label_a}_vs_{label_b}",
            "judges": judge_results,
        })

    return results


def compute_scores(all_judgments):
    """Compute win rates for each condition vs baseline A."""
    scores = {}
    for comp_label in ["A_vs_B", "A_vs_C", "A_vs_D", "A_vs_E"]:
        cond = comp_label.split("_vs_")[1]
        wins_a = 0
        wins_cond = 0
        ties = 0
        inconsistent = 0
        total = 0

        by_category = {}

        for j in all_judgments:
            if j["comparison"] != comp_label:
                continue
            cat = j.get("category", "?")
            if cat not in by_category:
                by_category[cat] = {"a": 0, "cond": 0, "tie": 0, "incon": 0}

            for jr in j["judges"]:
                total += 1
                fw = jr["final_winner"]
                if fw == "A":
                    wins_a += 1
                    by_category[cat]["a"] += 1
                elif fw == cond:
                    wins_cond += 1
                    by_category[cat]["cond"] += 1
                elif fw == "tie":
                    ties += 1
                    by_category[cat]["tie"] += 1
                elif fw == "inconsistent":
                    inconsistent += 1
                    by_category[cat]["incon"] += 1

        win_rate = wins_cond / max(1, total) * 100
        scores[comp_label] = {
            "condition": cond,
            "wins_baseline": wins_a,
            "wins_condition": wins_cond,
            "ties": ties,
            "inconsistent": inconsistent,
            "total_judgments": total,
            "win_rate_pct": round(win_rate, 1),
            "by_category": by_category,
        }

    return scores


def main():
    # Load responses
    with open(RESPONSES_FILE) as f:
        questions = [json.loads(line) for line in f if line.strip()]
    print(f"Loaded {len(questions)} questions with responses", flush=True)
    print(f"Judges: {JUDGE_MODELS}", flush=True)
    print(f"Comparisons: {COMPARISONS}", flush=True)
    print(f"Total judge calls: {len(questions)} × {len(COMPARISONS)} × {len(JUDGE_MODELS)} × 2 = {len(questions)*len(COMPARISONS)*len(JUDGE_MODELS)*2}", flush=True)

    all_judgments = []
    started = datetime.now(timezone.utc).isoformat()

    # Process 10 questions at a time
    BATCH = 10
    for batch_start in range(0, len(questions), BATCH):
        batch_end = min(batch_start + BATCH, len(questions))

        with ThreadPoolExecutor(max_workers=BATCH) as pool:
            futs = {pool.submit(process_one_question, i, questions[i]): i for i in range(batch_start, batch_end)}
            for fut in as_completed(futs):
                idx = futs[fut]
                results = fut.result()
                all_judgments.extend(results)

        done = min(batch_end, len(questions))
        print(f">>> Judged {done}/{len(questions)} questions ({len(all_judgments)} total judgments)", flush=True)

        # Incremental save
        with save_lock:
            with open(f"{RESULTS_DIR}/judgments_partial.jsonl", "w") as f:
                for j in all_judgments:
                    f.write(json.dumps(j) + "\n")

    # Final save
    with open(JUDGMENTS_FILE, "w") as f:
        for j in all_judgments:
            f.write(json.dumps(j) + "\n")

    # Compute scores
    scores = compute_scores(all_judgments)
    scores["_meta"] = {
        "test": "T2",
        "started_at": started,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "n_questions": len(questions),
        "judge_models": JUDGE_MODELS,
        "comparisons": [f"{a}_vs_{b}" for a, b in COMPARISONS],
        "total_judgments": len(all_judgments) * 3,  # 3 judges per comparison
    }

    with open(SCORES_FILE, "w") as f:
        json.dump(scores, f, indent=2)

    # Print summary
    print(f"\n{'='*60}", flush=True)
    print(f"T2 JUDGING COMPLETE", flush=True)
    print(f"{'='*60}", flush=True)
    for comp, data in scores.items():
        if comp.startswith("_"):
            continue
        print(f"\n{comp}:", flush=True)
        print(f"  Baseline (A) wins: {data['wins_baseline']}", flush=True)
        print(f"  Condition {data['condition']} wins: {data['wins_condition']} ({data['win_rate_pct']}%)", flush=True)
        print(f"  Ties: {data['ties']}, Inconsistent: {data['inconsistent']}", flush=True)

    print(f"\nResults: {SCORES_FILE}", flush=True)

if __name__ == "__main__":
    main()
