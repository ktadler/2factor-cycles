#!/usr/bin/env python3
"""Exact quenched d=4: enumerate ALL 2-factors of simple 4-regular graphs.

2-factors are not matching complements when d>3. We backtrack on G itself
(Tutte-PM enumeration is hopeless: the gadget has 6n vertices).

Usage: enumerate_quartic.py n N
  N independent simple 4-regular graphs; graph i uses seed i+1.
  Writes results/exact_d4_n{n}.jsonl and .txt
"""
import json, math, os, sys, time
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "results")
os.makedirs(OUTDIR, exist_ok=True)
EULER = 0.5772156649015329


def girth_theory(n):
    return 0.5 * math.log(n) + EULER / 2.0 + math.log(2.0) - 0.75


def enumerate_2factor_cycle_counts(n, adj):
    """All 2-factors of a simple 4-regular graph; dict cycle_count -> multiplicity."""
    deg = [0] * n
    chosen = [[-1, -1] for _ in range(n)]
    counts = {}

    def add_edge(u, v):
        chosen[u][deg[u]] = v
        chosen[v][deg[v]] = u
        deg[u] += 1
        deg[v] += 1

    def rem_edge(u, v):
        deg[u] -= 1
        deg[v] -= 1
        chosen[u][deg[u]] = -1
        chosen[v][deg[v]] = -1

    def ncycles():
        seen = [False] * n
        c = 0
        for s in range(n):
            if seen[s]:
                continue
            c += 1
            prev, cur = -1, s
            while not seen[cur]:
                seen[cur] = True
                a, b = chosen[cur]
                nxt = b if a == prev else a
                prev, cur = cur, nxt
        return c

    def rec(v):
        while v < n and deg[v] == 2:
            v += 1
        if v == n:
            c = ncycles()
            counts[c] = counts.get(c, 0) + 1
            return
        need = 2 - deg[v]
        cands = [w for w in adj[v] if w > v and deg[w] < 2]
        if len(cands) < need:
            return
        if need == 0:
            rec(v + 1)
            return
        for combo in combinations(cands, need):
            for w in combo:
                add_edge(v, w)
            rec(v + 1)
            for w in combo:
                rem_edge(v, w)

    rec(0)
    return counts


def already(jsonl, n, N):
    xs = []
    if not os.path.isfile(jsonl):
        return xs
    for line in open(jsonl):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("n") == n and r.get("mean") is not None:
            xs.append(r)
    return xs


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: enumerate_quartic.py n N")
    n, N = int(sys.argv[1]), int(sys.argv[2])
    if n < 5 or n * 4 % 2:
        sys.exit("need n>=5, 4-regular")
    import networkx as nx

    tag = "exact_d4_n%d" % n
    jsonl = os.path.join(OUTDIR, tag + ".jsonl")
    summary = os.path.join(OUTDIR, tag + ".txt")
    done = already(jsonl, n, N)
    print("exact d=4 n=%d have %d/%d  girth=%.4f  seeds=1..%d" % (
        n, len(done), N, girth_theory(n), N), flush=True)

    for i in range(len(done), N):
        seed = 1 + i
        t0 = time.time()
        G = nx.random_regular_graph(4, n, seed=seed)
        adj = [[] for _ in range(n)]
        for u, v in G.edges():
            adj[u].append(v)
            adj[v].append(u)
        counts = enumerate_2factor_cycle_counts(n, adj)
        npm = sum(counts.values())
        mean = (sum(c * v for c, v in counts.items()) / npm) if npm else None
        rec = {"d": 4, "n": n, "i": i, "seed": seed, "mean": mean,
               "npm": npm, "counts": {str(k): v for k, v in sorted(counts.items())},
               "elapsed_s": round(time.time() - t0, 3)}
        with open(jsonl, "a") as f:
            f.write(json.dumps(rec) + "\n")
            f.flush()
            os.fsync(f.fileno())
        done.append(rec)
        print("[%d/%d] mean=%.4f  2-factors=%d  elapsed=%.2fs" % (
            len(done), N, mean, npm, rec["elapsed_s"]), flush=True)

    means = [r["mean"] for r in done if r.get("mean") is not None]
    if not means:
        return
    m = sum(means) / len(means)
    sd = (sum((x - m) ** 2 for x in means) / max(len(means) - 1, 1)) ** 0.5
    se = sd / (len(means) ** 0.5)
    npm = sum(r.get("npm") or 0 for r in done)
    line = ("exact d=4 n=%d  graphs=%d  2-factors=%d\n"
            "mean of per-graph means=%.4f  sd=%.4f  se=%.4f\n"
            "girth theory=%.4f  seeds=1..%d\n" % (
                n, len(means), npm, m, sd, se, girth_theory(n), len(means)))
    open(summary, "w").write(line)
    print(line, flush=True)


if __name__ == "__main__":
    main()
