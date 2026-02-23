# MELD External Tester Guide

**Status:** Private Beta  
**Testnet:** 4 nodes, 3 models (DeepSeek, Gemini, Llama 3.2), real credit accounting  
**Prerequisites:** Linux/macOS, Node.js 20+, basic command line familiarity

---

## What You're Testing

MELD is a peer-to-peer inference network where agents share API access using mutual credit (no money, no blockchain, no tokens). You earn credits by serving requests, spend credits by making requests.

**Core hypothesis (proven across 17 experiments):** Multi-model consensus from diverse nodes produces better answers than any single model 89-98% of the time.

---

## Quick Start (Connect to Existing Testnet)

### 1. Install Node.js 20+
```bash
# Check version
node --version  # Should be 20.x or higher

# If needed:
# Ubuntu/Debian: https://github.com/nodesource/distributions
# macOS: brew install node@20
```

### 2. Clone MELD
```bash
git clone https://github.com/bensargotest-sys/meld.git
cd meld
git checkout sqlite  # Use the sqlite branch
npm install
```

### 3. Configure Your Node
```bash
# Create config directory
mkdir -p ~/.meld

# Generate agent identity
node scripts/setup.js

# This creates ~/.meld/config.json with:
# - agentId: your unique ID (e.g. agent-abc123)
# - sharedSecret: HMAC signing key
# - servePort: 9377
```

### 4. Add at Least One API Key (Optional but Recommended)

You can earn credits even without API keys by serving requests from local models (Ollama). But to maximize earning potential, add an API key:

```bash
# Edit ~/.meld/passthrough.json
# Add one or more:
{
  "providers": {
    "deepseek": {
      "envVar": "DEEPSEEK_API_KEY",
      "endpoint": "https://api.deepseek.com/v1/chat/completions",
      "format": "openai",
      "models": ["deepseek-chat", "deepseek-reasoner"],
      "enabled": true
    },
    "google": {
      "envVar": "GEMINI_API_KEY",
      "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
      "format": "openai",
      "models": ["gemini-2.0-flash"],
      "enabled": true
    }
  }
}

# Set environment variable:
export DEEPSEEK_API_KEY="sk-..."
# OR
export GEMINI_API_KEY="AIza..."
```

**Free API keys:**
- **Gemini:** https://ai.google.dev/ (free tier, no credit card)
- **DeepSeek:** https://platform.deepseek.com/ (cheap, $5 minimum)

### 5. Connect to a Peer

Contact the testnet operator (AB) with your `agentId` from `~/.meld/config.json`. They'll register you as a peer and give you connection details.

Once registered, you'll receive:
- Peer agent IDs
- Peer hosts/ports
- Initial credit balance (typically 5000 credits = $5 equivalent)

### 6. Start Your Node
```bash
# Make sure MELD_HOST is set to allow external connections
export MELD_HOST=0.0.0.0
export MELD_PORT=9377

# Start the server
npm start

# Or with PM2 (recommended):
pm2 start src/server.js --name meld
pm2 logs meld
```

### 7. Test Your Connection
```bash
# Health check (no auth required)
curl http://localhost:9377/v1/health

# Should return:
# {"status":"ok","uptime":123.45,"db":true,"version":"0.1.0"}
```

---

## Making Requests (Spend Credits)

### Python Example
```python
import json, time, hmac, hashlib, httpx

# Your credentials (from ~/.meld/config.json)
YOUR_AGENT_ID = "agent-abc123"
YOUR_SECRET = "your_shared_secret_hex"

# Target peer (provided by testnet operator)
PEER_HOST = "72.61.53.248"
PEER_PORT = 9377

def sign_request(agent_id, secret_hex, body_str):
    timestamp = str(int(time.time() * 1000))
    message = agent_id + timestamp + body_str
    sig = hmac.new(bytes.fromhex(secret_hex), message.encode(), hashlib.sha256).hexdigest()
    return timestamp, sig

# Create request
body = json.dumps({
    "model": "deepseek-chat",  # or "gemini-2.0-flash", "llama3.2:3b"
    "messages": [{"role": "user", "content": "Explain quantum entanglement in one sentence"}],
    "max_tokens": 100
})

ts, sig = sign_request(YOUR_AGENT_ID, YOUR_SECRET, body)

# Make authenticated request
headers = {
    "Content-Type": "application/json",
    "x-meld-agent-id": YOUR_AGENT_ID,
    "x-meld-timestamp": ts,
    "x-meld-signature": sig
}

response = httpx.post(
    f"http://{PEER_HOST}:{PEER_PORT}/v1/infer",
    headers=headers,
    content=body,
    timeout=30
)

print(response.json())
# {"response":"Quantum entanglement is...","model":"deepseek-chat","input_tokens":8,"output_tokens":25}
```

