import pytest

from codebreak import permute_string, phrase_to_key, transposition_decipher, transposition_encipher


def test_phrase_to_key_orders_by_alphabetical_rank():
    assert phrase_to_key("CODE") == (0, 2, 3, 1)


def test_permute_string_pads_short_input_with_stars():
    assert permute_string("AB", (0, 2, 3, 1)) == "A**B"


def test_transposition_encipher_known_example():
    assert transposition_encipher("MESSAGE", phrase_to_key("CODE")) == "MASES*EG"


@pytest.mark.parametrize(
    "message,keyword",
    [
        ("MESSAGE", "CODE"),
        ("THE QUICK BROWN FOX JUMPS", "KEYWORD"),
        ("A", "ABCDEF"),
        ("EXACTLENGTH", "ABC"),
    ],
)
def test_transposition_round_trip(message, keyword):
    key = phrase_to_key(keyword)
    cipher = transposition_encipher(message, key)
    assert transposition_decipher(cipher, key) == message
