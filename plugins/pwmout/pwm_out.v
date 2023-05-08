module pwm
    #(parameter BITS = 16)
    (
        input clk,
        input [BITS - 1 : 0] dty,
        output pwm
    );
    reg rPwm;
    reg [BITS - 1 : 0] rDuty;
    wire pwmNext;
    wire [BITS - 1 : 0] dutyNext;
    always @(posedge clk)
    begin
        rPwm <= pwmNext;
        rDuty <= dutyNext;
    end
    assign dutyNext = rDuty + 1;
    assign pwmNext = rDuty < dty;
    assign pwm = rPwm;
endmodule
