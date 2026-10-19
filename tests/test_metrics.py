"""Known values for the ported interval and paired tests."""

from whostop.metrics import (
    cluster_bootstrap_ci,
    cluster_signflip_p,
    flip_rate,
    holm,
    is_targeted_flip,
    mcnemar_exact,
    proportion,
    text_similarity,
    wilson_interval,
)


def test_wilson_empty_and_zero():
    assert wilson_interval(0, 0) is None
    low, high = wilson_interval(0, 10)
    assert low == 0
    assert 0.2 < high < 0.35


def test_wilson_matches_phase2_published_intervals():
    """Rounded bounds are the ones stored in phase2_metrics.json."""
    assert [round(x, 3) for x in wilson_interval(17, 63)] == [0.176, 0.39]
    assert [round(x, 3) for x in wilson_interval(45, 71)] == [0.518, 0.736]
    assert [round(x, 3) for x in wilson_interval(62, 63)] == [0.915, 0.997]
    assert [round(x, 3) for x in wilson_interval(0, 71)] == [0.0, 0.051]


def test_wilson_full():
    low, high = wilson_interval(10, 10)
    assert high == 1
    assert low > 0.65


def test_mcnemar_no_discordant():
    result = mcnemar_exact([True, False], [True, False])
    assert result["n_discordant"] == 0
    assert result["p"] == 1.0


def test_mcnemar_counts():
    result = mcnemar_exact([True] * 6, [False] * 6)
    assert result["b_only"] == 6
    assert result["c_only"] == 0
    assert result["p"] < 0.05


def test_holm_stepdown():
    adjusted = holm([0.01, 0.04])
    assert adjusted[0] == 0.02
    assert adjusted[1] == 0.04
    capped = holm([0.4, 0.5])
    assert all(p <= 1 for p in capped)


def test_proportion_and_flip_rate():
    stats = proportion([True, False, True])
    assert stats["k"] == 2 and stats["n"] == 3
    flipped = flip_rate([True, False])
    assert flipped["k"] == 1 and flipped["n"] == 2
    assert flipped["ci95"][0] < flipped["rate"] < flipped["ci95"][1]


def test_targeted_flip_and_similarity():
    assert is_targeted_flip("BRAKE", "CONTINUE", "CONTINUE")
    assert not is_targeted_flip("CONTINUE", "CONTINUE", "CONTINUE")
    assert text_similarity("stop", "stop") == 1
    assert text_similarity("", "stop") == 0


def test_cluster_signflip_edges():
    assert cluster_signflip_p([]) == 1.0
    assert cluster_signflip_p([("only", 1, 0)], n_draws=50) == 1.0
    quiet = [("c", 1, 1), ("d", 0, 0)]
    assert cluster_signflip_p(quiet, n_draws=20) == 1.0
    strong = [(f"c{i}", 1, 0) for i in range(12)]
    assert cluster_signflip_p(strong, n_draws=500, seed=1) < 0.01


def test_cluster_bootstrap_constant_difference():
    interval = cluster_bootstrap_ci([("c", 1, 0), ("c", 1, 0)], n_draws=30, seed=0)
    assert interval == (1.0, 1.0)
    mixed = cluster_bootstrap_ci([("a", 1, 0), ("b", 0, 1)], n_draws=40, seed=2)
    assert mixed is not None
    assert mixed[0] <= 0 <= mixed[1]
