# Branch Predictor (Pentium M hybrid: bimodal + 2-way tagged global)

Direction predictor implemented in `src/my_predictor.h` (class `pm_predictor`)
on top of the CBP2 branch-prediction simulation infrastructure
(`cbp2-infrastructure-v2`). Design, results and discussion: `Branch_Predictor_Report.pdf`.

- Bimodal table: 4096 2-bit counters indexed by low address bits.
- Global predictor: 1024 rows x 2 ways, 10-bit tag, 2-bit counter, LRU; indexed by branch address XOR a 16-bit global history.
- A global hit decides the prediction, otherwise the bimodal counter does. A global entry is allocated only when the bimodal prediction was wrong.
- Loop predictor and branch target prediction are not implemented (allowed by the assignment).
- Average over the 20 CBP2 traces: 6.725 MPKI (the provided 32K-entry gshare: 6.306).

## Build and run
The simulator files (`predict.cc`, `trace.cc`, ...) are the unmodified CBP2 ones, copied here so the code builds on its own.
The **traces are not included** (they are large); take the `traces/` folder from `cbp2-infrastructure-v2`.

    sh build.sh                                  # or: cd src && make
    ./src/predict /path/to/traces/164.gzip/gzip.trace.bz2     # prints MPKI
    sh run_all.sh /path/to/cbp2-infrastructure-v2/traces       # all traces + average

Requires g++ and bzip2. Table sizes can be changed at compile time, e.g.
`g++ -O3 -DGHR_BITS=12 -DGP_WAYS=4 -o src/predict src/predict.cc src/trace.cc`.
