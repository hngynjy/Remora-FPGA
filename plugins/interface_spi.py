


class Plugin():

    def __init__(self, jdata):
        self.jdata = jdata

    def pinlist(self):
        pinlist_out = []
        if self.jdata['interface']['type'] == "spi":
            pinlist_out.append((f"SPI_MOSI", self.jdata['interface']['pins']['MOSI'], "INPUT"))
            pinlist_out.append((f"SPI_MISO", self.jdata['interface']['pins']['MISO'], "OUTPUT"))
            pinlist_out.append((f"SPI_SCK", self.jdata['interface']['pins']['SCK'], "INPUT"))
            pinlist_out.append((f"SPI_SSEL", self.jdata['interface']['pins']['SEL'], "INPUT"))
        return pinlist_out


    def funcs(self):
        func_out = ["    // spi interface"]
        func_out.append("    spidev #(BUFFER_SIZE) spi1 (")
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
        return """
module spidev
    #(parameter BUFFER_SIZE=64)
    (
        input clk,
        input SPI_SCK,
        input SPI_SSEL,
        input SPI_MOSI,
        input [BUFFER_SIZE-1:0] tx_data,
        output [BUFFER_SIZE-1:0] rx_data,
        output SPI_MISO
    );
    reg[2:0] SCKr;  always @(posedge clk) SCKr <= {SCKr[1:0], SPI_SCK};
    wire SCK_risingedge = (SCKr[2:1]==2'b01);  // now we can detect SCK rising edges
    wire SCK_fallingedge = (SCKr[2:1]==2'b10);  // and falling edges
    reg[2:0] SSELr;  always @(posedge clk) SSELr <= {SSELr[1:0], SPI_SSEL};
    wire SSEL_active = ~SSELr[1];  // SSEL is active low
    wire SSEL_startmessage = (SSELr[2:1]==2'b10);  // message starts at falling edge
    wire SSEL_endmessage = (SSELr[2:1]==2'b01);  // message stops at rising edge
    reg[15:0] bitcnt;
    reg byte_received;  // high when a byte has been received
    reg[BUFFER_SIZE-1:0] byte_data_received;
    reg[BUFFER_SIZE-1:0] byte_data_receive;
    reg[BUFFER_SIZE-1:0] byte_data_sent;
    assign rx_data = byte_data_received;
    always @(posedge clk)
    begin
        if(~SSEL_active) begin
            bitcnt <= 16'd0;
        end else begin
            if(SCK_risingedge) begin
                bitcnt <= bitcnt + 16'd1;
                byte_data_receive <= {byte_data_receive[BUFFER_SIZE-2:0], SPI_MOSI};
            end
        end
    end
    always @(posedge clk) byte_received <= SSEL_active && SCK_risingedge && (bitcnt == BUFFER_SIZE);
    always @(posedge clk) begin
        if (SSEL_endmessage) begin
            if (byte_data_receive[BUFFER_SIZE-1:BUFFER_SIZE-32] == 32'h74697277) begin
                byte_data_received <= byte_data_receive;
            end
        end
    end
    always @(posedge clk)
    if(SSEL_active)
    begin
        if(SSEL_startmessage) begin
            byte_data_sent = tx_data;
        end else begin
            if(SCK_fallingedge) begin
                if(bitcnt==16'd0)
                  byte_data_sent <= 8'h00;  // after that, we send 0s
                else
                  byte_data_sent <= {byte_data_sent[BUFFER_SIZE-2:0], 1'b0};
            end
        end
    end
    assign SPI_MISO = byte_data_sent[BUFFER_SIZE-1];  // send MSB first

endmodule

"""

