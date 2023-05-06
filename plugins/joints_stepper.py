


class Plugin():

    def __init__(self, jdata):
        self.jdata = jdata

    def pinlist(self):
        pinlist_out = []
        for num, joint in enumerate(self.jdata['joints']):
            if joint['type'] == "stepper":
                pinlist_out.append((f"STP{num}", joint['pins']['step'], "OUTPUT"))
                pinlist_out.append((f"DIR{num}", joint['pins']['dir'], "OUTPUT"))
                if joint.get('cl'):
                    pinlist_out.append((f"ENCA{num}", joint['pins']['enc_a'], "INPUT"))
                    pinlist_out.append((f"ENCB{num}", joint['pins']['enc_b'], "INPUT"))
        return pinlist_out

    def joints(self):
        joints_out = 0
        for num, joint in enumerate(self.jdata['joints']):
            if joint['type'] == "stepper":
                joints_out += 1
        return joints_out

    def funcs(self):
        func_out = ["    // stepgen's"]
        for num, joint in enumerate(self.jdata['joints']):
            if joint['type'] == "stepper":

                if joint.get('cl'):
                    func_out.append(f"    quad quad{num} (")
                    func_out.append("        .clk (sysclk),")
                    func_out.append(f"        .quadA (ENCA{num}),")
                    func_out.append(f"        .quadB (ENCB{num}),")
                    func_out.append(f"        .pos (jointFeedback{num})")
                    func_out.append("    );")
                    func_out.append(f"    stepgen_nf stepgen{num} (")
                    func_out.append("        .clk (sysclk),")
                    func_out.append(f"        .jointFreqCmd (jointFreqCmd{num}),")
                    func_out.append(f"        .DIR (DIR{num}),")
                    func_out.append(f"        .STP (STP{num})")
                    func_out.append("    );")
                else:
                    func_out.append(f"    stepgen stepgen{num} (")
                    func_out.append("        .clk (sysclk),")
                    func_out.append(f"        .jointFreqCmd (jointFreqCmd{num}),")
                    func_out.append(f"        .jointFeedback (jointFeedback{num}),")
                    func_out.append(f"        .DIR (DIR{num}),")
                    func_out.append(f"        .STP (STP{num})")
                    func_out.append("    );")

        return func_out

    def ips(self):
        return """
module stepgen
    (
        input clk,
        input signed [31:0] jointFreqCmd,
        output signed [31:0] jointFeedback,
        output DIR,
        output STP
    );
    assign DIR = (jointFreqCmd > 0);
    reg [31:0] jointCounter = 32'd0;
    reg [31:0] jointFreqCmdAbs = 32'd0;
    reg signed [31:0] jointFeedbackMem = 32'd0;
    reg step = 0;
    assign STP = step;
    assign jointFeedback = jointFeedbackMem;
    always @ (posedge clk) begin
        if (DIR) begin
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
                    if (DIR) begin
                        jointFeedbackMem = jointFeedbackMem + 1;
                    end else begin
                        jointFeedbackMem = jointFeedbackMem - 1;
                    end
                end
            end
        end
    end
endmodule

module stepgen_nf
    (
        input clk,
        input signed [31:0] jointFreqCmd,
        output DIR,
        output STP
    );
    assign DIR = (jointFreqCmd > 0);
    reg [31:0] jointCounter = 32'd0;
    reg [31:0] jointFreqCmdAbs = 32'd0;
    reg step = 0;
    assign STP = step;
    always @ (posedge clk) begin
        if (DIR) begin
            jointFreqCmdAbs = jointFreqCmd / 2;
        end else begin
            jointFreqCmdAbs = -jointFreqCmd / 2;
        end
        jointCounter <= jointCounter + 1;
        if (jointFreqCmd != 0) begin
            if (jointCounter >= jointFreqCmdAbs) begin
                step <= ~step;
                jointCounter <= 32'b0;
            end
        end
    end
endmodule

module quad
    (
        input clk,
        input quadA,
        input quadB,
        output [31:0] pos
    );
    reg [2:0] quadA_delayed, quadB_delayed;
    always @(posedge clk) quadA_delayed <= {quadA_delayed[1:0], quadA};
    always @(posedge clk) quadB_delayed <= {quadB_delayed[1:0], quadB};
    wire count_enable = quadA_delayed[1] ^ quadA_delayed[2] ^ quadB_delayed[1] ^ quadB_delayed[2];
    wire count_direction = quadA_delayed[1] ^ quadB_delayed[2];
    reg [31:0] count = 0;
    assign pos = count;
    always @(posedge clk) begin
        if (count_enable) begin
            if(count_direction) begin
                count <= count + 1; 
            end else begin
                count <= count - 1;
            end
        end
    end
endmodule 

"""
