#!/usr/bin/env python3
"""Three sim panels: (a) exact vs KS at n<=80, (b) KS log-n, (c) degree."""
import glob, json, math, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EULER = 0.5772156649015329

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "mathtext.fontset": "dejavusans",
    "axes.unicode_minus": False,
    "legend.frameon": False,
})

# exact quenched: (n, mean_of_means, sd_across_graphs, n_graphs)
EXACT = [
    (8, 1.3348, 0.1607, 40),
    (12, 1.5207, 0.1996, 40),
    (16, 1.67, 0.19, 40),
    (24, 1.88, 0.25, 40),
    (32, 2.06, 0.36, 40),
    (48, 2.26, 0.26, 40),
    (64, 2.34, 0.14, 20),
    (80, 2.5255, 0.2317, 10),
]


def girth(n):
    return 0.5 * math.log(n) + EULER / 2.0 + math.log(2.0) - 0.75


def load_cells(folder):
    out = {}
    for path in glob.glob(os.path.join(folder, "*.jsonl")):
        if os.path.basename(path).startswith("exact"):
            continue
        xs, d, n = [], None, None
        for line in open(path):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("x") is None:
                continue
            xs.append(r["x"])
            d, n = r["d"], r["n"]
        if xs and d is not None:
            m = sum(xs) / len(xs)
            sd = (sum((v - m) ** 2 for v in xs) / max(len(xs) - 1, 1)) ** 0.5
            se = sd / (len(xs) ** 0.5)
            out[(d, n)] = {"xs": xs, "mean": m, "sd": sd, "se": se, "N": len(xs)}
    return out


def load_exact_d4(folder):
    """Per-graph exact means -> (n, mean_of_means, sd, N)."""
    out = []
    for path in sorted(glob.glob(os.path.join(folder, "exact_d4_n*.jsonl"))):
        means, n = [], None
        for line in open(path):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("mean") is None:
                continue
            means.append(r["mean"])
            n = r["n"]
        if means and n is not None:
            m = sum(means) / len(means)
            sd = (sum((x - m) ** 2 for x in means) / max(len(means) - 1, 1)) ** 0.5
            out.append((n, m, sd, len(means)))
    return sorted(out)


