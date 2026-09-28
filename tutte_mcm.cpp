// Cubic-only sampler (legacy stdin: n m, then m edges).
// Karp–Sipser then blossom on G; 2-factor = complement of the perfect matching.
// No Tutte gadget.
//
// Args: nreps seed
// Output: one cycle count per line.
#include <cstdio>
#include <cstdlib>
#include <vector>

#include "ks_blossom.hpp"

int main(int argc, char** argv) {
    if (argc < 3) { fprintf(stderr, "args: nreps seed\n"); return 1; }
    int nreps = atoi(argv[1]);
    std::mt19937_64 rng(strtoull(argv[2], nullptr, 10));

    int n, m;
    if (scanf("%d %d", &n, &m) != 2 || n < 2) return 1;
    std::vector<int> eu(m), ev(m);
    std::vector<std::vector<int>> adj((size_t)n);
    for (int i = 0; i < m; i++) {
        scanf("%d %d", &eu[i], &ev[i]);
        add_undirected(adj, eu[i], ev[i]);
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
        if (!cycles_complement(n, eu, ev, mate, c)) {
            fprintf(stderr, "rep %d: complement is not a 2-factor\n", rep);
            return 2;
        }
        fprintf(stderr, "rep %d: ks_unmatched=%d cycles=%ld\n",
                rep, fin.unmatched_after_ks, c);
        printf("%ld\n", c);
        fflush(stdout);
        fflush(stderr);
    }
    return 0;
}
