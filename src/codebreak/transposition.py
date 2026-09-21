"""Columnar transposition cipher: encipher and decipher.

The key is a permutation of column indices, derived from a keyword: sort the
keyword's letters alphabetically and record where each one came from.
"""


def phrase_to_key(phrase: str) -> tuple[int, ...]:
    """Turn a keyword into a column-order permutation, e.g. 'CODE' -> (0,2,3,1)."""
    indexed = sorted(enumerate(phrase), key=lambda pair: pair[1])
    return tuple(i for i, _ in indexed)


def permute_string(string: str, key: tuple[int, ...]) -> str:
    """Reorder `string` according to `key`, padding with '*' if too short."""
    string += "*" * (len(key) - len(string))
    return "".join(string[i] for i in key)


def transposition_encipher(message: str, key: tuple[int, ...]) -> str:
    k = len(key)
    grid = [permute_string(message[i : i + k], key) for i in range(0, len(message), k)]
    return "".join("".join(column) for column in zip(*grid))


def transposition_decipher(ciphertext: str, key: tuple[int, ...]) -> str:
    k = len(key)
    num_rows = len(ciphertext) // k
    blocks = [ciphertext[i * num_rows : (i + 1) * num_rows] for i in range(k)]

    columns = [""] * k
    for position, original_column in enumerate(key):
        columns[original_column] = blocks[position]

    rows = ("".join(columns[j][r] for j in range(k)) for r in range(num_rows))
    return "".join(rows).rstrip("*")
