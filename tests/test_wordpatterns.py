import pytest

from codebreak import Dictionary, all_patterns, get_pattern
from codebreak.wordpatterns import intersect, intersect_mappings, union, valid_combinations


def test_get_pattern_textbook_example():
    assert get_pattern("HGHHU") == "0.1.0.0.2"


def test_get_pattern_all_distinct_letters():
    assert get_pattern("CAT") == "0.1.2"


def test_all_patterns_groups_words_by_pattern():
    grouped = all_patterns(["CAT", "DOG", "PUP"])
    assert grouped["0.1.2"] == ["CAT", "DOG"]
    assert grouped["0.1.0"] == ["PUP"]


def test_intersect_and_union_of_sets():
    sets = [{"A", "B", "C"}, {"B", "C", "D"}, {"B", "C"}]
    assert intersect(sets) == {"B", "C"}
    assert union(sets) == {"A", "B", "C", "D"}


def test_valid_combinations_excludes_reused_items():
    combos = set(valid_combinations((("A", "B"), ("A", "B"))))
    assert combos == {("A", "B"), ("B", "A")}


def test_intersect_mappings_merges_and_narrows_possibilities():
    maps = [{"X": {"A", "B"}}, {"X": {"B", "C"}}]
    assert intersect_mappings(maps) == {"X": {"B"}}


def test_dictionary_word_mapping_matches_pattern():
    dictionary = Dictionary(["CAT", "DOG", "PUPPY"])  # PUPPY has a different pattern, a distractor
    mapping = dictionary.word_mapping("CAT")
    assert mapping["C"] == {"C", "D"}
    assert mapping["A"] == {"A", "O"}
    assert mapping["T"] == {"T", "G"}


def test_dictionary_word_mapping_raises_for_unmatched_pattern():
    dictionary = Dictionary(["CAT"])
    with pytest.raises(ValueError):
        dictionary.word_mapping("AB")  # pattern 0.1, no dictionary word matches


def test_dictionary_is_english_respects_tolerance():
    dictionary = Dictionary(["CALL", "ME", "NOW"])
    assert dictionary.is_english("CALL ME NOW", tolerance=0.8)
    assert not dictionary.is_english("CALL ME ZZZZ", tolerance=0.8)


def test_dictionary_brute_force_cracks_a_short_phrase():
    # Short phrases like this have too little text for frequency analysis,
    # but word-pattern matching plus a dictionary narrows the key space
    # enough to brute force directly.
    dictionary = Dictionary(["CALL", "BALL", "TALL", "ME", "GO", "NOW", "FOR"])
    plaintext = "CALL ME NOW"
    key = {"C": "Q", "A": "X", "L": "Z", "M": "V", "E": "R", " ": " ", "N": "F", "O": "D", "W": "T"}
    cipher = "".join(key[c] for c in plaintext)

    candidates = dictionary.brute_force(cipher, tolerance=0.8)
    assert plaintext in candidates
