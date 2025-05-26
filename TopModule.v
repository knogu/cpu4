module TopModule(
	//////////// CLOCK //////////
	input 		          		CLK1,
	input 		          		CLK2,
	//////////// SEG7 //////////
	output		     [7:0]		HEX0,
	output		     [7:0]		HEX1,
	output		     [7:0]		HEX2,
	output		     [7:0]		HEX3,
	output		     [7:0]		HEX4,
	output		     [7:0]		HEX5,
	//////////// Push Button //////////
	input 		     [1:0]		BTN,
	//////////// LED //////////
	output		     [9:0]		LED,
	//////////// SW //////////
	input 		     [9:0]		SW

	);

wire c1,c2;
m_prescale50000 u0(CLK1, c1);
m_prescale1000 u1(CLK1, c1, c2);

wire [31:0] result;
cpu cpu(c2, result);

wire [7:0] result_dec;
m_seven_segment seg1(result[3:0], result_dec);
assign HEX0 = result_dec;

endmodule
