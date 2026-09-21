"""Benchmarks for the Metropolis-algorithm substitution solver.

Three experiments, each run over many random (excerpt, key) trials per
condition so results reflect a distribution rather than a single run:

1. Recovery accuracy vs. message length.
2. Recovery accuracy vs. n-gram order used for scoring.
3. Recovery accuracy vs. cooling schedule (t_min/t_max/iterations).

Run with --quick for a fast sanity-check pass, or --full (default) for the
full sweep. Writes CSVs and plots to benchmarks/results/.
"""

import argparse
import random
import time

import matplotlib.pyplot as plt
from _common import RESULTS_DIR, clip_error, errorbar_plot, load_english_corpus, mean_std, write_csv

from codebreak import (
    NgramScorer,
    metropolis_algorithm,
    ngram_frequency,
    random_substitution_key,
    substitution_encipher,
    unigram_attack,
)


def run_trial(corpus, unigram_freq, scorer, length, t_min, t_max, iterations, seed):
    rng = random.Random(seed)
    offset = rng.randrange(0, len(corpus) - length)
    excerpt = corpus[offset : offset + length]
    key = random_substitution_key(rng=rng)
    cipher = substitution_encipher(excerpt, key)
    guess = unigram_attack(cipher, unigram_freq)

    t0 = time.time()
    result = metropolis_algorithm(guess, scorer, t_min=t_min, t_max=t_max, iterations=iterations, rng=rng)
    elapsed = time.time() - t0

    accuracy = sum(a == b for a, b in zip(result.message, excerpt)) / length
    return accuracy, elapsed


def experiment_length(corpus, unigram_freq, bigram_freq, lengths, trials):
    print(f"[length] lengths={lengths} trials={trials}")
    scorer = NgramScorer(bigram_freq)
    rows = []
    means, stds = [], []
    for length in lengths:
        accuracies = []
        for t in range(trials):
            scorer.clear_cache()
            acc, elapsed = run_trial(
                corpus, unigram_freq, scorer, length, 0.5, 5, 20_000, seed=1000 * length + t
            )
            accuracies.append(acc)
            rows.append({"length": length, "trial": t, "accuracy": acc, "seconds": elapsed})
        m, s = mean_std(accuracies)
        means.append(m)
        stds.append(s)
        print(f"  length={length:5d}  accuracy={m:.3f} +/- {s:.3f}")

    write_csv(RESULTS_DIR / "substitution_length.csv", rows, ["length", "trial", "accuracy", "seconds"])
    errorbar_plot(
        lengths,
        means,
        stds,
        xlabel="Message length (characters)",
        ylabel="Character-level recovery accuracy",
        title="Metropolis solver: accuracy vs. message length",
        path=RESULTS_DIR / "substitution_length.png",
        xscale="log",
        y_bounds=(0.0, 1.0),
    )


def experiment_ngram_order(corpus, unigram_freq, freqs_by_order, length, trials):
    orders = sorted(freqs_by_order)
    print(f"[ngram order] orders={orders} length={length} trials={trials}")
    rows = []
    means, stds = [], []
    for n in orders:
        scorer = NgramScorer(freqs_by_order[n])
        accuracies = []
        for t in range(trials):
            acc, elapsed = run_trial(corpus, unigram_freq, scorer, length, 0.5, 5, 20_000, seed=2000 * n + t)
            accuracies.append(acc)
            rows.append({"n": n, "trial": t, "accuracy": acc, "seconds": elapsed})
        m, s = mean_std(accuracies)
        means.append(m)
        stds.append(s)
        print(f"  n={n}  accuracy={m:.3f} +/- {s:.3f}")

    write_csv(RESULTS_DIR / "substitution_ngram_order.csv", rows, ["n", "trial", "accuracy", "seconds"])

    fig, ax = plt.subplots(figsize=(6, 4.5))
    yerr = clip_error(means, stds, (0.0, 1.0))
    ax.bar([str(n) for n in orders], means, yerr=yerr, capsize=4)
    ax.set_ylim(0.0, 1.05)
    ax.set_xlabel("n-gram order used for scoring")
    ax.set_ylabel("Character-level recovery accuracy")
    ax.set_title("Metropolis solver: accuracy vs. n-gram order")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "substitution_ngram_order.png", dpi=150)
    plt.close(fig)


