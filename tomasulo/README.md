# Tomasulo simulator with multi-issue (issue width 1-4)

Python Tomasulo simulator (ROB, RAT, reservation stations, load/store queue, memory
disambiguation), extended to issue and commit up to 1-4 instructions per cycle.
Design, bug fixes, results and limitations: `Tomasulo_Report.pdf`.

## Run
    cd code
    python3 main.py <input_file> [-w WIDTH]      # default input: test_case.txt

`-w` overrides the `Issue width = N` line in the input file (1-4, default 1).
Output: instruction status table (ISSUE / EXE / MEM / WB / COMMIT cycles), register values,
non-zero memory, and a SUMMARY line.

## Test
    python3 tests/run_directed.py        # hand-written tests t1..t5 + supplied test, widths 1-4
    python3 tests/run_random.py 100      # 100 random programs x 4 widths

Both compare final registers and memory with an in-order reference interpreter (`tests/ref.py`).
Python 3 standard library only.
