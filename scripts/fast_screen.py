#!/usr/bin/env python3
"""Fast DeepSeek screener - concurrent API calls."""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request

REFUSAL_PATTERNS = [
    "i cannot discuss", "i'm not able to", "i cannot provide",
    "as an ai", "i must decline", "this topic is sensitive",
    "i cannot comment on",
]

API_KEY = os.environ["OPENROUTER_API_KEY"]

def screen(item):
    q = item["question"] if isinstance(item, dict) else item
    cat = item.get("category", "unknown") if isinstance(item, dict) else "unknown"
    try:
        payload = json.dumps({
            "model": "deepseek/deepseek-chat",
            "messages": [{"role": "user", "content": q}],
            "max_tokens": 300,
        }).encode()
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        response = data["choices"][0]["message"]["content"]
        wc = len(response.split())
        flags = []
        lower = response.lower()
        for p in REFUSAL_PATTERNS:
            if p in lower:
                flags.append(f"refusal: {p}")
        if wc < 20:
            flags.append(f"too_short: {wc}w")
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        caveats = sum(1 for s in sentences if any(x in s.lower() for x in ["however", "important to note", "should be aware"]))
        if len(sentences) > 0 and caveats / len(sentences) > 0.5:
            flags.append(f"heavy_hedging: {caveats}/{len(sentences)}")
        return {"question": q, "category": cat, "flags": flags, "censored": len(flags) > 0, "response": response[:200]}
    except Exception as e:
        return {"question": q, "category": cat, "flags": [f"error: {str(e)[:100]}"], "censored": True, "response": ""}

with open(sys.argv[1]) as f:
    candidates = [json.loads(line) for line in f if line.strip()]

print(f"Screening {len(candidates)} questions with 10 threads...")
clean, removed = [], []

with ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(screen, c): i for i, c in enumerate(candidates)}
    done = 0
    for fut in as_completed(futures):
        done += 1
        result = fut.result()
        if result["censored"]:
            removed.append(result)
            print(f"[{done}/{len(candidates)}] REMOVED: {result['question'][:50]}... {result['flags']}")
        else:
            clean.append({"question": result["question"], "category": result["category"]})
        if done % 50 == 0:
            print(f"  Progress: {done}/{len(candidates)}")

with open(sys.argv[2], "w") as f:
    for item in clean:
        f.write(json.dumps(item) + "\n")

with open(sys.argv[3], "w") as f:
    for item in removed:
        f.write(json.dumps(item) + "\n")

# Summary
reasons = {}
for r in removed:
    for flag in r["flags"]:
        key = flag.split(":")[0].strip()
        reasons[key] = reasons.get(key, 0) + 1

print(f"\n{'='*50}")
print(f"SCREENING SUMMARY")
print(f"{'='*50}")
print(f"Total candidates: {len(candidates)}")
print(f"Passed: {len(clean)}")
print(f"Removed: {len(removed)}")
print(f"Removal reasons:")
for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")
print(f"{'='*50}")

# Category breakdown
cats = {}
for item in clean:
    c = item.get("category", "unknown")
    cats[c] = cats.get(c, 0) + 1
print(f"Clean by category:")
for k, v in sorted(cats.items()):
    print(f"  {k}: {v}")
