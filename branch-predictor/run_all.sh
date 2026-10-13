#!/bin/sh
# Run the predictor on every trace in a directory and print MPKI + average.
# usage: ./run_all.sh /path/to/cbp2-infrastructure-v2/traces
[ -z "$1" ] && { echo "usage: $0 <trace-directory>"; exit 1; }
BIN="$(dirname "$0")/src/predict"
[ -x "$BIN" ] || { echo "run: sh build.sh first"; exit 1; }
find "$1" -name '*.trace.*' | sort | while read -r t; do
  printf "%-45s %s\n" "$(basename "$t")" "$("$BIN" "$t" | tail -1)"
done | tee /tmp/bp_run_all.$$ 
awk '{s+=$2; n++} END {printf "average MPKI: %.3f over %d traces\n", s/n, n}' /tmp/bp_run_all.$$; rm -f /tmp/bp_run_all.$$
