"""Exact quenched cycle counts for simple cubic graphs.

A 2-factor is the complement of a perfect matching. For each
n in {16, 24, 32, 48, 64, 80} this samples simple cubic graphs from
random.Random(20260806) and enumerates every perfect matching.
n = 8 and n = 12 are enumerate_cubic_small.py.
The large-n sampler is tutte_mcm_d, driven by sample_cell.py.
"""
import json, math, random
from pathlib import Path
from collections import defaultdict

import networkx as nx


# ---------- graph generation (uniform-ish simple d-regular via networkx) ----------

def random_cubic(n, rng):
    G = nx.random_regular_graph(3, n, seed=rng.randint(0, 2**62))
    edges = list(G.edges())
    adj = [[] for _ in range(n)]
    for (u, v) in edges:
        adj[u].append(v)
        adj[v].append(u)
    return edges, adj


# ---------- exact enumeration of perfect matchings ----------

def enumerate_pm_cycle_counts(n, edges, adj):
    """Enumerate all perfect matchings; for each, count cycles of the
    complementary 2-factor. Returns dict c -> count."""
    matched = [False] * n
    partner = [-1] * n
    counts = defaultdict(int)

    seen = bytearray(n)

    def complement_cycles():
        # 2-factor = non-matching edges; each vertex has exactly two such
        # neighbours (graph is simple), so walk each cycle directly.
        for i in range(n):
            seen[i] = 0
        c = 0
        for s in range(n):
            if seen[s]:
                continue
            c += 1
            prev, cur = -1, s
            while not seen[cur]:
                seen[cur] = 1
                p = partner[cur]
                for y in adj[cur]:
                    if y != p and y != prev:
                        prev, cur = cur, y
                        break
        return c

    def rec(v0):
        # find lowest unmatched vertex
        v = v0
        while v < n and matched[v]:
            v += 1
        if v == n:
            counts[complement_cycles()] += 1
            return
        matched[v] = True
        for w in adj[v]:
            if not matched[w]:
                matched[w] = True
                partner[v], partner[w] = w, v
                rec(v + 1)
                matched[w] = False
        matched[v] = False
        partner[v] = -1

    rec(0)
    return dict(counts)



def run():
    rng = random.Random(20260806)
    out = Path("results")
    out.mkdir(exist_ok=True)
    print("Quenched exact (enumerate all perfect matchings), d=3")
    rows = {}
    for n in (16, 24, 32, 48, 64, 80):
        graph_means, npm_tot = [], 0
        reps = 40 if n <= 48 else (20 if n <= 64 else 10)
        for _ in range(reps):
            edges, adj = random_cubic(n, rng)
            counts = enumerate_pm_cycle_counts(n, edges, adj)
            npm = sum(counts.values())
            if npm == 0:
                continue
            mean = sum(c * v for c, v in counts.items()) / npm
            graph_means.append(mean)
            npm_tot += npm
        gm = sum(graph_means) / len(graph_means)
        sd = (sum((x - gm) ** 2 for x in graph_means) / len(graph_means)) ** 0.5
        rows[str(n)] = {
            "mean_of_means": gm, "sd_across_graphs": sd,
            "graphs": len(graph_means), "total_pms": npm_tot,
        }
        print(f"  n={n}: mean X = {gm:.3f} +- {sd:.3f} across {len(graph_means)} graphs"
              f" ({npm_tot} matchings), 0.5*ln n + 0.232 = {0.5*math.log(n)+0.2318:.3f}")
    (out / "quenched_d3.json").write_text(json.dumps(rows, indent=1) + "\n")
    print("wrote results/quenched_d3.json")


if __name__ == "__main__":
    run()
