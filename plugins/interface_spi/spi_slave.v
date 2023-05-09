
module spi_slave
    #(parameter BUFFER_SIZE=64, parameter MSGID=32'h74697277)
    (
        input clk,
        input SPI_SCK,
        input SPI_SSEL,
        input SPI_MOSI,
        input [BUFFER_SIZE-1:0] tx_data,
        output [BUFFER_SIZE-1:0] rx_data,
        output SPI_MISO
        //output [15:0] counter
    );
    //assign counter = bitcnt;
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
            if (byte_data_receive[BUFFER_SIZE-1:BUFFER_SIZE-32] == MSGID) begin
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
