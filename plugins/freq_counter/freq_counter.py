class Plugin:
    def __init__(self, jdata):
        self.jdata = jdata

    def pinlist(self):
        pinlist_out = []
        for num, vin in enumerate(self.jdata.get("vin", [])):
            if vin.get("type") == "frequency":
                pullup = vin.get("pullup", False)
                pinlist_out.append((f"VIN{num}", vin["pin"], "INPUT", pullup))
        return pinlist_out

    def vins(self):
        vins_out = 0
        for _num, vin in enumerate(self.jdata.get("vin", [])):
            if vin.get("type") == "frequency":
                vins_out += 1
        return vins_out

    def funcs(self):
        func_out = ["    // vin's"]
        for num, vin in enumerate(self.jdata.get("vin", [])):
            if vin.get("type") == "frequency":
                func_out.append(f"    assign processVariable{num} = 0;")

        return func_out

    def funcs(self):
        func_out = ["    // vin's"]
        for num, vin in enumerate(self.jdata.get("vin", [])):
            if vin.get("type") == "frequency":
                func_out.append(f"    freq_counter #({self.jdata['clock']['speed']}) freq_counter{num} (")
                func_out.append("        .clk (sysclk),")
                func_out.append(f"        .frequency (processVariable{num}),")
                func_out.append(f"        .SIGNAL (VIN{num})")
                func_out.append("    );")

        return func_out

    def ips(self):
        files = ["freq_counter.v"]
        return files

