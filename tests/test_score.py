from evals.score import score

P = {"i-0123456789abcdef0", "vol-0123456789abcdef0", "eipalloc-0123456789abcdef0"}


def test_perfect_report():
    assert score(" ".join(P), P) == {"recall": 1.0, "missed": [], "false_positives": []}


def test_missed_and_false_positive():
    r = score("i-0123456789abcdef0 vol-ffffffffffffffff0", P)
    assert round(r["recall"], 2) == 0.33
    assert r["missed"] == ["eipalloc-0123456789abcdef0", "vol-0123456789abcdef0"]
    assert r["false_positives"] == ["vol-ffffffffffffffff0"]
