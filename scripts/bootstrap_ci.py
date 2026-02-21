#!/usr/bin/env python3
import numpy as np
import json
import sys
from itertools import combinations

def bootstrap_paired_ci(scores_a, scores_b, n_boot=10000, ci=0.95, seed=42):
    """Bootstrap CI for paired difference (same questions, two conditions)."""
    rng = np.random.RandomState(seed)
    diffs = np.array(scores_a) - np.array(scores_b)
    boot_means = [np.mean(rng.choice(diffs, len(diffs), replace=True))
                  for _ in range(n_boot)]
    alpha = (1 - ci) / 2
    ci_lower = float(np.percentile(boot_means, 100 * alpha))
    ci_upper = float(np.percentile(boot_means, 100 * (1 - alpha)))
    return {
        'mean_diff': float(np.mean(diffs)),
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'n': len(diffs),
        'n_bootstrap': n_boot,
        'significant': ci_lower > 0 or ci_upper < 0
    }

def holm_bonferroni(p_values, alpha=0.05):
    """
    Holm-Bonferroni correction for multiple hypotheses.
    Returns list of booleans: True = reject null (significant after correction).
    """
    n = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    rejected = [False] * n
    for rank, (orig_idx, p) in enumerate(indexed):
        threshold = alpha / (n - rank)
        if p <= threshold:
            rejected[orig_idx] = True
        else:
            break  # stop at first non-rejection
    return rejected

if __name__ == '__main__':
    import json
    data = json.load(sys.stdin)
    result = bootstrap_paired_ci(data['scores_a'], data['scores_b'])
    print(json.dumps(result, indent=2))