def main():
    folder = os.path.join(HERE, "results")
    cells = load_cells(folder)
    d3 = sorted((n, c) for (d, n), c in cells.items() if d == 3)
    d4 = sorted((n, c) for (d, n), c in cells.items() if d == 4)
    exact4 = load_exact_d4(folder)
    if not exact4:
        exact4 = [
            (8, 1.2859, 0.0082, 40),
            (12, 1.4876, 0.0461, 40),
            (16, 1.6211, 0.0465, 40),
            (20, 1.7441, 0.0795, 40),
            (24, 1.8246, 0.0657, 40),
        ]

    # --- (a) small n: exact vs KS, log2 axis ---
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    ns = np.logspace(math.log2(7.5), math.log2(84), 80, base=2)
    ax.plot(ns, [girth(n) for n in ns], "k-", lw=1.3, label="simple graph")
    ax.errorbar([p[0] for p in EXACT], [p[1] for p in EXACT],
                yerr=[p[2] / (p[3] ** 0.5) for p in EXACT],
                fmt="o", ms=6, color="tab:blue", capsize=2,
                label="exact uniform, d=3")
    if exact4:
        ax.errorbar([p[0] for p in exact4], [p[1] for p in exact4],
                    yerr=[p[2] / (p[3] ** 0.5) for p in exact4],
                    fmt="^", ms=6, color="tab:green", capsize=2,
                    label="exact uniform, d=4")
    small3 = [(n, c) for n, c in d3 if n <= 80]
    if small3:
        ax.errorbar([n * (2 ** 0.06) for n, c in small3],
                    [c["mean"] for n, c in small3],
                    yerr=[c["se"] for n, c in small3],
                    fmt="s", ms=5, color="tab:red", capsize=2,
                    label="KS+blossom, d=3")
    small4 = [(n, c) for n, c in d4 if n <= 80]
    if small4:
        ax.errorbar([n * (2 ** -0.06) for n, c in small4],
                    [c["mean"] for n, c in small4],
                    yerr=[c["se"] for n, c in small4],
                    fmt="D", ms=5, color="tab:orange", capsize=2,
                    label="KS+blossom, d=4")
    ax.set_xscale("log", base=2)
    ax.set_xlabel(r"$n$")
    ax.set_ylabel("mean cycle count")
    ticks = [8, 12, 16, 24, 32, 48, 64, 80]
    ax.set_xticks(ticks)
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.legend(fontsize=7, ncol=2)
    ax.grid(alpha=0.25)
    fig.savefig(os.path.join(HERE, "fig_small_exact.png"), dpi=180, bbox_inches="tight")
    print("wrote fig_small_exact.png")

    # --- (b) KS only, log n, every degree we have for n>=100 ---
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    ns = np.logspace(1.9, 6.05, 80)
    ax.plot(ns, [girth(n) for n in ns], "k-", lw=1.3, label="simple graph")
    styles = {
        3: ("s", "tab:red"),
        4: ("D", "tab:orange"),
        10: ("^", "tab:green"),
        30: ("v", "tab:purple"),
        50: ("o", "tab:brown"),
    }
    by_d = {}
    for (d, n), c in cells.items():
        logn = math.log10(n)
        if n >= 100 and c["N"] >= 100 and abs(logn - round(logn)) < 1e-6:
            by_d.setdefault(d, []).append((n, c))
    for i, d in enumerate(sorted(by_d)):
        pts = []
        for n, c in sorted(by_d[d]):
            xs = c["xs"][:100]
            m = sum(xs) / len(xs)
            sd = (sum((v - m) ** 2 for v in xs) / max(len(xs) - 1, 1)) ** 0.5
            se = sd / (len(xs) ** 0.5)
            pts.append((n, {"mean": m, "se": se, "N": len(xs)}))
        fmt, color = styles.get(d, ("s", "0.4"))
        # nudge shared n so markers do not sit on each other
        dodge = 10 ** (0.045 * (i - 2))
        label = "d=%d" % d
        ax.errorbar([n * dodge for n, c in pts], [c["mean"] for n, c in pts],
                    yerr=[c["se"] for n, c in pts],
                    fmt=fmt, ms=5, color=color, capsize=2,
                    label=label)
    ax.set_xscale("log")
    ax.set_xlabel(r"$n$")
    ax.set_ylabel("mean cycle count")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(alpha=0.25)
    fig.savefig(os.path.join(HERE, "fig_mean_all.png"), dpi=180, bbox_inches="tight")
    print("wrote fig_mean_all.png from", folder)

    # --- (c) degree at n=10^4 ---
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    ax.axhline(girth(10000), color="k", lw=1.2, label=r"simple graph at $n=10^{4}$")
    deg_order = [3, 4, 10, 30, 50]
    xs, ys, yerr = [], [], []
    for i, d in enumerate(deg_order):
        c = cells.get((d, 10000))
        if c:
            xs.append(i)
            ys.append(c["mean"])
            yerr.append(c["se"])
    if xs:
        ax.errorbar(xs, ys, yerr=yerr, fmt="s", ms=7, color="tab:red",
                    capsize=4, elinewidth=1.2,
                    label="KS+blossom, 1 draw / independent G")
    ax.set_xticks(range(len(deg_order)))
    ax.set_xticklabels([str(d) for d in deg_order])
    ax.set_xlim(-0.5, len(deg_order) - 0.5)
    ax.set_xlabel(r"degree $d$")
    ax.set_ylabel("mean cycle count")
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=2)
    ax.grid(axis="y", alpha=0.25)
    fig.savefig(os.path.join(HERE, "fig_degree_indep.png"), dpi=180, bbox_inches="tight")
    print("wrote fig_degree_indep.png")

    # --- dist: same layout as the August make_figures.py plot ---
    write_dist(cells)


