"""Generate random but well-formed test programs (word-aligned, in-range memory,
bounded loops) for differential testing against ref.py."""
import random

HW = """               # of rs         Cycles in EX    Cycles in Mem   # of FUs
Integer adder   {ri}               {ei}                               1
FP adder        {rf}               {ef}                               1
FP multiplier   {rm}               {em}                               1
Load/store unit {rl}               {el}                {ml}               1

ROB entries = {rob}
Issue width = 1
R1={b1}, R2={b2}, R3={b3}, F2=1.5, F3=2.0, F4=0.5
{mem}
"""

def gen(seed):
    rnd = random.Random(seed)
    hw = dict(ri=rnd.choice([1, 2, 4]), ei=rnd.choice([1, 2]),
              rf=rnd.choice([1, 2, 3]), ef=rnd.choice([2, 3, 4]),
              rm=rnd.choice([1, 2]), em=rnd.choice([5, 10, 15]),
              rl=rnd.choice([2, 3, 5]), el=1, ml=rnd.choice([2, 4, 5]),
              rob=rnd.choice([8, 16, 64]),
              b1=rnd.choice([64, 96]), b2=rnd.choice([100, 128]), b3=rnd.choice([160, 192]))
    hw['mem'] = ', '.join('Mem[%d]=%s' % (a, rnd.choice([1.0, 2.5, 3.0, 0.5, 4.0]))
                          for a in range(32, 256, 12)) if False else ', '.join(
                          'Mem[%d]=%s' % (a, rnd.choice([1.0, 2.5, 3.0, 0.5, 4.0])) for a in range(32, 224, 8))
    iregs = ['R4', 'R5', 'R6', 'R7', 'R8']
    fregs = ['F%d' % i for i in range(2, 9)]
    base = ['R1', 'R2', 'R3']
    def off(): return rnd.choice(range(-24, 28, 4))
    def one():
        k = rnd.random()
        if k < 0.20: return 'Ld %s, %d(%s)' % (rnd.choice(fregs), off(), rnd.choice(base))
        if k < 0.35: return 'Sd %s, %d(%s)' % (rnd.choice(fregs), off(), rnd.choice(base))
        if k < 0.55: return '%s %s, %s, %s' % (rnd.choice(['Add.d', 'Sub.d']), rnd.choice(fregs), rnd.choice(fregs), rnd.choice(fregs))
        if k < 0.65: return 'Mult.d %s, %s, F4' % (rnd.choice(fregs), rnd.choice(['F2', 'F3', 'F4']))
        if k < 0.80: return 'Addi %s, %s, %d' % (rnd.choice(iregs), rnd.choice(iregs + ['R0']), rnd.randint(-5, 9))
        return '%s %s, %s, %s' % (rnd.choice(['Add', 'Sub']), rnd.choice(iregs), rnd.choice(iregs), rnd.choice(iregs))
    code = []
    for _ in range(rnd.randint(1, 3)):
        code += [one() for _ in range(rnd.randint(2, 6))]
        if rnd.random() < 0.6:          # bounded loop with counter R9
            body = [one() for _ in range(rnd.randint(2, 6))]
            code.append('Addi R9, R0, %d' % rnd.randint(2, 4))
            start = len(code)
            code += body
            code.append('Addi R9, R9, -1')
            k = len(code)
            code.append('Bne R9, R0, %d' % ((start - k - 1) * 4))
        if rnd.random() < 0.3:          # forward branch (skip a few instructions)
            skip = rnd.randint(1, 3)
            code.append('%s R%d, R%d, %d' % (rnd.choice(['Beq', 'Bne']), rnd.randint(4, 8), rnd.randint(4, 8), skip * 4))
            code += [one() for _ in range(skip)]
    return HW.format(**hw) + '\n' + '\n'.join(code) + '\n'
