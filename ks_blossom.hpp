// Karp–Sipser (linear greedy) then Edmonds/blossom to finish a maximum matching.
//
// Boost's edmonds_maximum_cardinality_matching always runs extra_greedy first
// and would throw away the KS seed. We therefore call
// edmonds_augmenting_path_finder directly on the partial matching.
#pragma once

#include <algorithm>
#include <cstdint>
#include <numeric>
#include <random>
#include <vector>

#include <boost/graph/adjacency_list.hpp>
#include <boost/graph/max_cardinality_matching.hpp>

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::undirectedS> Graph;
typedef boost::graph_traits<Graph>::vertex_descriptor Vd;

inline Graph graph_from_adj(const std::vector<std::vector<int>>& adj) {
    int n = (int)adj.size();
    Graph g(n);
    for (int u = 0; u < n; u++)
        for (int v : adj[u])
            if (u < v) boost::add_edge(u, v, g);
    return g;
}

inline void add_undirected(std::vector<std::vector<int>>& adj, int u, int v) {
    adj[u].push_back(v);
    adj[v].push_back(u);
}

// Event-driven Karp–Sipser: force degree-1 vertices, else match a random
// remaining vertex to a random living neighbour. partner[v] = -1 if unmatched.
inline void karp_sipser(const std::vector<std::vector<int>>& adj,
                        std::vector<int>& partner, std::mt19937_64& rng) {
    int n = (int)adj.size();
    partner.assign(n, -1);
    std::vector<int> deg(n);
    std::vector<uint8_t> alive(n, 1);
    for (int v = 0; v < n; v++) deg[v] = (int)adj[v].size();

    std::vector<int> forced;
    forced.reserve((size_t)n);
    for (int v = 0; v < n; v++)
        if (deg[v] == 1) forced.push_back(v);

    std::vector<int> pool(n);
    std::iota(pool.begin(), pool.end(), 0);
    std::shuffle(pool.begin(), pool.end(), rng);
    size_t pi = 0;

    auto match = [&](int u, int v) {
        partner[u] = v;
        partner[v] = u;
        alive[u] = alive[v] = 0;
        for (int x : {u, v}) {
            for (int y : adj[x]) {
                if (alive[y] && --deg[y] == 1) forced.push_back(y);
            }
        }
    };

    for (;;) {
        bool did = false;
        while (!forced.empty()) {
            int u = forced.back();
            forced.pop_back();
            if (!alive[u] || deg[u] != 1) continue;
            int w = -1;
            for (int y : adj[u])
                if (alive[y]) { w = y; break; }
            if (w >= 0) match(u, w);
            did = true;
        }
        int u = -1;
        while (pi < pool.size()) {
            int x = pool[pi++];
            if (alive[x] && deg[x] > 0) { u = x; break; }
        }
        if (u < 0) {
            if (!did) break;
            continue;
        }
        int w = -1, seen = 0;
        for (int y : adj[u]) {
            if (!alive[y]) continue;
            ++seen;
            if (std::uniform_int_distribution<int>(0, seen - 1)(rng) == 0) w = y;
        }
        if (w >= 0) match(u, w);
    }
}

struct BlossomFinish {
    int unmatched_after_ks;
    int unmatched_after_blossom;
    bool perfect;
};

// Seed Boost mate[] from KS, then blossom-augment until maximum.
inline BlossomFinish ks_then_blossom(const Graph& g,
                                     const std::vector<std::vector<int>>& adj,
                                     std::vector<Vd>& mate,
                                     std::mt19937_64& rng) {
    const int n = (int)adj.size();
    std::vector<int> partner;
    karp_sipser(adj, partner, rng);

    const Vd nil = boost::graph_traits<Graph>::null_vertex();
    mate.assign((size_t)n, nil);
    int left = 0;
    for (int v = 0; v < n; v++) {
        if (partner[v] >= 0) mate[v] = (Vd)partner[v];
        else ++left;
    }
    BlossomFinish out;
    out.unmatched_after_ks = left;

    auto vm = boost::get(boost::vertex_index, g);
    boost::edmonds_augmenting_path_finder<Graph, Vd*, decltype(vm)>
        aug(g, &mate[0], vm);
    while (aug.augment_matching()) {}
    aug.get_current_matching(&mate[0]);

    int left2 = 0;
    for (int v = 0; v < n; v++)
        if (mate[v] == nil) ++left2;
    out.unmatched_after_blossom = left2;
    out.perfect = (left2 == 0);
    return out;
}

