import pytest

from codebreak import (
    break_vigenere,
    count_chars,
    estimate_key_length,
    index_of_coincidence,
    vigenere_decipher,
    vigenere_encipher,
)
from codebreak.vigenere import ENGLISH_IC


def test_vigenere_round_trip():
    message = "VIGENERE AUTOMATICALLY"
    cipher = vigenere_encipher(message, "KEY")
    assert vigenere_decipher(cipher, "KEY") == message


def test_vigenere_preserves_non_alphabet_characters():
    cipher = vigenere_encipher("HELLO WORLD", "KEY")
    assert " " in cipher
    assert len(cipher) == len("HELLO WORLD")


def test_count_chars_ignores_spaces():
    counts = count_chars("AA B")
    assert counts["A"] == 2
    assert counts[" "] == 0


def test_index_of_coincidence_english_text_higher_than_short_period_rotation(english_corpus):
    # IC is invariant under reshuffling, but a short-period Vigenere rotation
    # spreads letter frequencies out and should visibly lower it.
    sample = english_corpus[:5000].replace(" ", "")
    rotated = vigenere_encipher(sample, "AB")
    assert index_of_coincidence(sample) > index_of_coincidence(rotated)


def test_estimate_key_length_scores_the_true_length_as_well_as_its_pick(english_corpus):
    # The closest-average-IC heuristic cannot distinguish a key length from
    # its harmonics: a multiple of the true period produces near-identical
    # column statistics, so `best_length` can land on a harmonic (e.g. 14
    # instead of 7) from a near-exact tie. This checks that the true length
    # scores as well as whichever length was picked, rather than requiring
    # exact recovery.
    plaintext = english_corpus[:100_000]
    key = "VIGENER"
    cipher = vigenere_encipher(plaintext, key)
    ics, best_length = estimate_key_length(cipher)

    true_diff = abs(ics[len(key) - 1] - ENGLISH_IC)
    best_diff = abs(ics[best_length - 1] - ENGLISH_IC)
    assert true_diff == pytest.approx(best_diff, abs=1e-3)


def test_break_vigenere_recovers_the_key(english_corpus):
    # Per-column key-letter recovery needs enough ciphertext per key letter
    # for the most-frequent-letter heuristic to be reliable (~3k chars/letter
    # here). guess_len is passed explicitly since key-length estimation is a
    # separate, less reliable step (see the test above).
    plaintext = english_corpus[:20_000].replace(" ", "")
    key = "VIGENER"
    cipher = vigenere_encipher(plaintext, key)

    decryption, recovered_key = break_vigenere(cipher, guess_len=len(key))

    assert recovered_key == key
    assert decryption == plaintext
