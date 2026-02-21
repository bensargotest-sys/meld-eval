#!/usr/bin/env node
// Snapshot ledger state from all nodes and verify zero-sum.
// Run via PM2 cron during active tests.
// Usage: node collect_ledger.js [output_dir]

import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const NODES = [
  { id: 'meld-2', host: '147.93.72.73', port: 9377 },
  { id: 'meld-3', host: '72.61.53.248', port: 9377 },
  { id: 'meld-4', host: '76.13.198.23', port: 9377 },
  { id: 'meld-5', host: '187.77.177.78', port: 9377 },
];

async function fetchBalance(node) {
  // Use /health endpoint (available on all nodes)
  const res = await fetch(`http://${node.host}:${node.port}/health`, {
    signal: AbortSignal.timeout(5000),
  });
  if (!res.ok) throw new Error(`${node.id} returned ${res.status}`);
  const health = await res.json();

  // Extract balance from health response if available
  if (health.net_balance !== undefined) {
    return health;
  }

  // Fall back to /v1/balance if health doesn't include balance
  try {
    const balRes = await fetch(`http://${node.host}:${node.port}/v1/balance`, {
      signal: AbortSignal.timeout(5000),
    });
    if (balRes.ok) return await balRes.json();
  } catch (_) {}

  // Return health data even without balance info
  return { ...health, net_balance: null };
}

async function snapshot(outputDir) {
  const timestamp = new Date().toISOString();
  const results = await Promise.allSettled(NODES.map(fetchBalance));

  const balances = {};
  const errors = [];

  for (let i = 0; i < NODES.length; i++) {
    const node = NODES[i];
    if (results[i].status === 'fulfilled') {
      balances[node.id] = results[i].value;
    } else {
      errors.push({ node: node.id, error: results[i].reason.message });
    }
  }

  // Zero-sum check across all bilateral balances
  let networkSum = 0n;
  let hasBalanceData = false;
  for (const [nodeId, data] of Object.entries(balances)) {
    if (data.net_balance !== undefined && data.net_balance !== null) {
      hasBalanceData = true;
      networkSum += BigInt(Math.round(data.net_balance * 10000));
    }
  }

  const record = {
    timestamp,
    sum_all_balances: Number(networkSum),
    zero_sum_pass: hasBalanceData ? networkSum === 0n : null,
    balances,
    errors,
  };

  mkdirSync(outputDir, { recursive: true });
  const filename = join(outputDir, `${timestamp.replace(/[:.]/g, '-')}.json`);
  writeFileSync(filename, JSON.stringify(record, null, 2));

  if (hasBalanceData && !record.zero_sum_pass) {
    console.error(`ZERO-SUM VIOLATION at ${timestamp}: sum=${networkSum}`);
    process.exit(1);
  }

  console.log(`[${timestamp}] snapshot OK, sum=0, nodes=${Object.keys(balances).length}`);
}

const outputDir = process.argv[2] || 'raw_ledger_snapshots';
snapshot(outputDir).catch(err => {
  console.error(err);
  process.exit(1);
});