inline long count_cycles_2regular(int n, const std::vector<int>& nbr2,
                                  const std::vector<int>& degf) {
    std::vector<uint8_t> seen((size_t)n, 0);
    long c = 0;
    for (int v0 = 0; v0 < n; v0++) {
        if (seen[v0]) continue;
        ++c;
        int prev = -1, cur = v0;
        do {
            seen[cur] = 1;
            int a = nbr2[2 * (size_t)cur], b = nbr2[2 * (size_t)cur + 1];
            int nxt = (a != prev) ? a : b;
            prev = cur;
            cur = nxt;
        } while (cur != v0);
    }
    (void)degf;
    return c;
}

// d = 3: 2-factor is the complement of a perfect matching of G.
inline bool cycles_complement(int n, const std::vector<int>& eu,
                              const std::vector<int>& ev,
                              const std::vector<Vd>& mate, long& cycles) {
    std::vector<int> nbr(2 * (size_t)n, -1), degf(n, 0);
    int m = (int)eu.size();
    for (int i = 0; i < m; i++) {
        int u = eu[i], v = ev[i];
        if ((int)mate[u] == v) continue;
        if (degf[u] >= 2 || degf[v] >= 2) return false;
        nbr[2 * (size_t)u + degf[u]++] = v;
        nbr[2 * (size_t)v + degf[v]++] = u;
    }
    for (int v = 0; v < n; v++)
        if (degf[v] != 2) return false;
    cycles = count_cycles_2regular(n, nbr, degf);
    return true;
}

// d > 3: 2-factor edges are the Tutte gadget pairs (2i — 2i+1) that are matched.
inline bool cycles_from_tutte(int n, int m, const std::vector<int>& eu,
                              const std::vector<int>& ev,
                              const std::vector<Vd>& mate, long& cycles) {
    std::vector<int> nbr(2 * (size_t)n, -1), degf(n, 0);
    for (int i = 0; i < m; i++) {
        if ((int)mate[2 * i] != 2 * i + 1) continue;
        int u = eu[i], v = ev[i];
        if (degf[u] >= 2 || degf[v] >= 2) return false;
        nbr[2 * (size_t)u + degf[u]++] = v;
        nbr[2 * (size_t)v + degf[v]++] = u;
    }
    for (int v = 0; v < n; v++)
        if (degf[v] != 2) return false;
    cycles = count_cycles_2regular(n, nbr, degf);
    return true;
}

inline void build_tutte(int n, int d, const std::vector<int>& eu,
                        const std::vector<int>& ev,
                        std::vector<std::vector<int>>& adj) {
    int m = (int)eu.size();
    int stars = d - 2;
    int NV = 2 * m + n * stars;
    adj.assign((size_t)NV, {});
    for (int i = 0; i < m; i++) {
        add_undirected(adj, 2 * i, 2 * i + 1);
        int su = 2 * m + eu[i] * stars;
        int sv = 2 * m + ev[i] * stars;
        for (int k = 0; k < stars; k++) {
            add_undirected(adj, 2 * i, su + k);
            add_undirected(adj, 2 * i + 1, sv + k);
        }
    }
}

// Tutte gadget for a (not necessarily regular) graph with min degree >= 2:
// vertex v gets deg(v)-2 star vertices. Edge i is in the 2-factor iff the
// gadget pair (2i, 2i+1) is matched. Same decode as cycles_from_tutte.
inline void build_tutte_general(int n, const std::vector<int>& eu,
                                 const std::vector<int>& ev,
                                 const std::vector<std::vector<int>>& gadj,
                                 std::vector<std::vector<int>>& adj) {
    int m = (int)eu.size();
    std::vector<int> star0(n + 1, 0);
    for (int v = 0; v < n; v++) {
        int dv = (int)gadj[v].size();
        int s = dv - 2;
        if (s < 0) s = 0;
        star0[v + 1] = star0[v] + s;
    }
    int nstars = star0[n];
    int NV = 2 * m + nstars;
    adj.assign((size_t)NV, {});
    int base = 2 * m;
    for (int i = 0; i < m; i++) {
        add_undirected(adj, 2 * i, 2 * i + 1);
        int u = eu[i], v = ev[i];
        for (int k = star0[u]; k < star0[u + 1]; k++)
            add_undirected(adj, 2 * i, base + k);
        for (int k = star0[v]; k < star0[v + 1]; k++)
            add_undirected(adj, 2 * i + 1, base + k);
    }
}
