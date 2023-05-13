class Plugin:
    def __init__(self, jdata):
        self.jdata = jdata

    def pinlist(self):
        pinlist_out = []
        for num, vin in enumerate(self.jdata.get("vin", [])):
            if vin.get("type") == "encoder":
                pullup = vin.get("pullup", False)
                pinlist_out.append((f"ENCODER_A{num}", vin["pina"], "INPUT", pullup))
                pinlist_out.append((f"ENCODER_B{num}", vin["pinb"], "INPUT", pullup))
        return pinlist_out

    def vins(self):
        vins_out = 0
        for _num, vin in enumerate(self.jdata.get("vin", [])):
            if vin.get("type") == "encoder":
                vins_out += 1
        return vins_out

    def funcs(self):
        func_out = ["    // vencoder's"]
        for num, vin in enumerate(self.jdata.get("vin", [])):
            if vin.get("type") == "encoder":
                func_out.append(f"    assign processVariable{num} = 0;")

        return func_out

    def funcs(self):
        func_out = ["    // vencoder's"]
        for num, vin in enumerate(self.jdata.get("vin", [])):
            if vin.get("type") == "encoder":
                func_out.append(f"    quad_encoder #(32) vencoder{num} (")
                func_out.append("        .clk (sysclk),")
                func_out.append(f"        .quadA (ENCODER_A{num}),")
                func_out.append(f"        .quadB (ENCODER_B{num}),")
                func_out.append(f"        .pos (processVariable{num})")
                func_out.append("    );")

        return func_out

    def ips(self):
        files = ["quad_encoder.v"]
        files = []
        return files

