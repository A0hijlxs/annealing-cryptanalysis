"""Benchmarks for the word-pattern dictionary attack.

Word-pattern matching narrows a substitution cipher's key space by matching
each cipherword's pattern (e.g. HGHHU -> 0.1.0.0.2) against a dictionary.
How much it narrows things down depends entirely on how many dictionary
words share that pattern: a word with an all-distinct-letter pattern like
CAT matches hundreds of common words, while a word like LITTLE (0.1.2.2.0.3)
matches almost none.

This measures, for phrases built from words of different pattern rarity:
the theoretical remaining key-space size (cheap to compute for any input),
and the result of actually enumerating it under a fixed wall-clock budget
per trial - which keeps this script's own total runtime predictable
regardless of how pathological a condition turns out to be, rather than
letting one bad case consume an unpredictable share of it.

Run with --quick for a fast sanity-check pass, or --full (default) for the
full sweep. Writes CSVs and plots to benchmarks/results/.
"""

import argparse
import random
import time
from collections import defaultdict

import matplotlib.pyplot as plt
from _common import RESULTS_DIR, TEXTS_DIR, write_csv

from codebreak import Dictionary, get_pattern, random_substitution_key, substitution_encipher
from codebreak.wordpatterns import intersect_mappings, valid_combinations


def bucket_words_by_rarity(dictionary: Dictionary) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for word in dictionary.words:
        if len(word) < 4:
            continue
        n_matches = len(dictionary.patterns[get_pattern(word)])
        if n_matches <= 3:
            buckets["rare"].append(word)
        elif n_matches <= 50:
            buckets["medium"].append(word)
        else:
            buckets["common"].append(word)
    return buckets


CONDITIONS = {
    "all_rare": ("rare", "rare", "rare"),
    "all_medium": ("medium", "medium", "medium"),
    "mixed": ("rare", "medium", "common"),
    "all_common": ("common", "common", "common"),
}


def bounded_brute_force(dictionary: Dictionary, message: str, time_budget: float, tolerance: float = 0.8):
    """Same enumeration `Dictionary.brute_force` does, but stops after
    `time_budget` seconds and reports how far it got, using only the
    library's public building blocks."""
    maps = intersect_mappings([dictionary.word_mapping(word) for word in message.split()])
    chars = tuple(maps.keys())
    lists = tuple(tuple(values) for values in maps.values())

    candidates = []
    decipher_dict = {" ": " "}
    examined = 0
    completed = True
    t0 = time.time()
    for key in valid_combinations(lists):
        examined += 1
        decipher_dict.update(dict(zip(chars, key)))
        attempt = "".join(decipher_dict[char] for char in message)
        if dictionary.is_english(attempt, tolerance):
            candidates.append(attempt)
        if examined % 2000 == 0 and time.time() - t0 > time_budget:
            completed = False
            break

    return {
        "elapsed": time.time() - t0,
        "examined": examined,
        "candidates": candidates,
        "completed": completed,
    }


def run_trial(dictionary, buckets, rarities, time_budget, seed):
    rng = random.Random(seed)
    words = [rng.choice(buckets[rarity]) for rarity in rarities]
    plaintext = " ".join(words)
    key = random_substitution_key(rng=rng)
    cipher = substitution_encipher(plaintext, key)

    space_size = dictionary.reduced_key_space_size(cipher)
    outcome = bounded_brute_force(dictionary, cipher, time_budget)
    candidates = outcome.pop("candidates")

    return {
        "plaintext": plaintext,
        "space_size": space_size,
        "n_candidates": len(candidates),
        "found_plaintext": plaintext in candidates,
        **outcome,
    }


def experiment_search_space(dictionary, buckets, trials, time_budget):
    print(f"[search space] conditions={list(CONDITIONS)} trials={trials} time_budget={time_budget}s")
    rows = []
    for condition, rarities in CONDITIONS.items():
        sizes, elapsed_times, examined_counts, completions = [], [], [], []
        for t in range(trials):
            result = run_trial(
                dictionary, buckets, rarities, time_budget, seed=hash((condition, t)) & 0xFFFFFFFF
            )
            rows.append({"condition": condition, "trial": t, **result})
            sizes.append(result["space_size"])
            elapsed_times.append(result["elapsed"])
            examined_counts.append(result["examined"])
            completions.append(result["completed"])

        avg_size = sum(sizes) / len(sizes)
        completion_rate = sum(completions) / len(completions)
        avg_examined = sum(examined_counts) / len(examined_counts)
        print(
            f"  {condition:12s}  avg search space={avg_size:,.0f}"
            f"  completed within budget={completion_rate:.0%}"
            f"  avg combinations examined={avg_examined:,.0f}"
        )

    write_csv(
        RESULTS_DIR / "wordpatterns_search_space.csv",
        rows,
        [
            "condition",
            "trial",
            "plaintext",
            "space_size",
            "elapsed",
            "examined",
            "n_candidates",
            "found_plaintext",
            "completed",
        ],
    )
    return rows


def plot_results(rows, trials, time_budget):
    conditions = list(CONDITIONS)
    avg_sizes = [sum(r["space_size"] for r in rows if r["condition"] == c) / trials for c in conditions]
    completion_rates = [sum(r["completed"] for r in rows if r["condition"] == c) / trials for c in conditions]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    ax1.bar(conditions, avg_sizes)
    ax1.set_ylabel("Average theoretical key-space size")
    ax1.set_title("Search space by word-pattern rarity")
    ax1.set_yscale("log")
    ax1.grid(alpha=0.3, axis="y")

    ax2.bar(conditions, completion_rates)
    ax2.set_ylabel("Fraction enumerated to completion")
    ax2.set_title(f"Tractability within a {time_budget:g}s budget")
    ax2.set_ylim(0, 1.05)
    ax2.grid(alpha=0.3, axis="y")

    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "wordpatterns_search_space.png", dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--quick", action="store_true", help="fast sanity-check pass instead of the full sweep"
    )
    args = parser.parse_args()

    dictionary = Dictionary.from_file(TEXTS_DIR / "google.txt")
    buckets = bucket_words_by_rarity(dictionary)
    print({k: len(v) for k, v in buckets.items()})

    trials = 5 if args.quick else 30
    time_budget = 1.0 if args.quick else 2.0

    t0 = time.time()
    rows = experiment_search_space(dictionary, buckets, trials, time_budget)
    plot_results(rows, trials, time_budget)
    print(f"Total time: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
