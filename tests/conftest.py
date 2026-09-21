from pathlib import Path

import pytest

from codebreak import clean_text, get_text, ngram_frequency

TEXTS_DIR = Path(__file__).resolve().parent.parent / "texts"


@pytest.fixture(scope="session")
def english_corpus() -> str:
    return clean_text(get_text(TEXTS_DIR / "moby.txt") + get_text(TEXTS_DIR / "holmes.txt"))


@pytest.fixture(scope="session")
def unigram_freq(english_corpus):
    return ngram_frequency(english_corpus, 1)


@pytest.fixture(scope="session")
def bigram_freq(english_corpus):
    return ngram_frequency(english_corpus, 2)
