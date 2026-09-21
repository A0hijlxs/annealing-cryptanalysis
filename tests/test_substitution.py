import random

from codebreak import (
    cyclic_decipher,
    cyclic_encipher,
    decipher,
    invert_key,
    random_substitution_key,
    substitution_encipher,
    swap_chars,
    unigram_attack,
)
from codebreak.alphabet import ALPHABET


def test_cyclic_round_trip():
    message = "ATTACK AT DAWN"
    for shift in range(len(ALPHABET)):
        assert cyclic_decipher(cyclic_encipher(message, shift), shift) == message


def test_swap_chars_swaps_both_directions():
    assert swap_chars("ABCA", "A", "C") == "CBAC"


def test_swap_chars_is_a_no_op_for_untouched_characters():
    assert swap_chars("HELLO", "X", "Y") == "HELLO"


def test_random_substitution_key_is_a_bijection_and_fixes_space():
    key = random_substitution_key(rng=random.Random(0))
    assert key[" "] == " "
    assert sorted(key.values()) == sorted(ALPHABET)
    assert len(set(key.values())) == len(ALPHABET)


def test_substitution_round_trip_with_random_key():
    rng = random.Random(1)
    key = random_substitution_key(rng=rng)
    message = "THE QUICK BROWN FOX"
    cipher = substitution_encipher(message, key)
    assert decipher(cipher, invert_key(key)) == message


def test_unigram_attack_recovers_space_as_most_frequent_character():
    # Space is by far the most frequent character in English text, so a
    # unigram attack should map it correctly even before any refinement.
    cipher = "X A X A X"  # space is already the most frequent character here
    guess = unigram_attack(cipher, {" ": 0.5, "E": 0.3, "T": 0.2})
    assert guess.count(" ") == cipher.count(" ")
