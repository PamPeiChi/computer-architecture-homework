#!/bin/sh
# Build the predictor simulator (same as `make` in src/).
cd "$(dirname "$0")/src" && g++ -O3 -Wall -o predict predict.cc trace.cc && echo "built src/predict"
