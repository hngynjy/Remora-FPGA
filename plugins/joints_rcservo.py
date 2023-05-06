


class Plugin():

    def __init__(self, jdata):
        self.jdata = jdata

    def pinlist(self):
        pinlist_out = []
        for num, joint in enumerate(self.jdata['joints']):
            if joint['type'] == "rcservo":
                pinlist_out.append((f"RCOUT{num}", joint['pins']['out'], "OUTPUT"))
        return pinlist_out

    def joints(self):
        joints_out = 0
        for num, joint in enumerate(self.jdata['joints']):
            if joint['type'] == "rcservo":
                joints_out += 1
        return joints_out

    def funcs(self):
        func_out = ["    // rcservo's"]
        for num, joint in enumerate(self.jdata['joints']):
            if joint['type'] == "rcservo":
                func_out.append(f"    rcservo rcservo{num} (")
                func_out.append(f"        .clk (sysclk),")
                func_out.append(f"        .dty (setPoint{num}),")
                func_out.append(f"        .pwm (RCOUT{num})")
                func_out.append("    );")

        return func_out

