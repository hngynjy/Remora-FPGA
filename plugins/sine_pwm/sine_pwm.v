module sine_pwm
    #(parameter START = 0)
    (
        input clk,
        input [31:0] freq,
        output pwm_out
    );

    reg [31:0] clk_cnt = 0;
    reg [7:0] cnt = START;

    always@ (posedge(clk))
    begin
        clk_cnt = clk_cnt + 1;
        if (clk_cnt >= freq) begin
            clk_cnt = 0;
            cnt = cnt + 1;
            if (cnt == 29)
                cnt = 0;
        end
    end

    reg [7:0] sine_tbl [0:29];
    initial begin
        sine_tbl[0] = 128;
        sine_tbl[1] = 153;
        sine_tbl[2] = 177;
        sine_tbl[3] = 199;
        sine_tbl[4] = 217;
        sine_tbl[5] = 232;
        sine_tbl[6] = 242;
        sine_tbl[7] = 247;
        sine_tbl[8] = 247;
        sine_tbl[9] = 242;
        sine_tbl[10] = 232;
        sine_tbl[11] = 217;
        sine_tbl[12] = 199;
        sine_tbl[13] = 177;
        sine_tbl[14] = 153;
        sine_tbl[15] = 128;
        sine_tbl[16] = 103;
        sine_tbl[17] = 79;
        sine_tbl[18] = 57;
        sine_tbl[19] = 39;
        sine_tbl[20] = 24;
        sine_tbl[21] = 14;
        sine_tbl[22] = 9;
        sine_tbl[23] = 9;
        sine_tbl[24] = 14;
        sine_tbl[25] = 24;
        sine_tbl[26] = 39;
        sine_tbl[27] = 57;
        sine_tbl[28] = 79;
        sine_tbl[29] = 103;
    end

    wire [7:0] dty = sine_tbl[cnt];
    pwm #(8) pwm (
        .clk (clk),
        .dty (dty),
        .pwm (pwm_out)
    );

endmodule

