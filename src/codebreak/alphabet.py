"""Alphabets and text loading/cleaning shared across ciphers.

Substitution and word-pattern attacks need the space character in the
alphabet (it's highly informative for frequency analysis and required for
word boundaries). Vigenere and transposition traditionally operate on
letters only, so they use the 26-letter alphabet instead.
"""

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "
ALPHABET_PLAIN = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def get_text(path: str) -> str:
    """Read the full contents of a file, upper-cased."""
    with open(path, "r") as f:
        return f.read().upper()


def clean_text(text: str, allowed_chars: str = ALPHABET) -> str:
    """Strip characters outside `allowed_chars` and collapse whitespace."""
    text = "".join(char if char in allowed_chars else " " for char in text)
    return " ".join(text.split())
