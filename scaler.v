//1/50000 PreScaler
module m_prescale50000(input clk,output c_out);
	reg [15:0] cnt;
	wire wcout;
	
	assign wcout=(cnt==16'd49999) ? 1'b1 : 1'b0;
	assign c_out=wcout;
	
	always @(posedge clk) begin
		if(wcout==1'b1)
			cnt=0;
		else
			cnt=cnt+1;
	end
endmodule	
	

//1/100 PreScaler
module m_prescale1000(input clk, input c_in, output reg c_out);
    reg [10:0] cnt;
    reg prev_cin;

    always @(posedge clk) begin
        c_out <= 1'b0; // デフォルトではLOWにしておく
        prev_cin <= c_in;

        // c_in の立ち上がりを検出
        if (~prev_cin & c_in) begin
            if (cnt == 999) begin
                cnt <= 0;
                c_out <= 1'b1; // 1クロックだけHIGH
            end else begin
                cnt <= cnt + 1;
            end
        end
    end
endmodule
