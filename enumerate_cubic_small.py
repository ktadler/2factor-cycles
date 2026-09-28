#!/usr/bin/env python3
"""Exact d=3 at n=8 and n=12: all perfect-matching complements.

40 graphs, seeds 1..40. Writes results/exact_d3_n{n}.jsonl.
The larger exact cubic batches are enumerate_cubic.py with Random(20260806).
"""
import json, os, sys
import networkx as nx

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from enumerate_cubic import enumerate_pm_cycle_counts

OUTDIR = os.path.join(HERE, "results")
os.makedirs(OUTDIR, exist_ok=True)


def one(n, N=40):
    path = os.path.join(OUTDIR, "exact_d3_n%d.jsonl" % n)
    means = []
    with open(path, "w") as f:
        for i in range(N):
            seed = 1 + i
            G = nx.random_regular_graph(3, n, seed=seed)
            edges = list(G.edges())
            adj = [[] for _ in range(n)]
            for u, v in edges:
                adj[u].append(v)
                adj[v].append(u)
            counts = enumerate_pm_cycle_counts(n, edges, adj)
            npm = sum(counts.values())
            mean = sum(c * v for c, v in counts.items()) / npm
            means.append(mean)
            rec = {"d": 3, "n": n, "i": i, "seed": seed, "mean": mean,
                   "npm": npm,
                   "counts": {str(k): v for k, v in sorted(counts.items())}}
            f.write(json.dumps(rec) + "\n")
    m = sum(means) / len(means)
    sd = (sum((x - m) ** 2 for x in means) / len(means)) ** 0.5
    print("n=%d N=%d seeds 1..%d mean=%.4f sd=%.4f" % (n, N, N, m, sd))


if __name__ == "__main__":
    one(8)
    one(12)
