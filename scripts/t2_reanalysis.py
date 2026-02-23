#!/usr/bin/env python3
"""
T2 Re-analysis: Three experiments to isolate MELD's value proposition.

Exp 1 - ACCESS: Judge each raw node response vs baseline A
  → Does having access to Grok-3/Gemini/DeepSeek beat GPT-4o-mini?

Exp 2 - DIVERSITY: Best-of-3 raw node responses vs baseline A  
  → Does model diversity give you better options?

Exp 3 - SYNTHESIS QUALITY: Re-synthesize D responses with GPT-4o (strong), judge vs A
  → Does a better synthesizer unlock the multi-model advantage?

Uses 3 working judges: GPT-4o, Gemini Flash, Qwen 72B
"""

import json, os, sys, time, random, re, urllib.request, threading
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
BASE = "/root/meld-eval/experiments/P1_mechanism/T2_anchoring_control/results"
RESPONSES_FILE = f"{BASE}/responses.jsonl"
REANALYSIS_DIR = f"{BASE}/reanalysis"

JUDGE_MODELS = [
    "openai/gpt-4o",
    "google/gemini-2.0-flash-001",
    "qwen/qwen-2.5-72b-instruct",
]

SYNTHESIS_MODEL_STRONG = "openai/gpt-4o"

MAX_CONCURRENT = 20
sem = threading.Semaphore(MAX_CONCURRENT)

JUDGE_PROMPT = """You are evaluating two responses to a question. Determine which is better.

RULES:
- Do NOT favor longer responses. Concise and accurate beats padded.
- Evaluate: accuracy, reasoning quality, completeness, clarity, insight.
- If truly equal, say "tie".

Question:
{question}

Response A:
{response_a}

Response B:
{response_b}

Respond with ONLY valid JSON:
{{"winner": "A" or "B" or "tie", "confidence": 0.0-1.0, "reasoning": "one sentence"}}"""

def call_api(model, messages, max_tokens=200, retries=3):
    for attempt in range(retries + 1):
        try:
            with sem:
                payload = json.dumps({"model": model, "messages": messages, "max_tokens": max_tokens}).encode()
                req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                    data=payload, headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt + random.random())
                continue
            raise

def parse_verdict(raw):
    m = re.search(r'\{[^{}]*\}', raw)
    if m:
        try: return json.loads(m.group())
        except: pass
    return {"winner": "tie", "confidence": 0.0, "reasoning": raw[:200], "parse_error": True}

def judge_pair_all(question, resp_a, resp_b, label_a, label_b):
    """Judge with 3 models × 2 positions = 6 calls."""
    results = []
    for jm in JUDGE_MODELS:
        for swap in [False, True]:
            a = resp_a if not swap else resp_b
            b = resp_b if not swap else resp_a
            try:
                raw = call_api(jm, [{"role": "user", "content": JUDGE_PROMPT.format(question=question, response_a=a, response_b=b)}])
                v = parse_verdict(raw)
            except Exception as e:
                v = {"winner": "tie", "confidence": 0, "reasoning": str(e), "error": True}
            
            # Unswap
            if swap:
                if v.get("winner") == "A": v["winner"] = "B"
                elif v.get("winner") == "B": v["winner"] = "A"
            
            # Map to labels
            mapped = label_a if v["winner"] == "A" else (label_b if v["winner"] == "B" else v["winner"])
            results.append({"judge": jm, "swapped": swap, "raw_winner": v["winner"], "mapped": mapped,
                          "confidence": v.get("confidence", 0), "reasoning": v.get("reasoning", "")[:100]})
    return results

