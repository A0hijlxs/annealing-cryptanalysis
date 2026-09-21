"""Shared helpers for the benchmark scripts: corpus loading, trial
aggregation, and CSV/plot output."""

import csv
import statistics
from pathlib import Path

from codebreak import clean_text, get_text

BENCH_DIR = Path(__file__).resolve().parent
TEXTS_DIR = BENCH_DIR.parent / "texts"
RESULTS_DIR = BENCH_DIR / "results"


def load_english_corpus() -> str:
    return clean_text(get_text(TEXTS_DIR / "moby.txt") + get_text(TEXTS_DIR / "holmes.txt"))


def mean_std(values: list[float]) -> tuple[float, float]:
    if len(values) < 2:
        return (values[0] if values else 0.0), 0.0
    return statistics.mean(values), statistics.stdev(values)


def proportion_se(successes: list[bool]) -> tuple[float, float]:
    """Sample proportion and its standard error (sqrt(p(1-p)/n)) - the
    appropriate spread measure for a success/fail rate, unlike a generic
    sample stdev which can imply values outside [0, 1]."""
    n = len(successes)
    if n == 0:
        return 0.0, 0.0
    p = sum(successes) / n
    return p, (p * (1 - p) / n) ** 0.5


def clip_error(means: list[float], stds: list[float], bounds: tuple[float, float]) -> list[list[float]]:
    """Asymmetric (lower, upper) error bar magnitudes clipped so mean +/-
    error stays within `bounds` - for metrics like accuracy or a rate that
    can't actually go outside [0, 1], a symmetric stdev error bar can
    otherwise imply an impossible value."""
    lo, hi = bounds
    return [
        [min(s, m - lo) for m, s in zip(means, stds)],
        [min(s, hi - m) for m, s in zip(means, stds)],
    ]


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def errorbar_plot(
    x: list[float],
    means: list[float],
    stds: list[float],
    xlabel: str,
    ylabel: str,
    title: str,
    path: Path,
    xscale: str = "linear",
    y_bounds: tuple[float, float] | None = None,
) -> None:
    import matplotlib.pyplot as plt

    RESULTS_DIR.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.5))

    yerr = clip_error(means, stds, y_bounds) if y_bounds is not None else stds

    ax.errorbar(x, means, yerr=yerr, marker="o", capsize=3)
    if y_bounds is not None:
        ax.set_ylim(y_bounds[0] - 0.05, y_bounds[1] + 0.05)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xscale(xscale)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
