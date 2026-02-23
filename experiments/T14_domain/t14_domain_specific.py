#!/usr/bin/env python3
"""T14: Domain-Specific Testing — Does consensus help for code and math?

Tests whether the consensus advantage generalizes beyond general knowledge.
3 domains × 2 conditions × 20 questions each.

Domains:
  - Code (Python debugging, algorithm design, code review)
  - Math (word problems, proofs, numerical reasoning)
  - Analysis (business strategy, data interpretation, trade-off evaluation)

Conditions:
  A: GPT-4o single (control)
  B: 3-model → GPT-4o synthesis (proven MELD pattern)
"""

import asyncio, json, os, httpx
from pathlib import Path

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
GEMINI_MODEL = "gemini-2.0-flash"
GPT4O_URL = "https://api.openai.com/v1/chat/completions"
GPT4O_MODEL = "gpt-4o"
GROK_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-3"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

MAX_TOKENS = 768  # longer for code
TIMEOUT = 60.0

# Domain-specific questions
CODE_QUESTIONS = [
    "Write a Python function that finds the longest palindromic substring in a string. Explain your approach and its time complexity.",
    "Debug this Python code that's supposed to flatten a nested list: def flatten(lst): result = []; for item in lst: if type(item) == list: flatten(item); else: result.append(item); return result",
    "Implement a LRU cache in Python without using functools. It should support get(key) and put(key, value) in O(1) time.",
    "Review this code and identify all bugs: def merge_sort(arr): if len(arr) <= 1: return arr; mid = len(arr) / 2; left = merge_sort(arr[:mid]); right = merge_sort(arr[mid:]); return merge(left, right)",
    "Write a Python generator that yields all prime numbers up to n using the Sieve of Eratosthenes. Then explain when you'd use a generator vs a list.",
    "Explain the difference between deepcopy and shallow copy in Python with an example where using the wrong one causes a bug.",
    "Design a rate limiter class in Python that allows at most N requests per minute using the sliding window algorithm.",
    "Write a function to detect a cycle in a linked list. Explain why your approach works and its space/time complexity.",
    "What's wrong with this async Python code and how would you fix it? async def fetch_all(urls): results = []; for url in urls: resp = await aiohttp.get(url); results.append(resp); return results",
    "Implement a trie data structure in Python that supports insert, search, and startsWith operations. When would you use a trie vs a hash map?",
    "Write a Python decorator that retries a function up to 3 times with exponential backoff if it raises an exception.",
    "Explain Python's GIL. Write code that demonstrates when threading helps and when it doesn't.",
    "Design a simple pub/sub system in Python. How would you handle subscriber failures?",
    "Write a function that serializes and deserializes a binary tree to/from a string.",
    "Review this SQL query for performance issues: SELECT * FROM orders o JOIN users u ON o.user_id = u.id WHERE u.created_at > '2024-01-01' ORDER BY o.total DESC LIMIT 100",
    "Implement consistent hashing in Python for distributing keys across N servers.",
    "Write a Python function that evaluates a mathematical expression string like '2 + 3 * (4 - 1)' respecting operator precedence.",
    "Explain the CAP theorem with a concrete example. How would you design a system that prioritizes availability over consistency?",
    "Write a Python context manager that measures execution time, handles exceptions, and logs both.",
    "Design a simple task queue with worker pools in Python using only the standard library.",
]

MATH_QUESTIONS = [
    "A rope is tied around the Earth's equator. If you add 1 meter to the rope's length and distribute the slack evenly, how high above the surface will the rope be? Show your work.",
    "Prove that the square root of 2 is irrational.",
    "A prisoner is given 2 dice. If the sum is 7, they go free. What's the probability? What if they can choose to roll 1 or 2 dice?",
    "In a room of 23 people, what's the probability that at least two share a birthday? Derive the formula, don't just state it.",
    "You have 12 identical-looking coins. One is counterfeit (lighter or heavier). Using a balance scale exactly 3 times, find the counterfeit coin and determine if it's lighter or heavier.",
    "Explain the Monty Hall problem. Then extend it: what if there are 100 doors and Monty opens 98?",
    "A bat and ball cost $1.10 together. The bat costs $1.00 more than the ball. How much does the ball cost? Explain why most people get this wrong.",
    "Calculate the probability of getting exactly 3 heads in 10 fair coin flips. Then generalize to k heads in n flips.",
    "Two trains are 100km apart, heading toward each other at 50km/h each. A fly starts on one train and flies at 75km/h back and forth between them until they meet. How far does the fly travel?",
    "Prove that for any integer n, n³ - n is always divisible by 6.",
    "A king places 1 grain of rice on the first square of a chessboard, 2 on the second, 4 on the third, doubling each time. How many total grains? Express in common terms.",
    "Three logicians walk into a bar. The bartender asks 'Does everybody want a drink?' The first says 'I don't know.' The second says 'I don't know.' The third says 'Yes.' Explain the reasoning.",
    "What is the expected number of coin flips needed to get two heads in a row?",
    "Prove by induction that 1 + 2 + 3 + ... + n = n(n+1)/2.",
    "A clock shows 3:15. What is the exact angle between the hour and minute hands?",
    "You have two ropes that each take exactly 1 hour to burn (but burn non-uniformly). How do you measure exactly 45 minutes?",
    "Explain the difference between permutations and combinations. In how many ways can you select a committee of 3 from 10 people?",
    "A snail climbs 3 feet up a well each day but slides back 2 feet each night. If the well is 30 feet deep, on which day does the snail escape?",
    "What is Bayes' theorem? A medical test is 99% accurate. The disease affects 1 in 10,000 people. If you test positive, what's the probability you actually have it?",
    "Prove that there are infinitely many prime numbers.",
]

