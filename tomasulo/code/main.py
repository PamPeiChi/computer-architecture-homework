# Qing 
# 21st May 2017 
# Modified: input-file driven configuration, issue width 1-4 (multi-issue and
#           multi-commit), final register / memory dump.
#
# usage: python main.py [input_file] [-w ISSUE_WIDTH]

import sys
import argparse
from copy import deepcopy
from collections import deque
from init import build_rs, ld_sd_exe, ld_sd_mem, cdb, PC
from issue import issue
from exe import exe 
from mem import mem
from wb import wb 
import commit as commit_mod
from commit import commit
from config import parse

ap = argparse.ArgumentParser()
ap.add_argument('infile', nargs='?', default='test_case.txt')
ap.add_argument('-w', '--width', type=int, default=None,
                help='issue width 1-4 (overrides "Issue width" in the input file)')
args = ap.parse_args()

cfg = parse(args.infile)
issue_width = cfg['width'] if args.width is None else max(1, min(4, args.width))
commit_width = issue_width            # commit as wide as issue so ROB can drain

instructions = cfg['code']

'''initialize regs, RAT, memory''' 
reg_int = [0]*32
reg_fp = [0]*32
for name, val in cfg['regs'].items():
    if name[0] == 'R' and name != 'R0':
        reg_int[int(name[1:])] = val
    elif name[0] == 'F':
        reg_fp[int(name[1:])] = val
rat_int = deepcopy(reg_int)
rat_fp = deepcopy(reg_fp)
memory = [0]*256
for addr, val in cfg['mem'].items():
    memory[addr] = val

'''intialize reservation stations'''
rs_int_adder = build_rs(cfg['rs_int'])
rs_fp_adder = build_rs(cfg['rs_fpadd'])
rs_fp_multi = build_rs(cfg['rs_fpmul'])

'''initilize function unit'''
fu_int_adder = deque(); time_fu_int_adder = cfg['ex_int']
fu_fp_adder = deque();  time_fu_fp_adder = cfg['ex_fpadd']
fu_fp_multi = deque();  time_fu_fp_multi = cfg['ex_fpmul']

'''initialize load/store queue'''
ld_sd_queue = deque()
size_ld_sd_queue = cfg['rs_ldst']
ld_sd_exe = ld_sd_exe()
ld_sd_exe.busy = 0
time_ld_sd_exe = cfg['ex_ldst']
ld_sd_mem = ld_sd_mem()
ld_sd_mem.busy = 0
time_ld_sd_mem = cfg['mem_ldst']

'''initialize ROB'''
ROB = deque()
size_ROB = cfg['rob']

'''initialize CDB'''
results_buffer = deque()
cdb = cdb()
cdb.valid = 0

"""instruction pointer"""
PC = PC()
PC.PC = 0
PC.valid = 1 
cycle = 1

# print title 
item = ''.ljust(30)
for h in ('ISSUE', 'EXE', 'MEM', 'WB', 'COMMIT'):
    item += h.ljust(15)
print(item)

# main loop (cap on cycles protects against a non-terminating test program)
MAX_CYCLES = 100000
# (also wait for the memory unit: a committed store finishes its write after leaving the ROB)
while (len(ROB) > 0) or (0 <= PC.PC < len(instructions)) or (ld_sd_mem.busy == 1):
    if cycle > MAX_CYCLES:
        print('ERROR: exceeded %d cycles (infinite loop in program?)' % MAX_CYCLES)
        break

    '''ISSUE stage (up to issue_width instructions, in order)'''
    issue(cycle, PC, instructions, ROB, size_ROB, 
          rs_int_adder, rs_fp_adder, rs_fp_multi, 
          ld_sd_queue, size_ld_sd_queue, 
          rat_int, rat_fp, issue_width)

    '''EXE stage'''
    exe(fu_int_adder, time_fu_int_adder, 
        fu_fp_adder, time_fu_fp_adder, 
        fu_fp_multi, time_fu_fp_multi, results_buffer,  
        rs_int_adder, rs_fp_adder, rs_fp_multi, 
        ld_sd_exe, time_ld_sd_exe, ld_sd_queue,
        cycle, ROB, PC)

    '''MEM stage'''
    mem(ld_sd_queue, ld_sd_mem, time_ld_sd_mem, results_buffer,
        memory, ROB, cycle)

    '''CDB stage (one CDB: one broadcast per cycle)'''
    wb(cdb, rat_int, rat_fp, 
       rs_int_adder, rs_fp_adder, rs_fp_multi,
       ld_sd_queue, ROB, cycle,
       results_buffer) 
    
    '''COMMIT stage (up to commit_width instructions, in order)'''
    commit(ROB, reg_int, reg_fp, cycle, instructions, commit_width)
    
    cycle += 1

total_cycles = commit_mod.last_commit_cycle     # cycle in which the last instruction committed

# ---- final report ----
print()
print('REGISTER VALUES')
def fmt(v):
    return ('%.10g' % v) if isinstance(v, float) else str(v)
def dump(prefix, vals):
    for s in range(0, 32, 8):
        print(''.join(('%s%d' % (prefix, i)).ljust(18) for i in range(s, s+8)))
        print(''.join(fmt(vals[i]).ljust(18) for i in range(s, s+8)))
dump('R', reg_int)
dump('F', reg_fp)
print()
print('NON-ZERO MEMORY VALUES')
print('Addresses'.ljust(12) + 'Values')
for a, v in enumerate(memory):
    if v != 0:
        print(str(a).ljust(12) + fmt(v))
print()
print('SUMMARY issue_width=%d cycles=%d' % (issue_width, total_cycles))
