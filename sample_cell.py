#!/usr/bin/env python3
"""One KS+blossom cell: N independent simple d-regular graphs, one draw each.

The reported uncertainty is the sample standard error sd/sqrt(N).
Usage: sample_cell.py d n N [seed_lo seed_hi]
Seeds are inclusive and start at 1. A seed range writes
results/d{d}_n{n}_s{lo}-{hi}.jsonl and does not touch the shared cell file.
"""
import json, math, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "tutte_mcm_d")
OUTDIR = os.path.join(HERE, "results")
os.makedirs(OUTDIR, exist_ok=True)

EULER = 0.5772156649015329


def girth_theory(n):
    return 0.5 * math.log(n) + EULER / 2.0 + math.log(2.0) - 0.75


def pairing_theory(n):
    return 1.0 + sum(1.0 / (2 * j + 1) for j in range(1, n))


def make_graph(n, d, seed, path):
    import networkx as nx
    G = nx.random_regular_graph(d, n, seed=seed)
    with open(path, "w") as f:
        f.write("%d %d\n" % (n, d))
        for u, v in G.edges():
            f.write("%d %d\n" % (u, v))


def already(jsonl, d, n, N):
    if not os.path.isfile(jsonl):
        return []
    xs = []
    for line in open(jsonl):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("d") == d and r.get("n") == n and r.get("x") is not None:
            xs.append(r["x"])
    return xs


def done_seeds(jsonl, d, n):
    seeds = []
    if not os.path.isfile(jsonl):
        return seeds
    for line in open(jsonl):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("d") == d and r.get("n") == n and r.get("seed") is not None and r.get("x") is not None:
            seeds.append(int(r["seed"]))
    return seeds


def main():
    if len(sys.argv) not in (4, 6):
        sys.exit("usage: sample_cell.py d n N [seed_lo seed_hi]")
    d, n, N = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    seed_lo = seed_hi = None
    if len(sys.argv) == 6:
        seed_lo, seed_hi = int(sys.argv[4]), int(sys.argv[5])
        if seed_lo < 1 or seed_hi < seed_lo:
            sys.exit("seed range must satisfy 1 <= seed_lo <= seed_hi")
    if not os.path.isfile(BIN):
        sys.exit("missing %s" % BIN)
    if seed_lo is None:
        tag = "d%d_n%d" % (d, n)
    else:
        tag = "d%d_n%d_s%d-%d" % (d, n, seed_lo, seed_hi)
    jsonl = os.path.join(OUTDIR, tag + ".jsonl")
    summary = os.path.join(OUTDIR, tag + ".txt")
    tmp = os.path.join(OUTDIR, "tmp_" + tag)
    os.makedirs(tmp, exist_ok=True)

    if seed_lo is None:
        xs = already(jsonl, d, n, N)
        print("cell d=%d n=%d have %d/%d  theory_girth=%.4f  seeds=1..%d" % (
            d, n, len(xs), N, girth_theory(n), N), flush=True)
        pending = list(range(len(xs), N))
    else:
        have = set(done_seeds(jsonl, d, n))
        pending = [seed - 1 for seed in range(seed_lo, seed_hi + 1) if seed not in have]
        xs = already(jsonl, d, n, N)
        print("cell d=%d n=%d seeds=%d..%d have %d/%d  theory_girth=%.4f" % (
            d, n, seed_lo, seed_hi, len(have), seed_hi - seed_lo + 1, girth_theory(n)), flush=True)

    for i in pending:
        seed = 1 + i  # graph i uses seed i+1 for NetworkX and for Karp–Sipser
        infile = os.path.join(tmp, "g%d.txt" % i)
        outfile = os.path.join(tmp, "o%d.txt" % i)
        errfile = os.path.join(tmp, "e%d.txt" % i)
        make_graph(n, d, seed, infile)
        t0 = time.time()
        with open(infile) as inf, open(outfile, "w") as outf, open(errfile, "w") as errf:
            rc = subprocess.call([BIN, "1", str(seed)], stdin=inf,
                                 stdout=outf, stderr=errf)
        elapsed = time.time() - t0
        try:
            vals = [int(t) for t in open(outfile).read().split()]
        except Exception:
            vals = []
        x = vals[0] if vals else None
        rec = {"d": d, "n": n, "i": i, "seed": seed, "x": x,
               "rc": rc, "elapsed_s": round(elapsed, 2)}
        if x is None:
            rec["stderr"] = open(errfile).read()[-400:]
        with open(jsonl, "a") as f:
            f.write(json.dumps(rec) + "\n")
            f.flush()
            os.fsync(f.fileno())
        if x is not None:
            xs.append(x)
        m = (sum(xs) / len(xs)) if xs else float("nan")
        if seed_lo is None:
            print("[%d/%d] x=%s  mean=%.3f  elapsed=%.1fs" % (
                len(xs), N, x, m, elapsed), flush=True)
        else:
            print("[seed %d  %d/%d] x=%s  mean=%.3f  elapsed=%.1fs" % (
                seed, seed_hi - seed_lo + 1 - len(pending) + pending.index(i) + 1,
                seed_hi - seed_lo + 1, x, m, elapsed), flush=True)

    if xs:
        m = sum(xs) / len(xs)
        var = sum((v - m) ** 2 for v in xs) / max(len(xs) - 1, 1)
        sd = var ** 0.5
        se = sd / (len(xs) ** 0.5)
        seeds = sorted(done_seeds(jsonl, d, n)) if seed_lo is not None else list(range(1, len(xs) + 1))
        line = ("KS+blossom  d=%d n=%d  N=%d independent graphs, 1 draw each\n"
                "seeds=%s  (graph i uses seed=i for i=1..N)\n"
                "mean=%.4f  sd=%.4f  se=%.4f\n"
                "girth theory=%.4f  pairing theory=%.4f\n"
                "draws=%s\n" % (
                    d, n, len(xs), seeds, m, sd, se,
                    girth_theory(n), pairing_theory(n), xs))
        open(summary, "w").write(line)
        print(line, flush=True)


if __name__ == "__main__":
    main()
