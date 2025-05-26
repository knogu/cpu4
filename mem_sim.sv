/*
mem	mem_inst (
	.address ( address_sig ),
	.clock ( clock_sig ),
	.data ( data_sig ),
	.wren ( wren_sig ),
	.q ( q_sig )
	);
*/
module mem(
  input	[15:0]  address,
	input	  clock,
	input	[31:0]  data,
	input	  wren,
	output	[31:0]  q
);
    reg [31:0] r_out;
    reg[31:0] mem[0:65536];
    always_ff @(posedge clock) begin
      r_out <= mem[address];
      if (wren) mem[address] <= data;
    end
    assign q = r_out;
endmodule
