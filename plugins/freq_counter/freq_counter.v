
module freq_counter
    #(parameter MFREQ=10000)
    (
        input clk,
        input SIGNAL,
        output [31:0] frequency
    );
    reg [31:0] freq_cnt = 0;

    reg[31:0] freq = 0;
    assign frequency = freq;

    reg[2:0] SIGr;  always @(posedge clk) SIGr <= {SIGr[1:0], SIGNAL};
    wire SIG_risingedge = (SIGr[2:1]==2'b01);

    always @(posedge clk)
    begin
        if (SIG_risingedge) begin
            //freq = MFREQ / (freq_cnt + 1) / 2;
            freq = freq_cnt + 1;
            freq_cnt = 0;
        end else begin
            freq_cnt = freq_cnt + 1;
        end
    end
endmodule
