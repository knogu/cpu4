module m_RF(input wire clk,
    input wire[4:0] rs1,
    input wire[4:0] rs2,
    input wire write_enabled,
    input wire[4:0] write_addr,
    input wire[31:0] write_data,
    output wire[31:0] rs1_val,
    output wire[31:0] rs2_val);

  reg[31:0] mem[0:63];
  reg[31:0] r_rs1_val = 0;
  reg[31:0] r_rs2_val = 0;
  always_ff @(posedge clk) begin
    if (write_enabled) mem[write_addr] <= write_data;
    if (write_enabled & (write_addr == 30) & (write_data == 10)) $finish; // for simulation
    // r_rs1_val <= (rs1 == 5'd0) ? 32'd0 : mem[rs1];
    // r_rs2_val <= (rs2 == 5'd0) ? 32'd0 : mem[rs2];
  end
  assign rs1_val = (rs1 == 5'd0) ? 32'd0 : mem[rs1];
  assign rs2_val = (rs2 == 5'd0) ? 32'd0 : mem[rs2];
  integer i; initial for (i=0; i<32; i=i+1) mem[i]=0;
endmodule

module m_alu(input wire[31:0] rs1_val, input wire[31:0] second_operand, input wire [3:0] alu_control, output wire[31:0] alu_out);
  assign alu_out = (alu_control == 4'b1000) ? rs1_val - second_operand :
                   (alu_control == 4'b1001) ? rs1_val * second_operand :
                   (alu_control == 4'b1010) ? rs1_val / second_operand :
                   (alu_control == 4'b0111) ? rs1_val & second_operand :
                   (alu_control == 4'b0110) ? rs1_val | second_operand :
                   (alu_control == 4'b0100) ? rs1_val ^ second_operand :
                   (alu_control == 4'b1111) ? second_operand :
                   (alu_control == 4'b0010) ? ($signed(rs1_val) < $signed(second_operand)) :
                   rs1_val + second_operand;
endmodule

module m_mux(w_in1, w_in2, w_sel, w_out);
    input wire [31:0] w_in1, w_in2;
    input wire w_sel;
    output wire [31:0] w_out;
    assign w_out = (w_sel) ? w_in2 : w_in1;
endmodule

module m_mux_2bit(w_in1, w_in2, w_in3, w_in4, w_sel, w_out);
    input wire [31:0] w_in1, w_in2, w_in3, w_in4;
    input wire [1:0] w_sel;
    output wire [31:0] w_out;
    assign w_out = (w_sel == 2'b00) ? w_in1 :
                   (w_sel == 2'b01) ? w_in2 :
                   (w_sel == 2'b10) ? w_in3 :
                   w_in4;
endmodule

module main_decoder(
    input wire clk,
    input wire [6:0] opcode,
    input wire [6:0] funct7,
    input wire [2:0] funct3,
    input wire is_alu_out_zero,
    output wire is_inst_updated,
    output wire is_mem_write,
    output wire is_reg_write,
    output wire is_read_from_result,
    output wire is_result_from_mem_read,
    output wire is_result_from_older_alu_out,
    output wire is_pc_incr,
    output wire is_pc_updated,
    output wire is_1st_op_inst_pc,
    output wire is_2nd_op_imm,
    output wire is_2nd_op_4,
    output wire is_j,
    output wire is_b,
    output wire is_s,
    output wire is_r,
    output wire is_u,
    output wire is_i,
    output wire is_jalr,
    output wire [3:0] alu_control
);
    assign is_j = (opcode[6:2] == 5'b11011);
    assign is_b = (opcode[6:2] == 5'b11000);
    assign is_s = (opcode[6:2] == 5'b01000);
    assign is_r = (opcode[6:2] == 5'b01100);
    assign is_u = (opcode[6:2] == 5'b01101 | opcode[6:2] ==5'b00101);
    assign is_i = ~(is_j | is_b | is_s | is_r | is_u);
    assign is_jalr = (opcode == 7'b1100111);
    assign is_jal = (opcode == 7'b1101111);
    assign is_lui = (opcode == 7'b0110111);
    assign is_auipc = (opcode == 7'b0010111);
    wire is_load; 
    assign is_load = (opcode == 7'b0000011);
    wire is_i_calc;
    assign is_i_calc = (opcode == 7'b0010011);

    typedef enum logic[3:0] {FETCH, DECODE, MEM_ADDR, MEM_READ, MEM_WRITE, MEM_WB, EX_R, EX_I, ALU_WB, BR, JAL, JALR} stage_t;
    stage_t stage;
    initial stage = FETCH;
    always_ff @(posedge clk) begin
        case (stage)
            FETCH: stage <= DECODE;
            DECODE: stage <= (is_r) ? EX_R :
                             (is_i_calc | is_u) ? EX_I :
                             (is_load | opcode == 7'b0100011) ? MEM_ADDR :
                             (is_b) ? BR :
                             (is_jal) ? JAL : 
                             (is_jalr) ? JALR : 
                             FETCH;
            JAL: stage <= ALU_WB;
            JALR: stage <= ALU_WB;
            EX_R: stage <= ALU_WB;
            EX_I: stage <= ALU_WB;
            ALU_WB: stage <= FETCH;
            MEM_ADDR: stage <= (is_load) ? MEM_READ : MEM_WRITE;
            MEM_READ: stage <= MEM_WB;
            MEM_WRITE: stage <= FETCH;
            MEM_WB: stage <= FETCH;
            BR: stage <= FETCH;
        endcase
    end

    assign is_mem_write = (stage == MEM_WRITE);
    assign is_reg_write = (is_load & (stage == MEM_WB))
                        | (stage == ALU_WB)
                        | (stage == JAL);
    assign is_inst_updated = (stage == DECODE); // not fetch, because at fetch, the next mem_addr is decided but its inst is not loaded yet
    assign is_read_from_result = (stage == MEM_READ | stage == MEM_WRITE);
    assign is_result_from_mem_read = (stage == MEM_WB);
    assign is_result_from_older_alu_out = (stage == BR | stage == JAL | stage == ALU_WB) | (stage == JALR);
    assign is_2nd_op_imm = ((stage == DECODE & is_b)) | is_i | is_s | | is_jal | is_jalr | is_u;
    assign is_2nd_op_4 = (stage == FETCH) | (stage == JAL);
    assign is_pc_incr = (stage == FETCH);
    assign is_pc_updated = is_pc_incr | (stage == BR & is_alu_out_zero) | (stage == JAL) | (stage == JALR);
    assign is_1st_op_inst_pc = ((stage == DECODE) & (is_b | is_jal))
                             | (stage == JAL) | (stage == JALR) | (is_auipc) ;

    assign alu_control = (stage == FETCH) ? 4'b0000 :
                         (is_r & funct7 == 7'b0000001 & funct3 == 3'b000) ? 4'b1001 : // mul
                         (is_r & funct7 == 7'b0000001 & funct3 == 3'b100) ? 4'b1010 : // div
                         is_r ? {funct7[5], funct3} :
                         (is_b & (stage == BR)) ? 4'b1000 : // todo: not 4'b1000 in some B insts
                         is_lui ? 4'b1111 :
                         is_i_calc ? {1'b0, funct3} : // todo: need fix
                         4'b0000;
endmodule

module m_imm_gen(input wire w_clk,
  input wire [31:0] w_inst,
  input wire is_j,
  input wire is_b,
  input wire is_s,
  input wire is_r,
  input wire is_u,
  input wire is_i,
  output wire [31:0] w_imm
); 
  assign w_imm = (is_i) ? { {20{w_inst[31]}}, w_inst[31:20] } :
                 (is_s) ? { {20{w_inst[31]}}, w_inst[31:25], w_inst[11:7] } :
                 (is_b) ? { {20{w_inst[31]}}, w_inst[7], w_inst[30:25], w_inst[11:8], 1'b0} :
                 (is_u) ? { w_inst[31:12], 12'b0 } :
                 (is_j) ? { {12{w_inst[31]}}, w_inst[19:12], w_inst[20], w_inst[30:21], 1'b0 } :
                 0;
endmodule

module cpu(input wire clk, output wire [31:0] result); // result: for displaying result by LED in FPGA
    // fetch
    reg [31:0] r_pc = 0;
    always_ff @( posedge clk ) begin
        if (is_pc_updated) r_pc <= {result[31:1], 1'b0}; // handle &~1 for jalr. Anyway the least-significant bit is not used anywhere
    end
    wire [31:0] read_data;
    wire [31:0] mem_addr;
    wire is_read_from_result;
    m_mux m(r_pc[31:2], result, is_read_from_result, mem_addr);
    mem mem(.address(mem_addr),
        .clock(clk),
        .data(rs2_val),
        .wren(is_mem_write),
        .q(read_data)
    );

    // decode
    wire[31:0] rs1_val, rs2_val;
    m_RF rf(clk, inst[19:15], inst[24:20], is_reg_write, inst[11:7], result, rs1_val, rs2_val); // pipeline regs
    wire is_inst_updated, is_reg_write;
    reg [31:0] inst = 0;
    wire[31:0] pc_cur_inst;
    assign pc_cur_inst = is_pc_incr ? r_pc : pc_cur_inst; // at the very beginning of FETCH, r_pc is not done +4 yet
    always_comb begin
        inst = is_inst_updated ? read_data : inst;
    end

    wire is_j, is_b, is_s, is_r, is_u, is_i;
    wire is_2nd_op_imm, is_pc_incr, is_pc_updated, is_2nd_op_4;
    wire is_mem_write, is_result_from_older_alu_out;
    wire [3:0] alu_control;
    main_decoder main_decoder(
        .clk(clk),
        .opcode(inst[6:0]),
        .funct7(inst[31:25]),
        .funct3(inst[14:12]),
        .is_alu_out_zero(alu_out == 0),
        .is_inst_updated(is_inst_updated),
        .is_mem_write(is_mem_write),
        .is_reg_write(is_reg_write),
        .is_read_from_result(is_read_from_result),
        .is_result_from_mem_read(is_result_from_mem_read),
        .is_result_from_older_alu_out(is_result_from_older_alu_out),
        .is_2nd_op_imm(is_2nd_op_imm),
        .is_2nd_op_4(is_2nd_op_4),
        .is_1st_op_inst_pc(is_1st_op_inst_pc),
        .is_pc_incr(is_pc_incr),
        .is_pc_updated(is_pc_updated),
        .is_j(is_j),
        .is_b(is_b),
        .is_s(is_s),
        .is_r(is_r),
        .is_u(is_u),
        .is_i(is_i),
        .alu_control(alu_control)
    );
    wire [31:0] imm;
    m_imm_gen imm_gen(clk, inst, is_j, is_b, is_s, is_r, is_u, is_i, imm);

    // execute
    wire[31:0] alu_out;
    wire[31:0] first_operand, second_operand;
    assign first_operand = is_1st_op_inst_pc ? pc_cur_inst :
                           is_pc_incr ? r_pc :
                           rs1_val;
    assign second_operand = is_2nd_op_4 ? 4 :
                            is_2nd_op_imm ? imm :
                            rs2_val;
    m_alu alu(first_operand, second_operand, alu_control, alu_out);
    reg[31:0] r_alu_res;
    always_ff @( posedge clk ) begin
        r_alu_res <= alu_out;
    end

    // memory access
    assign result = is_result_from_mem_read ? read_data :
                    is_result_from_older_alu_out ? r_alu_res :
                    alu_out;
    // pipeline reg: imem

    // write back
endmodule

module m_top();
    reg r_clk=0; initial #150 forever #50 r_clk = ~r_clk;
    wire [31:0] result;
    cpu c(r_clk, result);
    initial #99 forever begin
        #100;
        $display("stage: %0s", c.main_decoder.stage.name());
        $display("inst:  0b%32b", c.inst);
        $display("pc_cur_inst:         %d", c.pc_cur_inst);
        $display("pc_cur_inst_hex:         %h", c.pc_cur_inst);
        $display("tmp_next_pc:         %d", c.r_pc);
        $display("tmp_next_pc_hex:         %h", c.r_pc);
        $display("is_pc_incr:          %d", c.is_pc_incr);
        $display("rs1:                %d", c.inst[19:15]);
        $display("rs1_val:    %d", c.rs1_val);
        $display("rs2:                %d", c.inst[24:20]);
        $display("rs2_val:    %d", c.rs2_val);
        $display("imm:        %d", c.imm);
        $display("1st_op:     %d", c.first_operand);
        $display("1st_op:     %d", c.first_operand);
        $display("2nd_op:     %d", $signed(c.second_operand));
        $display("2nd_op_u:     %d", c.second_operand);
        $display("alu_control:    0b%4b", c.alu_control);
        $display("alu_out:     %d", c.alu_out);
        $display("alu_out_h:     %h", c.alu_out);
        $display("result:     %d", c.result);
        $display("is_jal:     %b", c.main_decoder.is_jal);
        $display("is_reg_write:     %b", c.is_reg_write);
        $display("rd:         %d", c.inst[11:7]);
        $display("mem_addr: %d", c.mem_addr);
        $display("rf.reg_to_write: %d", c.rf.write_addr);
        $display("rf.write_enabled: %d", c.rf.write_enabled);
        $display("rf.write_data: %d", c.rf.write_data);
        $display("x1:          %d", $signed(c.rf.mem[1]));
        $display("x2:          %d", $signed(c.rf.mem[2]));
        $display("x3:          %d", $signed(c.rf.mem[3]));
        $display("x4:          %d", $signed(c.rf.mem[4]));
        $display("x5:          %d", $signed(c.rf.mem[5]));
        $display("x6:          %d", $signed(c.rf.mem[6]));
        $display("x7:          %d", $signed(c.rf.mem[7]));
        $display("x8:          %d", $signed(c.rf.mem[8]));
        $display("x9:          %d", $signed(c.rf.mem[9]));
        $display("x10:         %d", $signed(c.rf.mem[10]));

        $display("x1_u:          %d", c.rf.mem[1]);
        $display("x2_u:          %d", c.rf.mem[2]);
        $display("x3_u:          %d", c.rf.mem[3]);
        $display("x4_u:          %d", c.rf.mem[4]);
        $display("x5_u:          %d", c.rf.mem[5]);
        $display("x6_u:          %d", c.rf.mem[6]);
        $display("x7_u:          %d", c.rf.mem[7]);
        $display("x8_u:          %d", c.rf.mem[8]);
        $display("x9_u:          %d", c.rf.mem[9]);
        $display("x10_u:         %d", c.rf.mem[10]);

        $display("x1_h:          %h", c.rf.mem[1]);
        $display("x2_h:          %h", c.rf.mem[2]);
        $display("x3_h:          %h", c.rf.mem[3]);
        $display("x4_h:          %h", c.rf.mem[4]);
        $display("x5_h:          %h", c.rf.mem[5]);
        $display("x6_h:          %h", c.rf.mem[6]);
        $display("x7_h:          %h", c.rf.mem[7]);
        $display("x8_h:          %h", c.rf.mem[8]);
        $display("x9_h:          %h", c.rf.mem[9]);
        $display("x10_h:         %h", c.rf.mem[10]);

        $display("is_mem_write:          %h", c.mem.wren);

        $display("sp:          %d", $signed(c.rf.mem[2]));
        $display("fp:          %d", $signed(c.rf.mem[8]));

        $display("\n");

        $display("m[996]:          %h", c.mem.mem[996]);
        $display("m[1000]:          %h", c.mem.mem[1000]);
        $display("m[1004]:          %h", c.mem.mem[1004]);
        $display("m[1008]:          %h", c.mem.mem[1008]);
        $display("m[1012]:          %h", c.mem.mem[1012]);
        $display("m[1016]:          %h", c.mem.mem[1016]);
        $display("m[1020]:          %h", c.mem.mem[1020]);
        $display("m[1024]:          %h", c.mem.mem[1024]);

        $display("\n");

        $display("m[996]:           %d", c.mem.mem[996]);
        $display("m[1000]:          %d", c.mem.mem[1000]);
        $display("m[1004]:          %d", c.mem.mem[1004]);
        $display("m[1008]:          %d", c.mem.mem[1008]);
        $display("m[1012]:          %d", c.mem.mem[1012]);
        $display("m[1016]:          %d", c.mem.mem[1016]);
        $display("m[1020]:          %d", c.mem.mem[1020]);
        $display("m[1024]:          %d", c.mem.mem[1024]);

        $display("===================");

    end
    // initial #1900 $finish;
    initial begin
      $readmemb("asm.bin", c.mem.mem);
    end
endmodule
