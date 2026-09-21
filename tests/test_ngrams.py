import pytest

from codebreak import ngram_frequency, sort_dict
from codebreak.ngrams import UNSEEN_NGRAM_SCORE, NgramScorer


def test_sort_dict_orders_by_value_descending():
    assert list(sort_dict({"a": 1, "b": 3, "c": 2})) == ["b", "c", "a"]


def test_ngram_frequency_counts_and_normalises():
    freq = ngram_frequency("AABBB", 1)
    assert freq == {"A": pytest.approx(2 / 5), "B": pytest.approx(3 / 5)}


def test_ngram_frequency_probabilities_sum_to_one():
    freq = ngram_frequency("THE QUICK BROWN FOX", 2)
    assert sum(freq.values()) == pytest.approx(1.0)


def test_ngram_frequency_only_includes_observed_ngrams():
    freq = ngram_frequency("AB", 2)
    assert set(freq) == {"AB"}


def test_scorer_scores_common_ngram_higher_than_unseen():
    scorer = NgramScorer({"TH": 0.5, "HE": 0.5})
    assert scorer.score("THE") > scorer.score("XYZ")


def test_scorer_assigns_unseen_score_for_unknown_ngram():
    scorer = NgramScorer({"TH": 1.0})
    assert scorer.score("XY") == round(UNSEEN_NGRAM_SCORE, 4)


def test_scorer_caches_repeated_messages():
    scorer = NgramScorer({"TH": 1.0})
    first = scorer.score("THTH")
    scorer.frequencies = {}  # sabotage the model; cached result must not change
    assert scorer.score("THTH") == first


def test_scorer_rejects_empty_frequencies():
    with pytest.raises(ValueError):
        NgramScorer({})
