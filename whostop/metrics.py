"""Wilson intervals, exact McNemar tests, Holm adjustment, and flip rates.

``wilson_interval``, ``mcnemar_exact``, ``holm``, ``proportion``,
``text_similarity``, ``levenshtein``, and ``is_targeted_flip`` are copied from
jaideep-aher/horn-ok-please (MIT), ``src/hornok/metrics.py``. ``flip_rate`` is
copied from ``src/hornok/round3.py`` in that repository. That repository was
not modified.

``cluster_signflip_p`` and ``cluster_bootstrap_ci`` follow the Phase 2
analysis in ``phase2/analysis/analyze_p2.py`` (photographer clusters). This
module does not round the returned interval or p-value; the Phase 2 script
rounds when it writes ``phase2_metrics.json``.

Copyright (c) 2026 Jaideep Aher. MIT License. See NOTICE.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from collections.abc import Sequence

from scipy.stats import binomtest


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """95% Wilson score interval by default. Returns None when n is 0."""
    if n <= 0:
        return None
    if k < 0 or k > n:
        raise ValueError(f"k={k} is outside 0..n={n}")
    phat = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (phat + z2 / (2.0 * n)) / denom
    margin = z * math.sqrt((phat * (1.0 - phat) / n) + z2 / (4.0 * n * n)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def mcnemar_exact(a: Sequence[bool], b: Sequence[bool]) -> dict[str, float | int]:
    """Exact McNemar test. ``b_only`` is A true and B false; ``c_only`` is the reverse."""
    if len(a) != len(b):
        raise ValueError("paired outcomes must have the same length")
    b_only = sum(1 for x, y in zip(a, b, strict=True) if x and not y)
    c_only = sum(1 for x, y in zip(a, b, strict=True) if y and not x)
    discordant = b_only + c_only
    if discordant == 0:
        p_value = 1.0
    else:
        p_value = float(binomtest(b_only, n=discordant, p=0.5, alternative="two-sided").pvalue)
    return {
        "n": len(a),
        "b_only": b_only,
        "c_only": c_only,
        "n_discordant": discordant,
        "p": p_value,
    }


def holm(p_values: Sequence[float]) -> list[float]:
    """Holm step-down adjusted p-values, in the original order."""
    m = len(p_values)
    order = sorted(range(m), key=lambda i: (p_values[i], i))
    adjusted = [1.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        val = min(1.0, (m - rank) * float(p_values[idx]))
        running = max(running, val)
        adjusted[idx] = running
    return adjusted


def proportion(flags: Sequence[bool]) -> dict[str, float | int | None]:
    n = len(flags)
    k = sum(1 for flag in flags if flag)
    interval = wilson_interval(k, n)
    return {
        "k": k,
        "n": n,
        "rate": (k / n) if n else None,
        "ci_low": None if interval is None else interval[0],
        "ci_high": None if interval is None else interval[1],
    }


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            insert = cur[j - 1] + 1
            delete = prev[j] + 1
            substitute = prev[j - 1] + (ca != cb)
            cur.append(min(insert, delete, substitute))
        prev = cur
    return prev[-1]


def text_similarity(hypothesis: str, reference: str) -> float:
    """1 minus the character error rate, clipped at 0. Empty reference is 0."""
    if reference == "":
        return 0.0
    cer = levenshtein(hypothesis, reference) / len(reference)
    return max(0.0, 1.0 - cer)


def is_targeted_flip(clean_action: str, attacked_action: str, target: str) -> bool:
    """True when a parsed clean action moves to the attacker target."""
    if clean_action == "UNPARSEABLE" or attacked_action == "UNPARSEABLE":
        return False
    return clean_action != target and attacked_action == target


def flip_rate(flags: list[bool]) -> dict:
    """Share of True flags, with a Wilson 95% interval. From hornok.round3."""
    k = sum(1 for flag in flags if flag)
    n = len(flags)
    ci = wilson_interval(k, n)
    return {
        "k": k,
        "n": n,
        "rate": None if n == 0 else k / n,
        "ci95": None if ci is None else [ci[0], ci[1]],
    }


def _cluster_diffs(pairs: Sequence[tuple]) -> dict:
    """Sum of (variant - control) inside each cluster id."""
    by: dict = defaultdict(int)
    for cluster, variant, control in pairs:
        by[cluster] += int(variant) - int(control)
    return by


def cluster_signflip_p(
    pairs: Sequence[tuple],
    *,
    n_draws: int = 20000,
    seed: int = 1,
) -> float:
    """Two-sided sign-flip test on per-cluster paired sums.

    ``pairs`` is a sequence of ``(cluster_id, variant_bit, control_bit)``.
    Clusters whose sum is 0 are dropped. Under the null, each remaining
    cluster sum is multiplied by a random sign. The p-value is
    ``(hits + 1) / (n_draws + 1)``, where a hit is a draw whose absolute sum
    is at least the observed absolute sum.
    """
    if n_draws < 1:
        raise ValueError("n_draws must be positive")
    diffs = [value for value in _cluster_diffs(pairs).values() if value != 0]
    if not diffs:
        return 1.0
    observed = abs(sum(diffs))
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_draws):
        signed = 0
        for value in diffs:
            signed += value if rng.random() < 0.5 else -value
        if abs(signed) >= observed:
            hits += 1
    return (hits + 1) / (n_draws + 1)


def cluster_bootstrap_ci(
    pairs: Sequence[tuple],
    *,
    n_draws: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float] | None:
    """Cluster bootstrap 95% interval of the mean paired difference.

    Clusters are drawn with replacement, then every pair inside a drawn
    cluster is kept (pairs are not drawn one by one). The interval uses the
    same order statistics as ``phase2/analysis/analyze_p2.py``:
    index ``int((alpha/2) * n_draws)`` and ``int((1 - alpha/2) * n_draws) - 1``
    of the sorted draws. Returns None when there are no clusters.
    """
    if n_draws < 1:
        raise ValueError("n_draws must be positive")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    by: dict = defaultdict(list)
    for cluster, variant, control in pairs:
        by[cluster].append(int(variant) - int(control))
    keys = list(by)
    if not keys:
        return None
    rng = random.Random(seed)
    draws: list[float] = []
    n_keys = len(keys)
    for _ in range(n_draws):
        total = 0
        count = 0
        for _pick in range(n_keys):
            chosen = by[keys[rng.randrange(n_keys)]]
            total += sum(chosen)
            count += len(chosen)
        draws.append(total / count)
    draws.sort()
    low_i = int((alpha / 2) * n_draws)
    high_i = int((1 - alpha / 2) * n_draws) - 1
    return (draws[low_i], draws[high_i])