def annealed_girth_pgf_dist(n, cmax):
    """P(X'=c) for c=1..cmax from exp(u C), C(x)=sum_{k>=3} x^k/(2k).

    Coefficients satisfy n a_n = (n-1) a_{n-1} + (u/2) a_{n-3}.
    """
    cap = max(cmax, 40)
    a = np.zeros(cap + 1)
    b = np.zeros(cap + 1)
    d = np.zeros(cap + 1)
    a[0] = 1.0
    for m in range(1, n + 1):
        e = ((m - 1) / m) * a
        e[1:] += d[:-1] / (2 * m)
        d, b, a = b, a, e
    tot = a[1:].sum()
    return (a[1:cmax + 1] / tot).tolist()


def write_dist(cells):
    """Two panels: largest substantial run at d=3 and at d=4.

    Bars against the annealed law. The same legend sits inside each panel.
    """
    from collections import Counter
    specs = []
    for d in (3, 4):
        cands = [(n, c) for (dd, n), c in cells.items() if dd == d and c["N"] >= 30]
        if not cands:
            continue
        n, c = max(cands, key=lambda t: (t[0], t[1]["N"]))
        specs.append((d, n, c))
    if not specs:
        print("no cell for fig_dist")
        return
    gmax = 1
    prepared = []
    for d, n, c in specs:
        cnt = Counter(c["xs"])
        gmax = max(gmax, max(cnt) + 2)
        prepared.append((d, n, c, cnt))
    gcs = np.arange(1, gmax + 1)
    colors = {3: "C3", 4: "C1"}
    ymax = 0.0
    fig, axes = plt.subplots(len(prepared), 1, figsize=(6.6, 3.15 * len(prepared)), sharex=True, sharey=True)
    axes = np.atleast_1d(axes)
    for i, (ax, (d, n, c, cnt)) in enumerate(zip(axes, prepared)):
        ann = annealed_girth_pgf_dist(n, gmax)
        gp = np.array([cnt.get(int(v), 0) / c["N"] for v in gcs])
        ax.plot(gcs, ann, "k--", lw=1.3, zorder=1, label="theory")
        ax.bar(gcs, gp, width=0.72, color=colors.get(d, "C3"), alpha=0.75, zorder=2,
               label="KS+blossom")
        ymax = max(ymax, float(gp.max()), float(max(ann)))
        ax.set_ylabel("probability")
        ax.grid(axis="y", alpha=0.25)
        ax.legend(fontsize=8, loc="upper right")
    axes[0].set_ylim(0, ymax * 1.18)
    axes[-1].set_xlim(0.4, gmax + 0.6)
    axes[-1].xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    axes[-1].xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%d"))
    axes[-1].set_xlabel(r"number of cycles $c$")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_dist.png"), dpi=200)
    print("wrote fig_dist.png", [(d, n, c["N"]) for d, n, c, _ in prepared])


def write_dist_unused(cells):
    from collections import Counter
    panels = [None] + [d for d in (3, 4, 10, 30, 50) if (d, 10000) in cells]
    ncols = 3
    nrows = (len(panels) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(10.2, 3.15 * nrows))
    axes = np.atleast_1d(axes).ravel()
    for ax, d in zip(axes, panels):
        if d is None:
            ann = annealed_girth_pgf_dist(64, 8)
            ax.plot(range(1, 9), ann, "ko-", ms=3.5, lw=1, label=r"annealed, $n=64$")
            ax.legend(fontsize=8)
        else:
            c = cells[(d, 10000)]
            cnt = Counter(c["xs"])
            gcs = sorted(cnt)
            gp = [cnt[v] / len(c["xs"]) for v in gcs]
            ax.bar(gcs, gp, width=0.7, color="C3", alpha=0.8,
                   label="KS, d=%d, N=%d" % (d, c["N"]))
            gmax = max(max(gcs) + 1, 8)
            ann4 = annealed_girth_pgf_dist(10000, gmax)
            ax.plot(range(1, gmax + 1), ann4, "ko-", ms=3, lw=1,
                    label=r"annealed, $n=10^{4}$")
            ax.legend(fontsize=7)
        ax.set_xlabel(r"number of cycles $c$")
        ax.set_ylabel("probability")
    for ax in axes[len(panels):]:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_dist.png"), dpi=200)
    print("wrote fig_dist.png")


if __name__ == "__main__":
    main()