ANALYSIS_QUESTIONS = [
    "A startup has $500K runway, 2 engineers, and a product with 100 daily users growing 5% week-over-week. Should they raise money now or wait? Analyze the trade-offs.",
    "Compare the strategic implications of building vs buying for a company that needs real-time data processing. Consider 3-year TCO.",
    "A SaaS company has 40% annual churn but strong NPS (65). Diagnose the likely root cause and recommend 3 specific interventions.",
    "Analyze the prisoner's dilemma as it applies to pricing strategy between two competing airlines. When does cooperation emerge?",
    "A city wants to reduce traffic congestion. Compare congestion pricing, expanded public transit, and remote work incentives. Which has the best ROI?",
    "Evaluate the decision to open-source a company's core product. What market conditions make this a good vs bad strategy?",
    "A hospital has data showing that patients admitted on weekends have higher mortality. Design a study to determine if this is causal or correlational.",
    "Compare microservices vs monolith architecture for a team of 5 building a marketplace. Consider the next 3 years.",
    "A country's central bank faces 8% inflation and 6% unemployment. Analyze the policy trade-offs between raising and lowering interest rates.",
    "Evaluate whether AI will increase or decrease income inequality over the next decade. Present both sides with evidence.",
    "A retail chain is deciding between opening 10 small stores or 2 large ones in a new market. Analyze using unit economics.",
    "Compare the risk profiles of index funds vs concentrated stock portfolios for a 30-year-old vs a 60-year-old investor.",
    "A platform with 1M users wants to introduce a subscription model. Analyze the risks and recommend a transition strategy.",
    "Evaluate the argument that remote work reduces innovation. What does the evidence actually show?",
    "A company discovers its product is being used for an unintended purpose that generates 3x revenue. Pivot or stay the course?",
    "Analyze the first-mover advantage vs fast-follower advantage in AI model development.",
    "A government must allocate $1B between education, healthcare, and infrastructure. Design a framework for making this decision.",
    "Compare the effectiveness of carbon taxes vs cap-and-trade for reducing emissions. Consider political feasibility.",
    "A tech company has a 10x engineer who is toxic to the team. Quantify the trade-off and recommend a decision.",
    "Evaluate whether MELD-style multi-agent consensus is economically viable as a business. Consider the cost of consensus vs single-model inference, the addressable market, and defensibility.",
]

ALL_QUESTIONS = (
    [{"question": q, "domain": "code"} for q in CODE_QUESTIONS] +
    [{"question": q, "domain": "math"} for q in MATH_QUESTIONS] +
    [{"question": q, "domain": "analysis"} for q in ANALYSIS_QUESTIONS]
)


async def call_api(client, url, model, api_key, messages, max_tokens=MAX_TOKENS):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    body = {"model": model, "messages": messages, "max_tokens": max_tokens, "stream": False}
    try:
        resp = await client.post(url, json=body, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"


async def synthesize(client, question, responses, api_key):
    parts = "\n\n".join(f"Response {i+1}:\n{r}" for i, r in enumerate(responses))
    prompt = f"Synthesize these responses into one superior answer. Combine the best elements, resolve any contradictions, and produce the most accurate and complete answer.\n\nQuestion: {question}\n\n{parts}\n\nProvide a single, superior synthesis."
    return await call_api(client, GPT4O_URL, GPT4O_MODEL, api_key, [{"role": "user", "content": prompt}])


async def run():
    out_dir = Path("/tmp/results")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "t14_responses.jsonl"
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

    print(f"T14 Domain-Specific — {len(ALL_QUESTIONS)} questions × 2 conditions")
    print(f"  Code: {len(CODE_QUESTIONS)}, Math: {len(MATH_QUESTIONS)}, Analysis: {len(ANALYSIS_QUESTIONS)}")

    async with httpx.AsyncClient() as client:
        for i, item in enumerate(ALL_QUESTIONS):
            if i < done:
                continue
            q = item["question"]
            domain = item["domain"]
            print(f"[{i+1}/{len(ALL_QUESTIONS)}] [{domain}] {q[:55]}...")
            row = {"q_idx": i, "question": q, "domain": domain}
            msgs = [{"role": "user", "content": q}]

            # A: GPT-4o single
            row["A"] = await call_api(client, GPT4O_URL, GPT4O_MODEL, keys["openai"], msgs)
            print(f"  A (single): {len(row['A'])} chars")

            # B: 3-model → GPT-4o synthesis
            t_grok = call_api(client, GROK_URL, GROK_MODEL, keys["xai"], msgs)
            t_gem = call_api(client, GEMINI_URL, GEMINI_MODEL, keys["gemini"], msgs)
            t_ds = call_api(client, DEEPSEEK_URL, DEEPSEEK_MODEL, keys["deepseek"], msgs)
            resps = list(await asyncio.gather(t_grok, t_gem, t_ds))
            row["B"] = await synthesize(client, q, resps, keys["openai"])
            print(f"  B (consensus): {len(row['B'])} chars")

            with open(out_path, "a") as f:
                f.write(json.dumps(row) + "\n")

    print(f"\n✅ T14 collection complete: {out_path}")


if __name__ == "__main__":
    asyncio.run(run())
