import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # annealing-cryptanalysis

    A tour of the toolkit: cyclic shifts, general substitution ciphers
    cracked with a simulated-annealing (Metropolis algorithm) solver, a
    word-pattern dictionary attack for short messages, columnar
    transposition, and Vigenere cryptanalysis via index of coincidence.
    """)


@app.cell
def _():
    import random
    from pathlib import Path

    import matplotlib.pyplot as plt

    import codebreak

    TEXTS_DIR = Path(__file__).resolve().parent / "texts"
    return TEXTS_DIR, codebreak, plt, random


@app.cell
def _(mo):
    mo.md(r"""
    ## Cyclic (Caesar) shift
    """)


@app.cell
def _(codebreak):
    cyclic_message = "MEET ME BY THE OLD OAK TREE AT NOON"
    cyclic_cipher = codebreak.cyclic_encipher(cyclic_message, shift=7)
    cyclic_recovered = codebreak.cyclic_decipher(cyclic_cipher, shift=7)
    cyclic_message, cyclic_cipher, cyclic_recovered


@app.cell
def _(mo):
    mo.md(r"""
    ## Substitution ciphers and frequency analysis

    A reference corpus gives unigram/bigram frequencies for English,
    which a unigram attack uses to make a first, usually rough, guess at
    a substitution key by matching character frequencies.
    """)


@app.cell
def _(TEXTS_DIR, codebreak):
    corpus = codebreak.clean_text(
        codebreak.get_text(TEXTS_DIR / "moby.txt") + codebreak.get_text(TEXTS_DIR / "holmes.txt")
    )
    unigram_freq = codebreak.ngram_frequency(corpus, 1)
    bigram_freq = codebreak.ngram_frequency(corpus, 2)
    return bigram_freq, corpus, unigram_freq


@app.cell
def _(codebreak, corpus, random):
    sub_excerpt = corpus[20000:20600]
    sub_key = codebreak.random_substitution_key(rng=random.Random(7))
    sub_ciphertext = codebreak.substitution_encipher(sub_excerpt, sub_key)
    sub_ciphertext
    return sub_ciphertext, sub_excerpt


@app.cell
def _(codebreak, sub_ciphertext, unigram_freq):
    sub_guess = codebreak.unigram_attack(sub_ciphertext, unigram_freq)
    sub_guess
    return (sub_guess,)


@app.cell
def _(mo):
    mo.md(r"""
    ## Simulated annealing (Metropolis algorithm)

    Starting from the unigram guess above, the solver repeatedly swaps
    two alphabet characters throughout the message, scoring each
    candidate against bigram frequencies and cooling a temperature
    parameter over the run so it explores broadly at first and settles
    later.
    """)


@app.cell
def _(bigram_freq, codebreak, random, sub_excerpt, sub_guess):
    metro_scorer = codebreak.NgramScorer(bigram_freq)
    metro_result = codebreak.metropolis_algorithm(
        sub_guess,
        metro_scorer,
        t_min=0.5,
        t_max=5,
        iterations=20_000,
        rng=random.Random(1),
        record=True,
    )
    metro_accuracy = sum(a == b for a, b in zip(metro_result.message, sub_excerpt)) / len(sub_excerpt)
    metro_result.message, metro_accuracy
    return (metro_result,)


@app.cell
def _(metro_result, plt):
    fig, ax = plt.subplots()
    ax.plot(metro_result.trace.scores)
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Score (log-likelihood)")
    ax.set_title("Metropolis algorithm: score per iteration")
    fig


@app.cell
def _(mo):
    mo.md(r"""
    ## Word-pattern dictionary attack

    Short messages don't have enough text for frequency analysis, but
    every plaintext word and its cipherword share the same "word
    pattern" (e.g. `PUPPY` -> `0.1.0.0.2`). Matching that pattern
    against a dictionary narrows the key space enough to brute-force
    directly.
    """)


@app.cell
def _(TEXTS_DIR, codebreak, random):
    word_dictionary = codebreak.Dictionary.from_file(TEXTS_DIR / "google.txt")
    word_phrase = "LITTLE PUPPY"
    word_key = codebreak.random_substitution_key(rng=random.Random(0))
    word_cipher = codebreak.substitution_encipher(word_phrase, word_key)
    word_candidates = word_dictionary.brute_force(word_cipher, tolerance=0.8)
    word_cipher, word_candidates


@app.cell
def _(mo):
    mo.md(r"""
    ## Columnar transposition
    """)


@app.cell
def _(codebreak):
    trans_message = "MEET AT THE OBSERVATORY"
    trans_key = codebreak.phrase_to_key("ENTROPY")
    trans_cipher = codebreak.transposition_encipher(trans_message, trans_key)
    trans_recovered = codebreak.transposition_decipher(trans_cipher, trans_key)
    trans_cipher, trans_recovered


@app.cell
def _(mo):
    mo.md(r"""
    ## Vigenere cipher

    Transposition and Vigenere ciphers don't change letter frequencies,
    only their arrangement, so frequency analysis alone doesn't work.
    The index of coincidence (IC) of English text is markedly higher
    than that of a well-mixed cipher, and comparing IC across candidate
    key lengths gives an estimate of the true key length; each column
    is then just a Caesar shift, recoverable from its most frequent
    letter.
    """)


@app.cell
def _(codebreak, corpus):
    vig_excerpt = corpus[:15_000].replace(" ", "")
    vig_key = "ENTROPY"
    vig_cipher = codebreak.vigenere_encipher(vig_excerpt, vig_key)
    vig_plain_ic = codebreak.index_of_coincidence(vig_excerpt)
    vig_cipher_ic = codebreak.index_of_coincidence(vig_cipher)
    vig_plain_ic, vig_cipher_ic
    return vig_cipher, vig_excerpt, vig_key


@app.cell
def _(codebreak, vig_cipher, vig_key):
    _vig_ics, vig_best_length = codebreak.estimate_key_length(vig_cipher)
    # A key length's harmonics (multiples of the true period) produce very
    # similar column statistics, so this estimate can occasionally lock onto
    # one of those instead of the true length.
    vig_best_length, len(vig_key)


@app.cell
def _(codebreak, vig_cipher, vig_excerpt, vig_key):
    vig_decrypted, vig_recovered_key = codebreak.break_vigenere(vig_cipher, guess_len=len(vig_key))
    vig_recovered_key, vig_decrypted == vig_excerpt


if __name__ == "__main__":
    app.run()
