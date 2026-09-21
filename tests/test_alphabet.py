from codebreak import clean_text, get_text
from codebreak.alphabet import ALPHABET_PLAIN


def test_clean_text_strips_punctuation_and_digits():
    # clean_text only filters against the allowed alphabet - it doesn't
    # uppercase (that's get_text's job), so lowercase letters are stripped
    # too unless the input has already been upper-cased.
    assert clean_text("HELLO, WORLD! 123") == "HELLO WORLD"


def test_clean_text_collapses_whitespace():
    assert clean_text("TOO   MANY\n\nSPACES") == "TOO MANY SPACES"


def test_clean_text_with_letters_only_alphabet_still_preserves_word_spacing():
    # Non-space punctuation and the space character both map to a literal
    # space, so restricting `allowed_chars` to letters doesn't remove spaces.
    assert clean_text("AB, CD!", allowed_chars=ALPHABET_PLAIN) == "AB CD"


def test_get_text_reads_and_uppercases(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("mixed CASE text")
    assert get_text(path) == "MIXED CASE TEXT"
