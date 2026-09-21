"""Vigenere cipher: enciphering, and index-of-coincidence-based cracking.

The key length is estimated by finding the length whose column-wise index
of coincidence is closest to plain English (~0.0667); each column is then
just a Caesar shift, recoverable from its most frequent letter.
"""

from .alphabet import ALPHABET_PLAIN

ENGLISH_IC = 0.0667


def vigenere_encipher(message: str, key: str, alphabet: str = ALPHABET_PLAIN) -> str:
    cipher = []
    for i, char in enumerate(message):
        if char not in alphabet:
            cipher.append(char)
        else:
            shift = alphabet.index(key[i % len(key)])
            cipher.append(alphabet[(alphabet.index(char) + shift) % len(alphabet)])
    return "".join(cipher)


def vigenere_decipher(ciphertext: str, key: str, alphabet: str = ALPHABET_PLAIN) -> str:
    plain = []
    for i, char in enumerate(ciphertext):
        if char not in alphabet:
            plain.append(char)
        else:
            shift = alphabet.index(key[i % len(key)])
            plain.append(alphabet[(alphabet.index(char) - shift) % len(alphabet)])
    return "".join(plain)


def count_chars(text: str) -> dict[str, int]:
    """Character counts, with spaces excluded (zeroed) since they carry no
    information about the underlying letter-substitution cipher."""
    counts: dict[str, int] = {}
    for char in text:
        counts[char] = counts.get(char, 0) + 1
    counts[" "] = 0
    return counts


def index_of_coincidence(text: str) -> float:
    counts = count_chars(text)
    n = sum(counts.values())
    if n <= 1:
        return 0.0
    return sum(c * (c - 1) for c in counts.values()) / (n * (n - 1))


def estimate_key_length(
    ciphertext: str, max_len: int = 20, english_ic: float = ENGLISH_IC
) -> tuple[list[float], int]:
    """Index of coincidence for each candidate key length 1..max_len, and the
    length whose IC is closest to plain English."""
    ics = []
    for length in range(1, max_len + 1):
        segments = ["".join(ciphertext[i::length]) for i in range(length)]
        ics.append(sum(index_of_coincidence(seg) for seg in segments) / length)

    best_length = min(range(1, max_len + 1), key=lambda length: abs(ics[length - 1] - english_ic))
    return ics, best_length


def break_vigenere(
    ciphertext: str,
    guess_len: int | None = None,
    alphabet: str = ALPHABET_PLAIN,
    most_common_plain_char: str = "E",
) -> tuple[str, str]:
    """Estimate the key length, recover the key one letter at a time by
    assuming each column's most frequent ciphertext letter maps to the most
    frequent English letter, then decipher."""
    key_len = guess_len if guess_len is not None else estimate_key_length(ciphertext)[1]

    key_chars = []
    for i in range(key_len):
        segment = "".join(ciphertext[j] for j in range(i, len(ciphertext), key_len))
        frequencies = count_chars(segment)
        most_common_char = max(frequencies, key=frequencies.get)
        shift = (alphabet.index(most_common_char) - alphabet.index(most_common_plain_char)) % len(alphabet)
        key_chars.append(alphabet[shift])

    key = "".join(key_chars)
    return vigenere_decipher(ciphertext, key, alphabet), key
