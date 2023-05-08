class Plugin:
    def __init__(self, jdata):
        self.jdata = jdata

    def pinlist(self):
        pinlist_out = []
        if self.jdata["interface"]["type"] == "spi":
            pinlist_out.append(
                (f"SPI_MOSI", self.jdata["interface"]["pins"]["MOSI"], "INPUT")
            )
            pinlist_out.append(
                (f"SPI_MISO", self.jdata["interface"]["pins"]["MISO"], "OUTPUT")
            )
            pinlist_out.append(
                (f"SPI_SCK", self.jdata["interface"]["pins"]["SCK"], "INPUT")
            )
            pinlist_out.append(
                (f"SPI_SSEL", self.jdata["interface"]["pins"]["SEL"], "INPUT")
            )
        return pinlist_out

    def funcs(self):
        func_out = ["    // spi interface"]
        func_out.append("    spi_slave #(BUFFER_SIZE) spi1 (")
        func_out.append("        .clk (sysclk),")
        func_out.append("        .SPI_SCK (SPI_SCK),")
        func_out.append("        .SPI_SSEL (SPI_SSEL),")
        func_out.append("        .SPI_MOSI (SPI_MOSI),")
        func_out.append("        .SPI_MISO (SPI_MISO),")
        func_out.append("        .rx_data (rx_data),")
        func_out.append("        .tx_data (tx_data)")
        func_out.append("    );")
        return func_out

    def ips(self):
        files = ["spi_slave.v"]
        return files
