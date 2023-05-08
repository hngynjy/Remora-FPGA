class Plugin:
    def __init__(self, jdata):
        self.jdata = jdata

    def pinlist(self):
        pinlist_out = []
        for num, joint in enumerate(self.jdata["joints"]):
            if joint["type"] == "rcservo":
                pinlist_out.append((f"RCSERVO{num}", joint["pin"], "OUTPUT"))
        return pinlist_out

    def joints(self):
        joints_out = 0
        for num, joint in enumerate(self.jdata["joints"]):
            if joint["type"] == "rcservo":
                joints_out += 1
        return joints_out

    def funcs(self):
        func_out = ["    // stepgen's"]
        sysclk = int(self.jdata["clock"]["speed"])
        for num, joint in enumerate(self.jdata["joints"]):
            if joint["type"] == "rcservo":
                scale = joint.get("scale", 64)
                func_out.append(
                    f"    rcservo #({sysclk // 1000 * 10}, {sysclk // 10000 * 15}, {scale}) rcservo{num} ("
                )
                func_out.append("        .clk (sysclk),")
                func_out.append(f"        .jointFreqCmd (jointFreqCmd{num}),")
                func_out.append(f"        .jointFeedback (jointFeedback{num}),")
                func_out.append(f"        .PWM (RCSERVO{num})")
                func_out.append("    );")

        return func_out

    def ips(self):
        return ["rcservo.v"]
