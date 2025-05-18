import dataclasses
import os
import subprocess


def collect_status(result: list):
    all_states = []
    cur_state: dict = {}
    for line in result:
        if "$finish called" in line or "warning" in line:
            break
        if "===" in line:
            all_states.append(cur_state)
            cur_state = {}
            continue
        if ":" in line and not "cpu.sv" in line:
            split = line.split(":")
            if 2 < len(split):
                print(split)
                exit(5)
            label, val = line.split(":")
            try:
                cur_state[label] = int(val)
            except:
                cur_state[label] = val.strip() # maybe better to warn
    return all_states


insts0 = [
    "00000000100000000000010010011", # addi x1, x0, 1
    "0000101000000000111100010011", # addi x30, x0, 10
]

assertions0 = [
    {"stage": "FETCH"},
    {"stage": "DECODE", "inst": "0b00000000000100000000000010010011"},
    {"stage": "EX_I", "inst": "0b00000000000100000000000010010011"},
    {"stage": "ALU_WB", "inst": "0b00000000000100000000000010010011"},
    {"stage": "FETCH", "x1": 1, "inst": "0b00000000000100000000000010010011"},
]

insts1 = [
    "0000000100000000000010010011", # addi x1, x0, 1
    "0000000000001000000100110011", # add  x2, x1, x0
]

assertions1 = [
    {"stage": "FETCH"},
        {"stage": "DECODE", "inst": "0b00000000000100000000000010010011"},
        {"stage": "EX_I", "inst": "0b00000000000100000000000010010011"},
        {"stage": "ALU_WB", "inst": "0b00000000000100000000000010010011"},
    {"stage": "FETCH", "x1": 1, "inst": "0b00000000000100000000000010010011"},
        {"stage": "DECODE", "inst": "0b00000000000000001000000100110011", "x1": 1},
        {"stage": "EX_R", "inst": "0b00000000000000001000000100110011", "1st_op": 1, "2nd_op": 0},
        {"stage": "ALU_WB", "inst": "0b00000000000000001000000100110011"},
    {"stage": "FETCH", "inst": "0b00000000000000001000000100110011", "x2": 1},
]

insts2 = [
    "0000100000000000010010011", # addi x1, x0, 1
    "0000100000010010000100011", # sw x1, 8(x0)
    "0000100000000010000100000011", # lw x2, 8(x0)
]

assertions2 = [
    {"stage": "FETCH"},
        {"stage": "DECODE", "inst": "0b00000000000100000000000010010011"},
        {"stage": "EX_I", "inst": "0b00000000000100000000000010010011"},
        {"stage": "ALU_WB", "inst": "0b00000000000100000000000010010011"},
    {"stage": "FETCH", "inst": "0b00000000000100000000000010010011", "x1": 1},
        {"stage": "DECODE", "inst": "0b00000000000100000010010000100011"},
        {"stage": "MEM_ADDR"},
        {"stage": "MEM_WRITE", "rs2_val": 1},
    {"stage": "FETCH"},
        {"stage": "DECODE"},
        {"stage": "MEM_ADDR"},
        {"stage": "MEM_READ"},
        {"stage": "MEM_WB"},
    {"stage": "FETCH", "x2": 1},
]

insts3 = [
    "00000000000100000000000010010011",#   // addi x1, x0, 1",
    "00000000000100000000000100010011", # L: addi x2, x0, 1",
    "11111110001000001000111011100011", # beq x1, x2, L", # eq. so expected to branch # 11111110001000001000111011100011
    "110011", # add x0, x0, x0",
]

assertions3 = [
    {"stage": "FETCH"},
        {"stage": "DECODE", "inst": "0b00000000000100000000000010010011"},
        {"stage": "EX_I", "inst": "0b00000000000100000000000010010011"},
        {"stage": "ALU_WB", "inst": "0b00000000000100000000000010010011"},
    {"stage": "FETCH", "inst": "0b00000000000100000000000010010011", "x1": 1},
        {"stage": "DECODE"},
        {"stage": "EX_I"},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "x2": 1},
        {"stage": "DECODE", "pc_cur_inst": 8, "1st_op": 8, "2nd_op": -4, "alu_control": "0b0000", "alu_out": 4},
        {"stage": "BR", "1st_op": 1, "2nd_op": 1, "alu_control": "0b1000", "alu_out": 0, "result": 4},
    {"stage": "FETCH", "pc": 4},
]

insts4 = [
    "00000000000100000000000010010011", # addi x1, x0, 1",
    "00000000001000000000000100010011", # L: addi x2, x0, 2",
    "11111110001000001000111011100011", # beq x1, x2, L", # not eq. so expected not to branch
    "110011", # add x0, x0, x0",
]

