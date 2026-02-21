#!/usr/bin/env python3
"""
LLM-as-judge pairwise evaluation with position-swap bias control.
Usage: python judge_quality.py --question Q --response-a A --response-b B --judge-model MODEL
"""

import argparse
import json
import os
import sys
from datetime import datetime

JUDGE_PROMPT_TEMPLATE = """You are evaluating two responses to a question. Your task is to determine which response is better.

IMPORTANT: Do not score response length as quality. A shorter, accurate response is better than a longer padded response.

Question:
{question}

Response A:
{response_a}

Response B:
{response_b}

Evaluate on: accuracy, reasoning quality, completeness, and clarity.
Do NOT consider response length as a quality signal.

Respond with JSON only:
{{"winner": "A" or "B" or "tie", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

def judge_pair(question, response_a, response_b, judge_model, api_key=None):
    """Run pairwise judgment with position swap."""
    import urllib.request

    results = []
    for swap in [False, True]:
        a = response_a if not swap else response_b
        b = response_b if not swap else response_a

        prompt = JUDGE_PROMPT_TEMPLATE.format(
            question=question, response_a=a, response_b=b
        )

        payload = json.dumps({
            "model": judge_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
        }).encode()

        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key or os.environ['OPENROUTER_API_KEY']}",
                "Content-Type": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())

        raw = data["choices"][0]["message"]["content"]
        try:
            verdict = json.loads(raw)
        except json.JSONDecodeError:
            verdict = {"winner": "tie", "confidence": 0.0, "reasoning": raw, "parse_error": True}

        if swap and verdict.get("winner") == "A":
            verdict["winner"] = "B"
        elif swap and verdict.get("winner") == "B":
            verdict["winner"] = "A"

        verdict["swapped"] = swap
        results.append(verdict)

    winners = [r["winner"] for r in results]
    consistent = winners[0] == winners[1]

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "judge_model": judge_model,
        "question_hash": hash(question) & 0xFFFFFF,
        "results": results,
        "consistent": consistent,
        "final_winner": winners[0] if consistent else "inconsistent",
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    parser.add_argument("--response-a", required=True)
    parser.add_argument("--response-b", required=True)
    parser.add_argument("--judge-model", default="openai/gpt-4o")
    parser.add_argument("--output", help="Write result JSON to this file")
    args = parser.parse_args()

    result = judge_pair(args.question, args.response_a, args.response_b, args.judge_model)
    output = json.dumps(result, indent=2)
    print(output)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
