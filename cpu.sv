module m_top();
    reg r_clk=0; initial #150 forever #50 r_clk = ~r_clk;
    typedef enum logic {FETCH, DECODE} stage_t;
    stage_t stage;
    initial stage = FETCH;
    always_ff @(posedge r_clk) begin
        case (stage)
            FETCH: stage <= DECODE;
            DECODE: stage <= FETCH;
        endcase
    end
    initial #99 forever begin
        #100;
        $display(stage);
    end
    initial #900 $finish;
endmodule
