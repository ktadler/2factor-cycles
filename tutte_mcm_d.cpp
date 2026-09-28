// Sample 2-factor cycle counts of a fixed simple d-regular graph.
//
//   d = 3: Karp–Sipser then blossom on G itself; 2-factor = complement of PM.
//   d > 3: same matching pipeline on the Tutte gadget of G.
//
// Input (stdin): n d   then m = n*d/2 lines "u v"
// Args: nreps seed
// Output: one cycle count per line (flushed after each draw).
// Stderr: one-line KS leftover / blossom leftover per draw.
#include <cstdio>
#include <cstdlib>
#include <vector>

#include "ks_blossom.hpp"

int main(int argc, char** argv) {
    if (argc < 3) { fprintf(stderr, "args: nreps seed\n"); return 1; }
    int nreps = atoi(argv[1]);
    std::mt19937_64 rng(strtoull(argv[2], nullptr, 10));

    int n, d;
    if (scanf("%d %d", &n, &d) != 2 || d < 3) return 1;
    int m = n * d / 2;
    std::vector<int> eu(m), ev(m);
    for (int i = 0; i < m; i++) scanf("%d %d", &eu[i], &ev[i]);

    std::vector<std::vector<int>> adj;
    if (d == 3) {
        adj.assign((size_t)n, {});
        for (int i = 0; i < m; i++) add_undirected(adj, eu[i], ev[i]);
    } else {
        build_tutte(n, d, eu, ev, adj);
    }
    Graph g = graph_from_adj(adj);
    std::vector<Vd> mate;

    for (int rep = 0; rep < nreps; rep++) {
        BlossomFinish fin = ks_then_blossom(g, adj, mate, rng);
        if (!fin.perfect) {
            fprintf(stderr, "rep %d: matching not perfect (ks_left=%d blossom_left=%d)\n",
                    rep, fin.unmatched_after_ks, fin.unmatched_after_blossom);
            continue;
        }
        long c = 0;
        bool ok = (d == 3)
            ? cycles_complement(n, eu, ev, mate, c)
            : cycles_from_tutte(n, m, eu, ev, mate, c);
        if (!ok) {
            fprintf(stderr, "rep %d: decoded matching is not a 2-factor\n", rep);
            return 2;
        }
        fprintf(stderr, "rep %d: ks_unmatched=%d blossom_unmatched=0 cycles=%ld\n",
                rep, fin.unmatched_after_ks, c);
        printf("%ld\n", c);
        fflush(stdout);
        fflush(stderr);
    }
    return 0;
}
