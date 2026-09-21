"""Simple substitution ciphers: cyclic (Caesar) shifts and general key maps.

Also provides helpers to generate random substitution keys, used to build
synthetic ciphertexts for tests and benchmarks.
"""

import random

from .alphabet import ALPHABET
from .ngrams import sort_dict, ngram_frequency


def decipher(message: str, decipher_dict: dict[str, str]) -> str:
    """Replace each character of `message` using `decipher_dict`."""
    return "".join(decipher_dict[char] for char in message)


def cyclic_decipher_dict(shift: int, alphabet: str = ALPHABET) -> dict[str, str]:
    """Build a deciphering map for a cyclic (Caesar) shift of `shift` places."""
    return {char: alphabet[(i + shift) % len(alphabet)] for i, char in enumerate(alphabet)}


def cyclic_encipher(message: str, shift: int, alphabet: str = ALPHABET) -> str:
    return decipher(message, cyclic_decipher_dict(-shift, alphabet))


def cyclic_decipher(message: str, shift: int, alphabet: str = ALPHABET) -> str:
    return decipher(message, cyclic_decipher_dict(shift, alphabet))


def swap_chars(text: str, a: str, b: str) -> str:
    """Swap every occurrence of `a` and `b` in `text`."""
    text = text.replace(a, "\0")
    text = text.replace(b, a)
    return text.replace("\0", b)


def unigram_attack(cipher: str, unigram_freq: dict[str, float]) -> str:
    """Guess a decryption by matching cipher character frequencies to a
    reference unigram frequency table (most-frequent-to-most-frequent)."""
    cipher_freq = ngram_frequency(cipher, 1)
    pairs = zip(sort_dict(cipher_freq), sort_dict(unigram_freq))
    decipher_dict = {c: s for c, s in pairs}
    return decipher(cipher, decipher_dict)


def random_substitution_key(alphabet: str = ALPHABET, rng: random.Random | None = None) -> dict[str, str]:
    """A random bijective substitution key over `alphabet` (space maps to itself)."""
    rng = rng or random
    letters = [c for c in alphabet if c != " "]
    shuffled = letters[:]
    rng.shuffle(shuffled)
    key = dict(zip(letters, shuffled))
    if " " in alphabet:
        key[" "] = " "
    return key


def substitution_encipher(message: str, key: dict[str, str]) -> str:
    """Encipher `message` with a substitution key (plaintext char -> cipher char)."""
    return decipher(message, key)


def invert_key(key: dict[str, str]) -> dict[str, str]:
    return {v: k for k, v in key.items()}
