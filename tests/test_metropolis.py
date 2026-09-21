import random

from codebreak import (
    NgramScorer,
    clean_text,
    get_text,
    metropolis_algorithm,
    random_substitution_key,
    substitution_encipher,
    unigram_attack,
)


def test_metropolis_algorithm_recovers_a_substitution_cipher(unigram_freq, bigram_freq):
    from pathlib import Path

    war_text = clean_text(get_text(Path(__file__).resolve().parent.parent / "texts" / "war.txt"))
    plaintext = war_text[10000:10600]

    key = random_substitution_key(rng=random.Random(42))
    cipher = substitution_encipher(plaintext, key)

    guess = unigram_attack(cipher, unigram_freq)
    scorer = NgramScorer(bigram_freq)
    result = metropolis_algorithm(guess, scorer, t_min=0.5, t_max=5, iterations=20000, rng=random.Random(1))

    matches = sum(a == b for a, b in zip(result.message, plaintext))
    assert matches / len(plaintext) > 0.95


def test_metropolis_algorithm_trace_is_recorded_only_when_requested():
    scorer = NgramScorer({"AB": 0.5, "BA": 0.5})
    result = metropolis_algorithm(
        "ABAB", scorer, t_min=1, t_max=1, iterations=10, rng=random.Random(0), record=False
    )
    assert result.trace is None

    result = metropolis_algorithm(
        "ABAB", scorer, t_min=1, t_max=1, iterations=10, rng=random.Random(0), record=True
    )
    assert result.trace is not None
    assert len(result.trace.scores) == 10
    assert len(result.trace.temperatures) == 10
    assert len(result.trace.accepted) == 10
