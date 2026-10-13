"""Parse the simulator input file (format of the assignment handout).

    <hardware table: Integer adder / FP adder / FP multiplier / Load/store unit>
    ROB entries = 128
    Issue width = 2
    R1=10, R2=20, F2=30.1
    Mem[4]=1, Mem[8]=2, Mem[12]=3.4

    Add.d F1, F2, F3
    Ld F4, 8(R1)
    Bne R2, R3, -12

Text is case insensitive; commas are optional; '#' starts a comment line.
"""
import re

CANON = {'ld': 'Ld', 'sd': 'Sd', 'beq': 'Beq', 'bne': 'Bne', 'add': 'Add',
         'addi': 'Addi', 'sub': 'Sub', 'add.d': 'Add.d', 'sub.d': 'Sub.d',
         'mult.d': 'Mult.d'}

def _num(s):
    s = s.strip()
    try:
        return int(s)
    except ValueError:
        return float(s)

def _norm_instruction(line):
    tokens = line.replace(',', ' ').split()
    op = tokens[0].lower()
    if op not in CANON:
        raise ValueError('unknown instruction: ' + line)
    out = [CANON[op]] + [t.upper() for t in tokens[1:]]
    return ' '.join(out)

def parse(path):
    cfg = dict(rs_int=2, ex_int=1, fu_int=1, rs_fpadd=3, ex_fpadd=3, fu_fpadd=1,
               rs_fpmul=2, ex_fpmul=20, fu_fpmul=1, rs_ldst=3, ex_ldst=1,
               mem_ldst=4, fu_ldst=1, rob=128, width=1,
               regs={}, mem={}, code=[])
    for raw in open(path):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        low = line.lower()
        nums = re.findall(r'-?\d+', line)
        if low.startswith('integer adder'):
            cfg['rs_int'], cfg['ex_int'], cfg['fu_int'] = map(int, nums[:3])
        elif low.startswith('fp adder'):
            cfg['rs_fpadd'], cfg['ex_fpadd'], cfg['fu_fpadd'] = map(int, nums[:3])
        elif low.startswith('fp multiplier'):
            cfg['rs_fpmul'], cfg['ex_fpmul'], cfg['fu_fpmul'] = map(int, nums[:3])
        elif low.startswith('load/store'):
            cfg['rs_ldst'], cfg['ex_ldst'], cfg['mem_ldst'], cfg['fu_ldst'] = map(int, nums[:4])
        elif low.startswith('rob'):
            cfg['rob'] = int(nums[-1])
        elif low.startswith('issue width'):
            cfg['width'] = max(1, min(4, int(nums[-1])))
        elif re.match(r'^[rf]\d+\s*=', low):
            for name, val in re.findall(r'([rfRF]\d+)\s*=\s*(-?[\d.]+)', line):
                cfg['regs'][name.upper()] = _num(val)
        elif low.startswith('mem['):
            for addr, val in re.findall(r'[mM][eE][mM]\[(\d+)\]\s*=\s*(-?[\d.]+)', line):
                cfg['mem'][int(addr)] = _num(val)
        elif 'cycles in' in low or '# of rs' in low:
            continue                      # table header
        else:
            cfg['code'].append(_norm_instruction(line))
    return cfg
