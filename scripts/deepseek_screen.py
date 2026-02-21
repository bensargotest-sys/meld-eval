#!/usr/bin/env python3
"""
Screen candidate questions through DeepSeek to detect censorship risk.
Usage: python deepseek_screen.py --input candidates.jsonl --output screened.jsonl
"""

import json
import os
import sys
import urllib.request
import time

REFUSAL_PATTERNS = [
    "i cannot discuss",
    "i'm not able to",
    "i cannot provide",
    "as an ai",
    "i must decline",
    "this topic is sensitive",
    "i cannot comment on",
]

def screen_question(question, api_key):
    payload = json.dumps({
        "model": "deepseek/deepseek-chat",
        "messages": [{"role": "user", "content": question}],
        "max_tokens": 300,
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    response = data["choices"][0]["message"]["content"]
    word_count = len(response.split())

    flags = []
    lower = response.lower()
    for pattern in REFUSAL_PATTERNS:
        if pattern in lower:
            flags.append(f"refusal_pattern: {pattern}")
    if word_count < 20:
        flags.append(f"too_short: {word_count} words")
    caveats = sum(1 for s in response.split('.') if any(p in s.lower() for p in ["however", "important to note", "should be aware"]))
    total_sentences = max(1, response.count('.'))
    if caveats / total_sentences > 0.5:
        flags.append(f"heavy_hedging: {caveats}/{total_sentences} sentences are caveats")

    return {
        "question": question,
        "response": response,
        "word_count": word_count,
        "flags": flags,
        "censored": len(flags) > 0,
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--removed", default="removed_questions.jsonl")
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        sys.exit(1)

    clean = []
    removed = []

    with open(args.input) as f:
        candidates = [json.loads(line) for line in f if line.strip()]

    print(f"Screening {len(candidates)} candidates...")
    for i, item in enumerate(candidates):
        question = item if isinstance(item, str) else item.get("question", "")
        result = screen_question(question, api_key)
        if result["censored"]:
            removed.append(result)
            print(f"[{i+1}/{len(candidates)}] REMOVED: {question[:60]}... flags={result['flags']}")
        else:
            clean.append({"question": question})
        time.sleep(0.5)

    with open(args.output, "w") as f:
        for item in clean:
            f.write(json.dumps(item) + "\n")

    with open(args.removed, "w") as f:
        for item in removed:
            f.write(json.dumps(item) + "\n")

    print(f"\nDone. {len(clean)} clean, {len(removed)} removed.")
    print(f"Clean questions → {args.output}")
    print(f"Removed questions → {args.removed}")