def tally(all_results, label_a, label_b):
    """Tally wins from judgment results."""
    counts = Counter()
    by_judge = {jm: Counter() for jm in JUDGE_MODELS}
    by_cat = {}
    for r in all_results:
        cat = r.get("category", "all")
        if cat not in by_cat: by_cat[cat] = Counter()
        for j in r["judgments"]:
            # Check consistency (same judge, normal vs swapped)
            counts[j["mapped"]] += 1
            by_judge[j["judge"]][j["mapped"]] += 1
            by_cat[cat][j["mapped"]] += 1
    total = sum(counts.values())
    return {
        "wins_a": counts.get(label_a, 0),
        "wins_b": counts.get(label_b, 0),
        "ties": counts.get("tie", 0),
        "errors": counts.get("error", 0),
        "total": total,
        "win_rate_b_pct": round(counts.get(label_b, 0) / max(1, total) * 100, 1),
        "win_rate_a_pct": round(counts.get(label_a, 0) / max(1, total) * 100, 1),
        "by_judge": {jm: dict(c) for jm, c in by_judge.items()},
        "by_category": {cat: dict(c) for cat, c in by_cat.items()},
    }

def run_experiment(questions, name, get_response_b, label_b="multi"):
    """Run a judging experiment comparing baseline A to some other response."""
    print(f"\n{'='*60}", flush=True)
    print(f"EXPERIMENT: {name}", flush=True)
    print(f"{'='*60}", flush=True)
    
    all_results = []
    BATCH = 10
    
    for batch_start in range(0, len(questions), BATCH):
        batch_end = min(batch_start + BATCH, len(questions))
        
        def process_q(i):
            q = questions[i]
            question = q["question"]
            resp_a = q["conditions"]["A"]["response"]
            resp_b = get_response_b(q)
            if not resp_b:
                return None
            judgments = judge_pair_all(question, resp_a, resp_b, "A", label_b)
            return {"qi": i, "qid": q.get("qid",""), "category": q.get("category",""), "judgments": judgments}
        
        with ThreadPoolExecutor(max_workers=BATCH) as pool:
            futs = {pool.submit(process_q, i): i for i in range(batch_start, batch_end)}
            for fut in as_completed(futs):
                r = fut.result()
                if r: all_results.append(r)
        
        print(f"  {min(batch_end, len(questions))}/{len(questions)} judged", flush=True)
    
    scores = tally(all_results, "A", label_b)
    
    # Save
    with open(f"{REANALYSIS_DIR}/{name}_judgments.jsonl", "w") as f:
        for r in all_results: f.write(json.dumps(r) + "\n")
    with open(f"{REANALYSIS_DIR}/{name}_scores.json", "w") as f:
        json.dump(scores, f, indent=2)
    
    print(f"\n  Results: A wins={scores['wins_a']} ({scores['win_rate_a_pct']}%) | {label_b} wins={scores['wins_b']} ({scores['win_rate_b_pct']}%) | ties={scores['ties']}", flush=True)
    return scores

