import dataclasses
import os
import subprocess


def collect_status(result: list):
    all_states = []
    cur_state: dict = {}
    for line in result:
        if "$finish called" in line:
            break
        if "===" in line:
            all_states.append(cur_state)
            cur_state = {}
            continue
        if ":" in line and not "cpu.v" in line:
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
    "`MM[0]=32'b00000000000100000000000010010011;    // addi x1, x0, 1",
]

assertions0 = [
    {"stage": "FETCH"},
    {"stage": "DECODE", "inst": "0b00000000000100000000000010010011"},
    {"stage": "EX_I", "inst": "0b00000000000100000000000010010011"},
    {"stage": "ALU_WB", "inst": "0b00000000000100000000000010010011"},
    {"stage": "FETCH", "x1": 1, "inst": "0b00000000000100000000000010010011"},
]

insts1 = [
    "`MM[0]=32'b00000000000100000000000010010011;    // addi x1, x0, 1",
    "`MM[1]=32'b00000000000000001000000100110011;    // add  x2, x1, x0",
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
    "`MM[0]=32'b00000000000100000000000010010011;    // addi x1, x0, 1",
    "`MM[1]={7'd0,5'd1,5'd0,3'h2,5'd8,7'h23}; // sw x1, 8(x0)",
    "`MM[2]={12'd8,5'd0,3'b010,5'd2,7'h3};    // lw x2, 8(x0)",
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
    "`MM[0]=32'b00000000000100000000000010010011;   // addi x1, x0, 1",
    "`MM[1]=32'b00000000000100000000000100010011;   // L: addi x2, x0, 1",
    "`MM[2]={~7'd0,5'd2,5'd1,3'h0,5'h1d,7'h63};     // beq x1, x2, L", # eq. so expected to branch
    "`MM[3]=32'b00000000000000000000000000110011;   // add x0, x0, x0",
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
    "`MM[0]=32'b00000000000100000000000010010011;   // addi x1, x0, 1",
    "`MM[1]=32'b00000000001000000000000100010011;   // L: addi x2, x0, 2",
    "`MM[2]={~7'd0,5'd2,5'd1,3'h0,5'h1d,7'h63};     // beq x1, x2, L", # not eq. so expected not to branch
    "`MM[3]=32'b00000000000000000000000000110011;   // add x0, x0, x0",
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
    "`MM[0]={1'b0,10'b0000000100,1'b0,8'b00000000,5'd1,7'b1101111};     // jal 8",
    "`MM[1]={12'd7,5'd0,3'd0,5'd1,7'h13};     // addi x1,x0,7",
    "`MM[2]={12'd7,5'd0,3'd0,5'd1,7'h13};     // addi x1,x0,7",
]

assertions5 = [
    {"stage": "FETCH"},
        {"stage": "DECODE", "1st_op": 0, "imm": 8, "2nd_op": 8, "alu_out": 8},
        {"stage": "JAL", "alu_out": 4},
        {"stage": "ALU_WB"},
    {"stage": "FETCH", "pc": 8, "x1": 4},
]

insts6 = [
    "`MM[0]=32'b00000000100000000000000010010011;   // addi x1, x0, 8",
    "`MM[1]={12'd4, 5'b1, 3'b0, 5'd2, 7'b1100111};   // jalr x2, 4(x1)",
    "`MM[2]=32'b00000000000000000000000000110011;   // add x0, x0, x0", # should be skipped by jalr
    "`MM[3]=32'b00000000010100000000000010010011;   // addi x1, x0, 5",
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
    "`MM[0]=32'b00000000100000000000000010010011;   // addi x1, x0, 8",
    "`MM[1]=32'b00000000011100000000000100010011;   // addi x2, x0, 7", 
    "`MM[2]=32'b00000010000100010000000110110011;   // mul  x3, x2, x1", 
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
    "`MM[0]=32'b00000000100000000000000010010011;   // addi x1, x0, 8",
    "`MM[1]=32'b00000000011100000000000100010011;   // addi x2, x0, 7", 
    "`MM[2]=32'b01000000001000001000000110110011;   // sub  x3, x2, x1", 
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

scenarios = [(insts0, assertions0), (insts1, assertions1), (insts2, assertions2), (insts3, assertions3), (insts4, assertions4), (insts5, assertions5),
             (insts6, assertions6), (insts7, assertions7), (insts8, assertions8)]

for ith, (insts, assertions) in enumerate(scenarios, start=0):
    for j, inst in enumerate(insts):
        if not "[" + str(j) + "]" in inst:
            print("check " + str(ith) + "-th inst: " + inst)
            exit(2)
    # Prepare instructions
    with open(os.path.expanduser('asm.txt'), 'w', encoding='utf-8') as f:
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
