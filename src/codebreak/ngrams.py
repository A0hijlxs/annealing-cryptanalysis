"""N-gram frequency modelling and Markov scoring of candidate plaintexts."""

from math import log

# Score assigned to an n-gram that never occurs in the reference corpus.
# Taking log(~0) rather than -inf keeps scores comparable and avoids errors.
UNSEEN_NGRAM_SCORE = log(1e-10)


def sort_dict(dictionary: dict) -> dict:
    """Return a copy of `dictionary` sorted by value, descending."""
    return dict(sorted(dictionary.items(), key=lambda item: item[1], reverse=True))


def ngram_frequency(text: str, n: int) -> dict[str, float]:
    """Count all n-grams in `text` and normalise the counts to probabilities.

    Only n-grams actually present in the text are included, which keeps the
    dictionary small even for large n (most n-grams of English text never
    occur).
    """
    counts: dict[str, int] = {}
    ngrams = (text[i : i + n] for i in range(len(text) - n + 1))

    for ngram in ngrams:
        counts[ngram] = counts.get(ngram, 0) + 1

    total = sum(counts.values())
    return {gram: count / total for gram, count in counts.items()}


class NgramScorer:
    """Scores candidate plaintexts against an n-gram frequency model.

    Wraps a small memoisation cache so repeated Metropolis-algorithm swaps
    that revisit the same message don't re-tokenise and re-sum every time.
    The cache is an instance attribute (not a module global) so scorers for
    different frequency models don't collide or leak state between tests.
    """

    def __init__(self, frequencies: dict[str, float]):
        if not frequencies:
            raise ValueError("frequencies must be non-empty")
        self.frequencies = frequencies
        self.n = len(next(iter(frequencies)))
        self._cache: dict[str, float] = {}

    def score(self, message: str) -> float:
        """Sum of log-probabilities of every n-gram in `message`."""
        if message not in self._cache:
            ngrams = (message[i : i + self.n] for i in range(len(message) - self.n + 1))
            total = sum(
                log(self.frequencies[gram]) if gram in self.frequencies else UNSEEN_NGRAM_SCORE
                for gram in ngrams
            )
            self._cache[message] = round(total, 4)
        return self._cache[message]
