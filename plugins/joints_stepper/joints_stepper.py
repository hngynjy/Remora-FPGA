class Plugin:
    def __init__(self, jdata):
        self.jdata = jdata

    def pinlist(self):
        pinlist_out = []
        for num, joint in enumerate(self.jdata["joints"]):
            if joint["type"] == "stepper":
                if "enable" in joint["pins"]:
                    pinlist_out.append((f"EN{num}", joint["pins"]["enable"], "OUTPUT"))
                pinlist_out.append((f"STP{num}", joint["pins"]["step"], "OUTPUT"))
                pinlist_out.append((f"DIR{num}", joint["pins"]["dir"], "OUTPUT"))
                if joint.get("cl"):
                    pinlist_out.append((f"ENCA{num}", joint["pins"]["enc_a"], "INPUT"))
                    pinlist_out.append((f"ENCB{num}", joint["pins"]["enc_b"], "INPUT"))

        return pinlist_out

    def joints(self):
        joints_out = 0
        for _num, joint in enumerate(self.jdata["joints"]):
            if joint["type"] == "stepper":
                joints_out += 1
        return joints_out

    def funcs(self):
        func_out = ["    // stepgen's"]
        for num, joint in enumerate(self.jdata["joints"]):
            if joint["type"] == "stepper":

                if "enable" in joint["pins"]:
                    func_out.append(f"    assign EN{num} = jointEnable{num} && ~ERROR;")

                if joint.get("cl"):
                    func_out.append(f"    quad_encoder quad{num} (")
                    func_out.append("        .clk (sysclk),")
                    func_out.append(f"        .quadA (ENCA{num}),")
                    func_out.append(f"        .quadB (ENCB{num}),")
                    func_out.append(f"        .pos (jointFeedback{num})")
                    func_out.append("    );")
                    func_out.append(f"    stepgen_nf stepgen{num} (")
                    func_out.append("        .clk (sysclk),")
                    func_out.append(f"        .jointEnable (jointEnable{num} && !ERROR),")
                    func_out.append(f"        .jointFreqCmd (jointFreqCmd{num}),")
                    func_out.append(f"        .DIR (DIR{num}),")
                    func_out.append(f"        .STP (STP{num})")
                    func_out.append("    );")
                else:
                    func_out.append(f"    stepgen stepgen{num} (")
                    func_out.append("        .clk (sysclk),")
                    func_out.append(f"        .jointEnable (jointEnable{num} && !ERROR),")
                    func_out.append(f"        .jointFreqCmd (jointFreqCmd{num}),")
                    func_out.append(f"        .jointFeedback (jointFeedback{num}),")
                    func_out.append(f"        .DIR (DIR{num}),")
                    func_out.append(f"        .STP (STP{num})")
                    func_out.append("    );")

        return func_out

    def ips(self):
        return ["quad_encoder.v", "stepgen.v"]