def experiment_cooling_schedule(
    corpus, unigram_freq, bigram_freq, t_configs, iteration_counts, length, trials
):
    print(f"[cooling] t_configs={t_configs} iterations={iteration_counts} length={length} trials={trials}")
    scorer = NgramScorer(bigram_freq)
    rows = []

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for t_min, t_max in t_configs:
        means, stds = [], []
        for iterations in iteration_counts:
            accuracies = []
            for t in range(trials):
                scorer.clear_cache()
                acc, elapsed = run_trial(
                    corpus,
                    unigram_freq,
                    scorer,
                    length,
                    t_min,
                    t_max,
                    iterations,
                    seed=hash((t_min, t_max, iterations, t)) & 0xFFFFFFFF,
                )
                accuracies.append(acc)
                rows.append(
                    {
                        "t_min": t_min,
                        "t_max": t_max,
                        "iterations": iterations,
                        "trial": t,
                        "accuracy": acc,
                        "seconds": elapsed,
                    }
                )
            m, s = mean_std(accuracies)
            means.append(m)
            stds.append(s)
        print(f"  t_min={t_min} t_max={t_max}  accuracies={[round(m, 3) for m in means]}")
        yerr = clip_error(means, stds, (0.0, 1.0))
        ax.errorbar(
            iteration_counts, means, yerr=yerr, marker="o", capsize=3, label=f"t_min={t_min}, t_max={t_max}"
        )

    ax.set_xlabel("Iterations")
    ax.set_ylabel("Character-level recovery accuracy")
    ax.set_title("Metropolis solver: accuracy vs. cooling schedule")
    ax.set_ylim(0.0, 1.05)
    ax.set_xscale("log")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "substitution_cooling_schedule.png", dpi=150)
    plt.close(fig)

    write_csv(
        RESULTS_DIR / "substitution_cooling_schedule.csv",
        rows,
        ["t_min", "t_max", "iterations", "trial", "accuracy", "seconds"],
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--quick", action="store_true", help="fast sanity-check pass instead of the full sweep"
    )
    args = parser.parse_args()

    corpus = load_english_corpus()
    unigram_freq = ngram_frequency(corpus, 1)
    freqs_by_order = {n: ngram_frequency(corpus, n) for n in (1, 2, 3, 4)}
    bigram_freq = freqs_by_order[2]

    if args.quick:
        lengths = [100, 500, 1000]
        length_trials = 5
        ngram_length = 300
        ngram_trials = 5
        cooling_t_configs = [(0.5, 5), (0.01, 1)]
        cooling_iterations = [5_000, 20_000]
        cooling_length = 300
        cooling_trials = 5
    else:
        lengths = [50, 100, 200, 500, 1000, 2000]
        length_trials = 25
        ngram_length = 500
        ngram_trials = 25
        cooling_t_configs = [(0.5, 5), (0.1, 10), (1, 50), (0.01, 1)]
        cooling_iterations = [5_000, 20_000, 50_000]
        cooling_length = 500
        cooling_trials = 15

    t0 = time.time()
    experiment_length(corpus, unigram_freq, bigram_freq, lengths, length_trials)
    experiment_ngram_order(corpus, unigram_freq, freqs_by_order, ngram_length, ngram_trials)
    experiment_cooling_schedule(
        corpus,
        unigram_freq,
        bigram_freq,
        cooling_t_configs,
        cooling_iterations,
        cooling_length,
        cooling_trials,
    )
    print(f"Total time: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
