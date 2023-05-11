
module pwm_counter
    #(parameter MFREQ=10000)
    (
        input clk,
        input SIGNAL,
        output [15:0] dty,
        output [15:0] dtyu
    );
    reg [31:0] freq_cnt = 0;

    reg[15:0] dtyr = 0;
    reg[15:0] dtyru = 0;
    assign dty = dtyr;
    assign dtyu = dtyr;


    reg[2:0] SIGr;  always @(posedge clk) SIGr <= {SIGr[1:0], SIGNAL};
    wire SIG_risingedge = (SIGr[2:1]==2'b01);
    wire SIG_fallingedge = (SIGr[2:1]==2'b10);

    always @(posedge clk)
    begin
        freq_cnt = freq_cnt + 1;
        if (SIG_fallingedge) begin
            dtyru = freq_cnt;

        end else if (SIG_risingedge) begin
            dtyr = freq_cnt;
            freq_cnt = 0;
        end
    end
endmodule
