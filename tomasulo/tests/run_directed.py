"""Run every directed test at issue widths 1-4, check against the reference interpreter."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(__file__))
from ref import check
here = os.path.dirname(os.path.abspath(__file__))
files = [os.path.join(here, '..', 'code', 'test_case.txt')] + sorted(glob.glob(os.path.join(here, 't*.txt')))
print('%-22s %6s %6s %6s %6s   correct' % ('test', 'w=1', 'w=2', 'w=3', 'w=4'))
for f in files:
    cyc, oks = [], []
    for w in (1, 2, 3, 4):
        ok, c, _ = check(f, w); cyc.append(c); oks.append(ok)
    print('%-22s %6d %6d %6d %6d   %s' % (os.path.basename(f), *cyc, 'PASS' if all(oks) else 'FAIL'))