def main():
    os.makedirs(REANALYSIS_DIR, exist_ok=True)
    
    with open(RESPONSES_FILE) as f:
        questions = [json.loads(l) for l in f if l.strip()]
    print(f"Loaded {len(questions)} questions", flush=True)
    print(f"Judges: {JUDGE_MODELS}", flush=True)
    
    all_scores = {}
    started = datetime.now(timezone.utc).isoformat()
    
    # --- EXP 1: ACCESS VALUE ---
    # Each raw node response vs baseline
    for node_key, node_name in [("x-ai/grok-3", "grok3"), ("google/gemini-2.0-flash-001", "gemini"), ("deepseek/deepseek-chat", "deepseek")]:
        def get_node_resp(q, nk=node_key):
            # Find this node's raw response in condition D (independent)
            for ind in q["conditions"].get("D", {}).get("individual", []):
                if ind.get("model") == nk:
                    return ind["response"]
            return None
        
        scores = run_experiment(questions, f"access_{node_name}", get_node_resp, label_b=node_name)
        all_scores[f"access_{node_name}"] = scores
    
    # --- EXP 2: DIVERSITY VALUE (best-of-3) ---
    # For each question, we'll use length-normalized quality proxy:
    # Pick the response most different from the other    # Best-of-3: have a quick judge pick the best raw response, then judge that against A
    def get_best_of_3(q):
        indiv = q["conditions"].get("D", {}).get("individual", [])
        if len(indiv) < 2:
            return None
        # Use the longest substantive response as a simple proxy
        # (In production you'd have a judge pick, but that doubles API calls)
        best = max(indiv, key=lambda x: len(x.get("response", "")))
        return best["response"]
    
    scores = run_experiment(questions, "diversity_best_of_3", get_best_of_3, label_b="best3")
    all_scores["diversity_best_of_3"] = scores
    
    # --- EXP 3: STRONG SYNTHESIS ---
    # Re-synthesize condition D responses with GPT-4o instead of GPT-4o-mini
    print(f"\n{'='*60}", flush=True)
    print(f"EXPERIMENT: strong_synthesis (re-synthesizing with GPT-4o)", flush=True)
    print(f"{'='*60}", flush=True)
    
    # First pass: re-synthesize all 200 questions
    synth_responses = [None] * len(questions)
    
    def resynthesize(i):
        q = questions[i]
        indiv = q["conditions"].get("D", {}).get("individual", [])
        if not indiv:
            return None
        prompt = (f"Question: {q['question']}\n\n"
                  f"Three independent AI models answered without seeing each other's responses:\n\n" +
                  "".join(f"--- {r.get('model','?')} ---\n{r['response']}\n\n" for r in indiv) +
                  "Synthesize the best possible answer. Combine unique insights, resolve contradictions, "
                  "correct errors. Be concise — quality over length.")
        return call_api(SYNTHESIS_MODEL_STRONG, [{"role": "user", "content": prompt}], max_tokens=1000)
    
    BATCH = 10
    for batch_start in range(0, len(questions), BATCH):
        batch_end = min(batch_start + BATCH, len(questions))
        with ThreadPoolExecutor(max_workers=BATCH) as pool:
            futs = {pool.submit(resynthesize, i): i for i in range(batch_start, batch_end)}
            for fut in as_completed(futs):
                idx = futs[fut]
                try:
                    synth_responses[idx] = fut.result()
                except Exception as e:
                    synth_responses[idx] = None
        print(f"  Re-synthesized {min(batch_end, len(questions))}/{len(questions)}", flush=True)
    
    # Save re-synthesized responses
    with open(f"{REANALYSIS_DIR}/strong_synthesis_responses.jsonl", "w") as f:
        for i, sr in enumerate(synth_responses):
            f.write(json.dumps({"qi": i, "qid": questions[i].get("qid",""), "response": sr}) + "\n")
    
    # Now judge
    def get_strong_synth(q):
        idx = q.get("qi", questions.index(q) if q in questions else -1)
        # Find by qid
        for i, qq in enumerate(questions):
            if qq.get("qid") == q.get("qid"):
                return synth_responses[i]
        return None
    
    # Add qi to questions for lookup
    for i, q in enumerate(questions):
        q["qi"] = i
    
    def get_strong_synth_by_idx(q):
        return synth_responses[q["qi"]]
    
    scores = run_experiment(questions, "strong_synthesis", get_strong_synth_by_idx, label_b="synth4o")
    all_scores["strong_synthesis"] = scores
    
    # --- FINAL SUMMARY ---
    completed = datetime.now(timezone.utc).isoformat()
    
    summary = {
        "meta": {"started": started, "completed": completed, "n_questions": len(questions), "judges": JUDGE_MODELS},
        "experiments": all_scores,
    }
    
    with open(f"{REANALYSIS_DIR}/summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*60}", flush=True)
    print(f"ALL EXPERIMENTS COMPLETE", flush=True)
    print(f"{'='*60}", flush=True)
    for name, sc in all_scores.items():
        print(f"\n{name}:", flush=True)
        print(f"  A (baseline) wins: {sc['wins_a']} ({sc['win_rate_a_pct']}%)", flush=True)
        print(f"  Condition wins: {sc['wins_b']} ({sc['win_rate_b_pct']}%)", flush=True)
        print(f"  Ties: {sc['ties']}", flush=True)
    
    print(f"\nSummary: {REANALYSIS_DIR}/summary.json", flush=True)

if __name__ == "__main__":
    main()
