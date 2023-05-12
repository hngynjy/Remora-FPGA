class Plugin:
    def __init__(self, jdata):
        self.jdata = jdata

    def pinlist(self):
        pinlist_out = []
        for num, joint in enumerate(self.jdata["joints"]):
            if joint["type"] == "pwmdir":
                if "enable" in joint["pins"]:
                    pinlist_out.append((f"EN{num}", joint["pins"]["enable"], "OUTPUT"))
                pinlist_out.append((f"PWMDIR_PWM{num}", joint["pins"]["step"], "OUTPUT"))
                pinlist_out.append((f"PWMDIR_DIR{num}", joint["pins"]["dir"], "OUTPUT"))
                if joint.get("cl"):
                    pullup = joint["pins"].get("pullup", False)
                    pinlist_out.append((f"ENCA{num}", joint["pins"]["enc_a"], "INPUT", pullup))
                    pinlist_out.append((f"ENCB{num}", joint["pins"]["enc_b"], "INPUT", pullup))
        return pinlist_out

    def joints(self):
        joints_out = 0
        for _num, joint in enumerate(self.jdata["joints"]):
            if joint["type"] == "pwmdir":
                joints_out += 1
        return joints_out

    def jointcalcs(self):
        jointcalcs_out = {}
        sysclk = int(self.jdata["clock"]["speed"])
        for num, joint in enumerate(self.jdata["joints"]):
            if joint["type"] == "pwmdir":
                pwm_freq = 100000
                jointcalcs_out[num] = ("none", int(sysclk / pwm_freq))
        return jointcalcs_out

    def funcs(self):
        func_out = ["    // pwmdir's"]
        sysclk = int(self.jdata["clock"]["speed"])
        for num, joint in enumerate(self.jdata["joints"]):
            if joint["type"] == "pwmdir":
                pwm_freq = 100000

                if "enable" in joint["pins"]:
                    func_out.append(f"    assign EN{num} = jointEnable{num} && ~ERROR;")

                if joint.get("cl"):
                    func_out.append(f"    quad_encoder quad{num} (")
                    func_out.append("        .clk (sysclk),")
                    func_out.append(f"        .quadA (ENCA{num}),")
                    func_out.append(f"        .quadB (ENCB{num}),")
                    func_out.append(f"        .pos (jointFeedback{num})")
                    func_out.append("    );")
                    func_out.append(f"    pwmdir_nf pwmdir{num} (")
                    func_out.append("        .clk (sysclk),")
                    func_out.append(f"        .jointEnable (jointEnable{num} && !ERROR),")
                    func_out.append(f"        .jointFreqCmd (jointFreqCmd{num}),")
                    func_out.append(f"        .DIR (PWMDIR_DIR{num}),")
                    func_out.append(f"        .PWM (PWMDIR_PWM{num})")
                    func_out.append("    );")
                else:
                    func_out.append(f"    pwmdir #({int(sysclk / pwm_freq)}) pwmdir{num} (")
                    func_out.append("        .clk (sysclk),")
                    func_out.append(f"        .jointEnable (jointEnable{num} && !ERROR),")
                    func_out.append(f"        .jointFreqCmd (jointFreqCmd{num}),")
                    func_out.append(f"        .jointFeedback (jointFeedback{num}),")
                    func_out.append(f"        .DIR (PWMDIR_DIR{num}),")
                    func_out.append(f"        .PWM (PWMDIR_PWM{num})")
                    func_out.append("    );")

        return func_out

    def ips(self):
        return ["pwm_dir.v"]
