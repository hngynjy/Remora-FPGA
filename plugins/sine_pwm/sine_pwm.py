class Plugin:
    def __init__(self, jdata):
        self.jdata = jdata

    def pinlist(self):
        pinlist_out = []
        for num, vout in enumerate(self.jdata["vout"]):
            if vout["type"] == "sine":
                if "pins" in vout:
                    for pn, pin in enumerate(vout['pins']):
                        pinlist_out.append((f"SINEPWM{num}_{pn}", pin, "OUTPUT"))
                else:
                    pinlist_out.append((f"SINEPWM{num}", vout["pin"], "OUTPUT"))
        return pinlist_out

    def vouts(self):
        vouts_out = 0
        for _num, vout in enumerate(self.jdata["vout"]):
            if vout["type"] == "sine":
                vouts_out += 1
        return vouts_out

    def funcs(self):
        func_out = ["    // sine_pwm's"]
        for num, vout in enumerate(self.jdata["vout"]):
            if vout["type"] == "sine":

                if "pins" in vout:
                    pstep = 30 // len(vout['pins'])
                    start = 0
                    for pn, pin in enumerate(vout['pins']):
                        func_out.append(f"    sine_pwm #({start}) sine_pwm{num}_{pn} (")
                        func_out.append("        .clk (sysclk),")
                        func_out.append(f"        .freq (setPoint{num}),")
                        func_out.append(f"        .pwm_out (SINEPWM{num}_{pn})")
                        func_out.append("    );")
                        start = start + pstep

                else:
                    start = vout.get("start", 0)
                    func_out.append(f"    sine_pwm #({start}) sine_pwm{num} (")
                    func_out.append("        .clk (sysclk),")
                    func_out.append(f"        .freq (setPoint{num}),")
                    func_out.append(f"        .pwm_out (SINEPWM{num})")
                    func_out.append("    );")
        return func_out

    def ips(self):
        files = ["sine_pwm.v"]
        return files
