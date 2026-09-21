"""Benchmarks for Vigenere cryptanalysis via index of coincidence.

Two experiments, each over many random (excerpt, key) trials per condition:

1. Key recovery accuracy vs. ciphertext length per key letter, at a fixed
   key length.
2. Key-length estimation accuracy vs. true key length, at a fixed total
   ciphertext length.

Run with --quick for a fast sanity-check pass, or --full (default) for the
full sweep. Writes CSVs and plots to benchmarks/results/.
"""

import argparse
import random
import string
import time

from _common import RESULTS_DIR, errorbar_plot, load_english_corpus, proportion_se, write_csv

from codebreak import break_vigenere, vigenere_encipher
from codebreak.vigenere import estimate_key_length


def random_key(length: int, rng: random.Random) -> str:
    return "".join(rng.choice(string.ascii_uppercase) for _ in range(length))


def experiment_key_recovery(corpus, lengths_per_letter, key_length, trials):
    print(f"[key recovery] lengths_per_letter={lengths_per_letter} key_length={key_length} trials={trials}")
    rows = []
    means, stds = [], []
    for length_per_letter in lengths_per_letter:
        total_length = length_per_letter * key_length
        successes = []
        for t in range(trials):
            rng = random.Random(10_000 * length_per_letter + t)
            offset = rng.randrange(0, len(corpus) - total_length)
            excerpt = corpus[offset : offset + total_length].replace(" ", "")
            key = random_key(key_length, rng)
            cipher = vigenere_encipher(excerpt, key)

            t0 = time.time()
            _, recovered_key = break_vigenere(cipher, guess_len=key_length)
            elapsed = time.time() - t0

            success = recovered_key == key
            successes.append(success)
            rows.append(
                {
                    "length_per_letter": length_per_letter,
                    "trial": t,
                    "success": int(success),
                    "seconds": elapsed,
                }
            )
        m, s = proportion_se(successes)
        means.append(m)
        stds.append(s)
        print(f"  length_per_letter={length_per_letter:6d}  key recovery rate={m:.2f}")

    write_csv(
        RESULTS_DIR / "vigenere_key_recovery.csv",
        rows,
        ["length_per_letter", "trial", "success", "seconds"],
    )
    errorbar_plot(
        lengths_per_letter,
        means,
        stds,
        xlabel="Ciphertext length per key letter (characters)",
        ylabel="Exact key recovery rate",
        title=f"Vigenere key recovery vs. ciphertext length (key length={key_length})",
        path=RESULTS_DIR / "vigenere_key_recovery.png",
        xscale="log",
        y_bounds=(0.0, 1.0),
    )


def experiment_key_length_estimation(corpus, key_lengths, total_length, trials):
    print(f"[key length estimation] key_lengths={key_lengths} total_length={total_length} trials={trials}")
    rows = []
    means, stds = [], []
    for key_length in key_lengths:
        successes = []
        for t in range(trials):
            rng = random.Random(20_000 * key_length + t)
            offset = rng.randrange(0, len(corpus) - total_length)
            excerpt = corpus[offset : offset + total_length].replace(" ", "")
            key = random_key(key_length, rng)
            cipher = vigenere_encipher(excerpt, key)

            _, best_length = estimate_key_length(cipher)
            success = best_length == key_length
            successes.append(success)
            rows.append({"key_length": key_length, "trial": t, "success": int(success)})
        m, s = proportion_se(successes)
        means.append(m)
        stds.append(s)
        print(f"  key_length={key_length:3d}  estimate correct rate={m:.2f}")

    write_csv(RESULTS_DIR / "vigenere_key_length_estimation.csv", rows, ["key_length", "trial", "success"])
    errorbar_plot(
        key_lengths,
        means,
        stds,
        xlabel="True key length",
        ylabel="Key-length estimate correct rate",
        title=f"Vigenere key-length estimation accuracy (ciphertext length={total_length})",
        path=RESULTS_DIR / "vigenere_key_length_estimation.png",
        y_bounds=(0.0, 1.0),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--quick", action="store_true", help="fast sanity-check pass instead of the full sweep"
    )
    args = parser.parse_args()

    corpus = load_english_corpus()

    if args.quick:
        lengths_per_letter = [200, 1000, 3000]
        key_recovery_trials = 5
        key_lengths = [3, 7, 12]
        key_length_total = 50_000
        key_length_trials = 5
    else:
        lengths_per_letter = [200, 500, 1000, 2000, 3000, 5000]
        key_recovery_trials = 30
        key_lengths = [3, 5, 7, 10, 12, 15]
        key_length_total = 100_000
        key_length_trials = 20

    t0 = time.time()
    experiment_key_recovery(corpus, lengths_per_letter, key_length=8, trials=key_recovery_trials)
    experiment_key_length_estimation(corpus, key_lengths, key_length_total, key_length_trials)
    print(f"Total time: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
