module mem(input wire [31:0] addr,
  input wire clk,
  input wire is_write_enabled,
  input wire [31:0] write_data,
  output wire [31:0] out
);
    reg [31:0] r_out;
    reg[31:0] mem[0:65536];
    always_ff @(posedge clk) begin
      r_out <= mem[addr[5:0]];
      if (is_write_enabled) mem[addr[5:0]] <= write_data;
    end
    assign out = r_out;
endmodule
