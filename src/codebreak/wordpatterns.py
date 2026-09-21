"""Pattern-based dictionary attack for substitution ciphers with word spacing.

Every plaintext word and its cipherword share the same "word pattern"
(e.g. HGHHU and its plaintext both have pattern 0.1.0.0.2 - first letter is
0, first occurrence of each new letter increments). Matching a cipherword's
pattern against a dictionary narrows down which plaintext letters each
cipherletter could map to, often enough to brute-force the remaining key
space directly. This makes short messages tractable even when there isn't
enough text for frequency analysis.
"""

from collections.abc import Iterable


def get_pattern(word: str) -> str:
    """Word pattern of `word`, e.g. 'HGHHU' -> '0.1.0.0.2'."""
    seen: dict[str, str] = {}
    for char in word:
        if char not in seen:
            seen[char] = str(len(seen))
    return ".".join(seen[char] for char in word)


def all_patterns(words: Iterable[str]) -> dict[str, list[str]]:
    """Group `words` by word pattern."""
    patterns: dict[str, list[str]] = {}
    for word in words:
        patterns.setdefault(get_pattern(word), []).append(word)
    return patterns


def intersect(sets: list[set]) -> set:
    if len(sets) == 1:
        return sets[0]
    return sets[0] & intersect(sets[1:])


def union(items: list):
    """Reduce `items` with `|` - works for both sets (union) and dicts
    (merge), which is exactly what `intersect_mappings` needs below."""
    if len(items) == 1:
        return items[0]
    return items[0] | union(items[1:])


def intersect_mappings(maps: list[dict[str, set]]) -> dict[str, set]:
    """Intersect several cipherletter->possible-plaintext-letters mappings."""
    keys = union(maps).keys() if maps else []
    new_map: dict[str, set] = {}
    for key in keys:
        possibilities = [m[key] for m in maps if m.get(key)]
        new_map[key] = intersect(possibilities)
    return new_map


def valid_combinations(lists: tuple[tuple, ...], current_combo=(), used_items=frozenset()):
    """Yield combinations of one item per list, excluding any combination
    that reuses the same plaintext letter for two different cipherletters."""
    if len(current_combo) == len(lists):
        yield current_combo
    else:
        index = len(current_combo)
        for item in lists[index]:
            if item not in used_items:
                yield from valid_combinations(lists, current_combo + (item,), used_items | {item})


class Dictionary:
    """A wordlist grouped by word pattern, for pattern-matching attacks."""

    def __init__(self, words: Iterable[str]):
        self.words = set(words)
        self.patterns = all_patterns(self.words)

    @classmethod
    def from_file(cls, path: str) -> "Dictionary":
        with open(path, "r") as f:
            return cls(f.read().upper().splitlines())

    def is_english(self, sentence: str, tolerance: float) -> bool:
        words = sentence.split()
        if not words:
            return False
        count = sum(1 for word in words if word in self.words)
        return count / len(words) > tolerance

    def word_mapping(self, word: str) -> dict[str, set[str]]:
        """Possible plaintext letters for each cipherletter in `word`,
        inferred from every dictionary word sharing its pattern."""
        pattern = get_pattern(word)
        possible_words = self.patterns.get(pattern)
        if not possible_words:
            raise ValueError(f"no dictionary word matches the pattern of {word!r} ({pattern})")

        mapping: dict[str, set[str]] = {}
        for letter, chars in zip(word, zip(*possible_words)):
            mapping.setdefault(letter, set()).update(chars)
        return mapping

    def _reduced_mapping(self, message: str) -> dict[str, set[str]]:
        return intersect_mappings([self.word_mapping(word) for word in message.split()])

    def reduced_key_space_size(self, message: str) -> int:
        """Number of decryption keys remaining after word-pattern matching
        narrows each cipherletter's possible plaintext letters. This is the
        size `brute_force` would have to enumerate (before excluding
        combinations that reuse a plaintext letter, which only shrinks it
        further)."""
        size = 1
        for values in self._reduced_mapping(message).values():
            size *= len(values)
        return size

    def brute_force(self, message: str, tolerance: float = 0.8) -> list[str]:
        """Reduce the key space via word-pattern matching, then brute-force
        the remaining combinations, returning every attempt that reads as
        English above `tolerance`."""
        maps = self._reduced_mapping(message)
        chars = tuple(maps.keys())
        lists = tuple(tuple(values) for values in maps.values())

        candidates = []
        decipher_dict = {" ": " "}
        for key in valid_combinations(lists):
            decipher_dict.update(dict(zip(chars, key)))
            attempt = "".join(decipher_dict[char] for char in message)
            if self.is_english(attempt, tolerance):
                candidates.append(attempt)
        return candidates
