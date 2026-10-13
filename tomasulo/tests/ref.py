"""In-order functional reference interpreter + comparison helper."""
import re, subprocess, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from config import parse

def run_ref(cfg, max_steps=100000):
    R = [0]*32; F = [0]*32; M = [0]*256
    for k, v in cfg['regs'].items():
        (R if k[0] == 'R' else F)[int(k[1:])] = v
    R[0] = 0
    for a, v in cfg['mem'].items():
        M[a] = v
    code = [c.split(' ') for c in cfg['code']]
    pc = steps = 0
    def reg(t): return R[int(t[1:])] if t[0] == 'R' else F[int(t[1:])]
    while 0 <= pc < len(code) and steps < max_steps:
        steps += 1
        op, a = code[pc][0], code[pc][1:]
        if op in ('Ld', 'Sd'):
            m = re.match(r'^(-?\d+)\((R\d+)\)$', a[1]); addr = int(m.group(1)) + reg(m.group(2))
            if op == 'Ld': F[int(a[0][1:])] = M[addr]
            else: M[addr] = F[int(a[0][1:])]
        elif op in ('Bne', 'Beq'):
            eq = reg(a[0]) == reg(a[1])
            if (op == 'Bne' and not eq) or (op == 'Beq' and eq):
                pc = int(pc + 1 + int(a[2]) / 4); continue
        else:
            x = reg(a[1])
            y = reg(a[2]) if a[2][0] in 'RF' else int(a[2])
            v = x - y if op in ('Sub', 'Sub.d') else (x * y if op == 'Mult.d' else x + y)
            d = int(a[0][1:])
            if a[0][0] == 'F': F[d] = v
            elif d != 0: R[d] = v
        pc += 1
    return R, F, M

def run_sim(path, width, code_dir=os.path.join(os.path.dirname(__file__), '..', 'code')):
    out = subprocess.run([sys.executable, 'main.py', os.path.abspath(path), '-w', str(width)],
                         cwd=code_dir, capture_output=True, text=True, timeout=120).stdout
    lines = out.splitlines()
    i = lines.index('REGISTER VALUES')
    nums = lambda ls: [float(x) for l in ls for x in l.split()]
    R = nums(lines[i+2:i+9:2])
    F = nums(lines[i+10:i+17:2])
    M = [0]*256
    j = lines.index('NON-ZERO MEMORY VALUES') + 2
    while lines[j].strip():
        a, v = lines[j].split(); M[int(a)] = float(v); j += 1
    cyc = int(lines[-1].split('cycles=')[1])
    return R, F, M, cyc, out

def same(a, b):
    return all(abs(x-y) <= 1e-6*max(1, abs(x), abs(y)) for x, y in zip(a, b))

def check(path, width):
    cfg = parse(path)
    r, f, m = run_ref(cfg)
    R, F, M, cyc, out = run_sim(path, width)
    ok = same(r, R) and same(f, F) and same(m, M)
    return ok, cyc, out
