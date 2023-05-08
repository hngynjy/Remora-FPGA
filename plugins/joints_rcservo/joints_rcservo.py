


class Plugin():

    def __init__(self, jdata):
        self.jdata = jdata

    def pinlist(self):
        pinlist_out = []
        for num, joint in enumerate(self.jdata['joints']):
            if joint['type'] == "rcservo":
                pinlist_out.append((f"RCSERVO{num}", joint['pin'], "OUTPUT"))
        return pinlist_out

    def joints(self):
        joints_out = 0
        for num, joint in enumerate(self.jdata['joints']):
            if joint['type'] == "rcservo":
                joints_out += 1
        return joints_out

    def funcs(self):
        func_out = ["    // stepgen's"]
        sysclk = int(self.jdata['clock']['speed'])
        for num, joint in enumerate(self.jdata['joints']):
            if joint['type'] == "rcservo":
                scale = joint.get('scale', 64)
                func_out.append(f"    rcservo #({sysclk // 1000 * 10}, {sysclk // 10000 * 15}, {scale}) rcservo{num} (")
                func_out.append("        .clk (sysclk),")
                func_out.append(f"        .jointFreqCmd (jointFreqCmd{num}),")
                func_out.append(f"        .jointFeedback (jointFeedback{num}),")
                func_out.append(f"        .PWM (RCSERVO{num})")
                func_out.append("    );")

        return func_out

    def ips(self):
        return """module rcservo
    #(
        parameter servo_freq = 480000, // clk / 1000 * 10
        parameter servo_center = 72000, // clk / 1000 * 1.5
        parameter servo_scale = 64
    )
    (
        input clk,
        input signed [31:0] jointFreqCmd,
        output signed [31:0] jointFeedback,
        output PWM
    );
    reg [31:0] jointCounter = 32'd0;
    reg [31:0] jointFreqCmdAbs = 32'd0;
    reg signed [31:0] jointFeedbackMem = 32'd0;
    reg step = 0;
    assign jointFeedback = jointFeedbackMem;
    always @ (posedge clk) begin
        if (jointFreqCmd > 0) begin
            jointFreqCmdAbs = jointFreqCmd / 2;
        end else begin
            jointFreqCmdAbs = -jointFreqCmd / 2;
        end
        jointCounter <= jointCounter + 1;
        if (jointFreqCmd != 0) begin
            if (jointCounter >= jointFreqCmdAbs) begin
                step <= ~step;
                jointCounter <= 32'b0;
                if (step) begin
                    if (jointFreqCmd > 0) begin
                        jointFeedbackMem = jointFeedbackMem + 1;
                    end else begin
                        jointFeedbackMem = jointFeedbackMem - 1;
                    end
                end
            end
        end
    end
    reg pulse;
    assign PWM = pulse;
    reg [31:0] counter = 0;
    always @ (posedge clk) begin
        counter = counter + 1;
        if (counter == servo_freq) begin
            pulse = 1;
            counter = 0;
        end else if (counter == servo_center + jointFeedbackMem / servo_scale) begin
            pulse = 0;
        end
    end
endmodule
"""