assertions4 = [
    {"stage": "FETCH"},
        {"stage": "DECODE"},
        {"stage": "EX_I"},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "x1": 1},
        {"stage": "DECODE"},
        {"stage": "EX_I"},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "x2": 2},
        {"stage": "DECODE"},
        {"stage": "BR"},
    {"stage": "FETCH", "pc": 12},
]

insts5 = [
    "00000000100000000000000011101111", # jal 8", 00000000100000000000000011101111
    "110011"#     // addi x1,x0,7",
    "110011", # addi x1,x0,7",
]

assertions5 = [
    {"stage": "FETCH"},
        {"stage": "DECODE", "1st_op": 0, "imm": 8, "2nd_op": 8, "alu_out": 8},
        {"stage": "JAL", "alu_out": 4},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "pc": 8, "x1": 4},
]

insts6 = [
    "00000000100000000000000010010011", # addi x1, x0, 8",
    "00000000010000001000000101100111", # jalr x2, 4(x1)"
    "110011", # add x0, x0, x0", # should be skipped by jalr
    "10100000000000010010011", # addi x1, x0, 5",
]

assertions6 = [
    {"stage": "FETCH"},
        {"stage": "DECODE"},
        {"stage": "EX_I"},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "x1": 8},
        {"stage": "DECODE", "rs1_val": 8, "1st_op": 8, "2nd_op": 4, "alu_out": 12},
        {"stage": "JALR", "1st_op": 4, "2nd_op": 4, "alu_out": 8, "result": 12},
        {"stage": "ALU_WB", "rd": 2, "result": 8},
    {"stage": "FETCH", "x2": 8}
]

insts7 = [
    "0000100000000000000010010011", # addi x1, x0, 8",
    "0000011100000000000100010011", # addi x2, x0, 7", 
    "0010000100010000000110110011", # mul  x3, x2, x1", 
]

assertions7 = [
    {"stage": "FETCH"},
        {"stage": "DECODE"},
        {"stage": "EX_I"},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "x1": 8},
        {"stage": "DECODE"},
        {"stage": "EX_I"},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "x2": 7},
        {"stage": "DECODE"},
        {"stage": "EX_R"},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "x3": 56},
]

insts8 = [
    "0000000100000000000000010010011", # addi x1, x0, 8",
    "0000000011100000000000100010011", # addi x2, x0, 7", 
    "1000000001000001000000110110011", # sub  x3, x2, x1", 
]

assertions8 = [
    {"stage": "FETCH"},
        {"stage": "DECODE"},
        {"stage": "EX_I"},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "x1": 8},
        {"stage": "DECODE"},
        {"stage": "EX_I"},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "x2": 7},
        {"stage": "DECODE"},
        {"stage": "EX_R"},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "x3": 1},
]

insts9 = [
    "11111111111111111111000010110111", # lui x1, 1048575"
]

assertions9 = [
    {"stage": "FETCH"},
        {"stage": "DECODE"},
        {"stage": "EX_I"},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "x1": 4294963200}
]

insts10 = [
    "11111111111111111111000010010111", # auipc x1, 1048575", # 
    "11111111111111111111000010010111", # auipc x1, 1048575",
]

assertions10 = [
    {"stage": "FETCH"},
        {"stage": "DECODE"},
        {"stage": "EX_I"},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "x1": 4294963200},
        {"stage": "DECODE"},
        {"stage": "EX_I"},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "x1": 4294963204},
]


scenarios = [(insts0, assertions0), (insts1, assertions1), (insts2, assertions2), (insts3, assertions3), (insts4, assertions4), (insts5, assertions5),
             (insts6, assertions6), (insts7, assertions7), (insts8, assertions8), (insts9, assertions9), (insts10, assertions10)
             ]

for ith, (insts, assertions) in enumerate(scenarios, start=0):
    # Prepare instructions
    with open(os.path.expanduser('asm.bin'), 'w', encoding='utf-8') as f:
        for inst in insts:
            f.write(inst + '\n')
    # Execute simulation
    result = subprocess.run(['./br.sh'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Check result
    status = collect_status(result.stdout.splitlines())

    for i, assertion in enumerate(assertions):
        for label, val in assertion.items():
            if (len(status) <= i):
                print("index " + str(i) + " is too big.")
                print(status)
                exit(3)
            if status[i][label] != val:
                print("Assertion failed in " + str(ith) + "-th scenario")
                # print("actual PC: " + str(status[i]["pc"]))
                print("assertion index: " + str(i))
                print(label)
                print("expected: ", val)
                print("actual: ", status[i][label])
                exit(1)

    print(str(ith) + "-th scenario succeeded")
