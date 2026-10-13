# Qing 
# 29th may 2017
# Modified: multi-commit (up to commit_width per cycle), R0 hardwired to zero,
#           Beq support, branch commit waits for the branch to finish EX.
'''
1. commit ROB head entries in program order (up to commit_width per cycle)
2. print the instruction status row when an entry commits
'''

last_commit_cycle = 0     # cycle in which the last instruction committed

# function: print ROB entry 
def print_ROB(entry, instructions):
    global last_commit_cycle
    if entry.commit:
        last_commit_cycle = max(last_commit_cycle, entry.commit[-1])
    item = instructions[entry.PC].ljust(30)
    item += str(entry.issue).ljust(15) 
    item += str(entry.exe).ljust(15) 
    item += str(entry.mem).ljust(15)
    item += str(entry.cdb).ljust(15)
    item += str(entry.commit)
    print(item)

# function: modify architectual reg
def modify_arch_reg(entry, reg_int, reg_fp):
    if entry.dest_tag[0] == 'F':
        reg_fp[int(entry.dest_tag[1:])] = entry.value
    elif entry.dest_tag[0] == 'R' and entry.dest_tag != 'R0':   # R0 is hardwired to 0
        reg_int[int(entry.dest_tag[1:])] = entry.value
    else:
        pass

# function: commit (in order, up to commit_width instructions per cycle)
def commit(ROB, reg_int, reg_fp, cycle, instructions, commit_width=1):
    for _ in range(commit_width):
        if len(ROB) == 0:
            break
        op = instructions[ROB[0].PC].split(' ')[0]
        if op in ('Bne', 'Beq'):
            if len(ROB[0].exe) == 2:        # branch has finished EX
                ROB[0].commit.append(cycle+1)
                print_ROB(ROB.popleft(), instructions)
            else:
                break
        elif len(ROB[0].cdb) != 0:          # result has been broadcast
            ROB[0].commit.append(cycle+1)
            entry = ROB.popleft()
            modify_arch_reg(entry, reg_int, reg_fp)
            print_ROB(entry, instructions)
        elif op == 'Sd' and len(ROB[0].commit) != 0:   # store already written by mem stage
            print_ROB(ROB.popleft(), instructions)
        else:
            break
