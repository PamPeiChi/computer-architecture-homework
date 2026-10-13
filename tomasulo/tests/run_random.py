import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from gen_random import gen
from ref import check
N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
tmp = os.path.join(os.path.dirname(__file__), "random_tmp%s.txt" % (sys.argv[2] if len(sys.argv) > 2 else ""))
bad = 0; tot = {1: 0, 2: 0, 3: 0, 4: 0}
START = int(sys.argv[3]) if len(sys.argv) > 3 else 0
for seed in range(START, START+N):
    open(tmp, 'w').write(gen(seed))
    for w in (1, 2, 3, 4):
        ok, cyc, out = check(tmp, w)
        tot[w] += cyc
        if not ok:
            bad += 1
            print('MISMATCH seed=%d width=%d' % (seed, w))
print('programs=%d  mismatches=%d' % (N, bad))
print('total cycles by width:', tot)
