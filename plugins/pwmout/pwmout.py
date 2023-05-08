


class Plugin():

    def __init__(self, jdata):
        self.jdata = jdata

    def pinlist(self):
        pinlist_out = []
        for num, vout in enumerate(self.jdata['vout']):
            if vout['type'] == "pwm":
                pinlist_out.append((f"PWMOUT{num}", vout['pin'], "OUTPUT"))
        return pinlist_out

    def vouts(self):
        vouts_out = 0
        for num, vout in enumerate(self.jdata['vout']):
            if vout['type'] == "pwm":
                vouts_out += 1
        return vouts_out

    def funcs(self):
        func_out = ["    // pwm's"]
        for num, vout in enumerate(self.jdata['vout']):
            if vout['type'] == "pwm":
                func_out.append(f"    pwm pwm{num} (")
                func_out.append(f"        .clk (sysclk),")
                func_out.append(f"        .dty (setPoint{num}),")
                func_out.append(f"        .pwm (PWMOUT{num})")
                func_out.append("    );")


        return func_out

    def ips(self):
        return """
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

"""
