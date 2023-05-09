class Plugin:
    def __init__(self, jdata):
        self.jdata = jdata

    def pinlist(self):
        pinlist_out = []
        for num, vin in enumerate(self.jdata.get("vin", ())):
            pinlist_out.append((f"VIN{num}", vin["pin"], "INPUT"))
        return pinlist_out

    def vins(self):
        vins_out = 0
        for _num, _vin in enumerate(self.jdata.get("vin", ())):
            vins_out += 1
        return vins_out

    def funcs(self):
        func_out = ["    // vin's"]
        for num, _vin in enumerate(self.jdata.get("vin", ())):
            func_out.append(f"    assign processVariable{num} = 0;")

        return func_out
