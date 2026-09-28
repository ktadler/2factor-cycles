# Cycle counts of a random 2-factor

Companion code for Katerina Adler and Simi Haber, *The number of cycles in a random 2-factor of a random regular graph*.

The large-order counts in the paper are one 2-factor of one simple *d*-regular graph per trial. The graph comes from `networkx.random_regular_graph`. The 2-factor comes from Karp–Sipser, finished by Edmonds' blossom algorithm: on the graph itself when *d* = 3, and on Tutte's gadget when *d* > 3.

## Karp–Sipser and blossom

Karp–Sipser is the function `karp_sipser` in `ks_blossom.hpp`. It is original to this repository.

The blossom phase was not rewritten, and it was not installed as its own program. It is Boost.Graph's `edmonds_augmenting_path_finder`, declared in `boost/graph/max_cardinality_matching.hpp`. The call is in `ks_then_blossom`. The driver does not call `edmonds_maximum_cardinality_matching`: that routine begins with its own greedy pass and would discard the Karp–Sipser matching. After Karp–Sipser has written a partial matching, Boost only searches for augmenting paths, and that search makes no further random choices.

Boost was already unpacked on the machine that compiled the binary, as the header tree `boost_1_86_0`. Nothing from Boost was installed for these runs. The program uses the headers only and does not link a Boost library.

## Compiler and libraries that produced the tables

The binary `tutte_mcm_d` was compiled on `energy1.lnx.biu.ac.il` and copied to `energy2.lnx.biu.ac.il`. Both copies have BuildID `870c614600cc26c8177848d01c3ad9e11ff42054`.

```bash
g++ -std=c++17 -O3 -Isoftware/boost_1_86_0 tutte_mcm_d.cpp -o tutte_mcm_d
```

- Compiler: GCC 11.5.0 20240719 (Red Hat 11.5.0-14), the system `g++`.
- Boost: 1.86.0 (`BOOST_VERSION` 108600, `BOOST_LIB_VERSION` `"1_86"`).
- Graphs: Python 3.10.21 and NetworkX 3.4.2.

One trial at *d* = 4, *n* = 10^6 took about two hours on one core of an Intel Xeon 6767P. The runs set `OMP_NUM_THREADS=1`.

## Prerequisites

- A C++17 compiler.
- Boost 1.86.0 headers. The include path is the directory that contains the `boost/` folder, not the `boost/` folder itself.
- Python 3.10 and NetworkX 3.4.2 for the graph generator and the exact enumerations.
- Matplotlib and NumPy only if the figures are redrawn.

```bash
python3 -m pip install -r requirements.txt
```

## Build

```bash
g++ -std=c++17 -O3 -I/path/to/boost_1_86_0 tutte_mcm_d.cpp -o tutte_mcm_d
```

`tutte_mcm_d` is the sampler used for every degree in the paper. `tutte_mcm.cpp` is the same pipeline restricted to cubic graphs.

Input on stdin is `n d`, then `n*d/2` lines `u v`. Arguments are `nreps seed`. Each line of stdout is one cycle count.

## Programs

`sample_cell.py` is the driver of the simulation table. One cell is *N* independent graphs and one draw on each. Seeds start at 1, and graph *i* is generated and sampled with seed *i*.

```bash
python3 sample_cell.py 3 1000 10
```

writes `results/d3_n1000.jsonl`. A seed range is `python3 sample_cell.py d n N seed_lo seed_hi`.

Exact counts, for the range in which every 2-factor can be listed:

- `enumerate_cubic.py` — cubic graphs at *n* = 16, 24, 32, 48, 64, 80, from `random.Random(20260806)`.
- `enumerate_cubic_small.py` — cubic graphs at *n* = 8 and *n* = 12, 40 graphs, seeds 1–40.
- `enumerate_quartic.py n N` — 4-regular graphs, seeds 1 through *N*. The paper uses *N* = 40 up to *n* = 24.

`make_seeded_figs.py` redraws the simulation figures from the jsonl files in `results/`.