### Node.js Example
```javascript
const crypto = require('crypto');
const https = require('https');

const YOUR_AGENT_ID = "agent-abc123";
const YOUR_SECRET = "your_shared_secret_hex";
const PEER_HOST = "72.61.53.248";
const PEER_PORT = 9377;

function signRequest(agentId, secretHex, bodyStr) {
  const timestamp = String(Date.now());
  const message = agentId + timestamp + bodyStr;
  const sig = crypto.createHmac('sha256', Buffer.from(secretHex, 'hex'))
    .update(message).digest('hex');
  return { timestamp, sig };
}

const body = JSON.stringify({
  model: "deepseek-chat",
  messages: [{ role: "user", content: "What is the capital of France?" }],
  max_tokens: 10
});

const { timestamp, sig } = signRequest(YOUR_AGENT_ID, YOUR_SECRET, body);

const options = {
  hostname: PEER_HOST,
  port: PEER_PORT,
  path: '/v1/infer',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-meld-agent-id': YOUR_AGENT_ID,
    'x-meld-timestamp': timestamp,
    'x-meld-signature': sig,
    'Content-Length': Buffer.byteLength(body)
  }
};

const req = https.request(options, (res) => {
  let data = '';
  res.on('data', (chunk) => data += chunk);
  res.on('end', () => console.log(JSON.parse(data)));
});

req.write(body);
req.end();
```

---

## Serving Requests (Earn Credits)

When other nodes call YOUR node, you earn credits automatically. No action needed.

**What you're serving:**
- Any API keys you configured in `passthrough.json`
- Local models via Ollama (if installed)

**To maximize earnings:**
1. Add multiple API keys (DeepSeek, Gemini, etc.)
2. Install Ollama and pull models: `ollama pull llama3.2:3b`
3. Keep your node online 24/7

**Check your earnings:**
```bash
# View balance with a specific peer
curl http://localhost:9377/v1/balance?peer_agent_id=agent-xyz

# View all transactions
curl http://localhost:9377/v1/ledger
```

---

## Multi-Model Consensus (The Core Value Prop)

Instead of calling one model, call 3+ models and synthesize:

```python
# Call 3 different nodes
responses = []
for peer in [peer1, peer2, peer3]:
    r = call_meld(peer, prompt)
    responses.append(r['response'])

# Synthesize with a 4th call (or local GPT-4o)
synthesis_prompt = f"""Combine these expert responses into the single best answer:

Response 1: {responses[0]}
Response 2: {responses[1]}
Response 3: {responses[2]}

Synthesized answer:"""

final = call_meld(synthesis_peer, synthesis_prompt)
```

**Why this works:** Our research (17 experiments, 11,000+ judgments) shows this beats any single model 89-98% of the time.

---

## Troubleshooting

### "Insufficient credits"
- You've spent more than you earned
- Solution: Serve more requests, or ask testnet operator to seed more credits

### "Invalid HMAC signature"
- Clock skew (timestamp >60s off)
- Wrong secret (check `~/.meld/config.json`)
- Body encoding mismatch (ensure UTF-8, no extra whitespace)

### "Unknown agent"
- Peer hasn't registered you yet
- Solution: Contact testnet operator with your `agentId`

### "Model Not Exist"
- Wrong model name (check peer's available models via `/v1/network`)
- Solution: Use raw model names (`deepseek-chat` not `deepseek/deepseek-chat`)

### Connection timeout
- Firewall blocking port 9377
- Peer offline
- Solution: Check `ufw status`, verify peer is running with `curl http://PEER:9377/v1/health`

---

## What to Test

1. **Basic inference** — Can you call a peer and get a response?
2. **Credit accounting** — Do credits increase when you serve, decrease when you call?
3. **Multi-model consensus** — Call 3 peers, synthesize. Is the result noticeably better?
4. **Model diversity** — Try DeepSeek, Gemini, Llama. Do different models give different insights?
5. **Latency** — How fast is P2P vs direct API call?
6. **Reliability** — Does it work consistently over hours/days?

---

## Feedback

Report bugs, issues, or suggestions:
- **Telegram:** @ABDB09
- **GitHub Issues:** https://github.com/bensargotest-sys/meld/issues
- **Research repo:** https://github.com/bensargotest-sys/meld-eval

---

## Next Steps After Testing

If the testnet proves stable:
1. **Open beta** — Anyone can join
2. **Network discovery** — Auto-find peers (currently manual)
3. **Client SDKs** — Python/JS/Go libraries for easy integration
4. **Guard product** — Consensus-gated safety checks for autonomous agents
5. **Production deployment** — Real economic activity, no artificial credit seeds

**Current stage:** Private beta, 4 nodes, real infrastructure, proven functional.
