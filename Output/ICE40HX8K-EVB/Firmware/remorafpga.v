
/*
    ######### ICE40HX8K-EVB #########
*/


module spidev
    #(parameter BUFFER_SIZE=8)
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



module pwm
    #(parameter BITS = 16)
    (
        input clk,
        input [BITS - 1 : 0] dty,
        output pwm
    );
    reg rPwm;
    reg [BITS - 1 : 0] rDuty;
    wire pwmNext;
    wire [BITS - 1 : 0] dutyNext;
    always @(posedge clk)
    begin
        rPwm <= pwmNext;
        rDuty <= dutyNext;
    end
    assign dutyNext = rDuty + 1;
    assign pwmNext = rDuty < dty;
    assign pwm = rPwm;
endmodule



module stepgen
    (
        input clk,
        input signed [31:0] jointFreqCmd,
        output signed [31:0] jointFeedback,
        output DIR,
        output STP
    );
    assign DIR = (jointFreqCmd > 0);
    reg [31:0] jointCounter = 32'd0;
    reg [31:0] jointFreqCmdAbs = 32'd0;
    reg signed [31:0] jointFeedbackMem = 32'd0;
    reg step = 0;
    assign STP = step;
    assign jointFeedback = jointFeedbackMem;
    always @ (posedge clk) begin
        if (DIR) begin
            jointFreqCmdAbs = jointFreqCmd / 2;
        end else begin
            jointFreqCmdAbs = -jointFreqCmd / 2;
        end
        jointCounter <= jointCounter + 1;
        if (jointFreqCmd != 0) begin
            if (jointCounter >= jointFreqCmdAbs) begin
                step <= ~step;
                jointCounter <= 32'b0;
                if (step) begin
                    if (DIR) begin
                        jointFeedbackMem = jointFeedbackMem + 1;
                    end else begin
                        jointFeedbackMem = jointFeedbackMem - 1;
                    end
                end
            end
        end
    end
endmodule

module stepgen_nf
    (
        input clk,
        input signed [31:0] jointFreqCmd,
        output DIR,
        output STP
    );
    assign DIR = (jointFreqCmd > 0);
    reg [31:0] jointCounter = 32'd0;
    reg [31:0] jointFreqCmdAbs = 32'd0;
    reg step = 0;
    assign STP = step;
    always @ (posedge clk) begin
        if (DIR) begin
            jointFreqCmdAbs = jointFreqCmd / 2;
        end else begin
            jointFreqCmdAbs = -jointFreqCmd / 2;
        end
        jointCounter <= jointCounter + 1;
        if (jointFreqCmd != 0) begin
            if (jointCounter >= jointFreqCmdAbs) begin
                step <= ~step;
                jointCounter <= 32'b0;
            end
        end
    end
endmodule

module quad
    (
        input clk,
        input quadA,
        input quadB,
        output [31:0] pos
    );
    reg [2:0] quadA_delayed, quadB_delayed;
    always @(posedge clk) quadA_delayed <= {quadA_delayed[1:0], quadA};
    always @(posedge clk) quadB_delayed <= {quadB_delayed[1:0], quadB};
    wire count_enable = quadA_delayed[1] ^ quadA_delayed[2] ^ quadB_delayed[1] ^ quadB_delayed[2];
    wire count_direction = quadA_delayed[1] ^ quadB_delayed[2];
    reg [31:0] count = 0;
    assign pos = count;
    always @(posedge clk) begin
        if (count_enable) begin
            if(count_direction) begin
                count <= count + 1; 
            end else begin
                count <= count - 1;
            end
        end
    end
endmodule 



module top (
        input sysclk,
        input SPI_MOSI,
        output SPI_MISO,
        input SPI_SCK,
        input SPI_SSEL,
        output PWMOUT0,
        output PWMOUT1,
        output PWMOUT2,
        output PWMOUT3,
        output PWMOUT4,
        output PWMOUT5,
        input DIN0,
        input DIN1,
        input DIN2,
        input DIN3,
        input DIN4,
        input DIN5,
        output DOUT0,
        output DOUT1,
        output DOUT2,
        output DOUT3,
        output DOUT4,
        output DOUT5,
        output DOUT6,
        output DOUT7,
        output STP0,
        output DIR0,
        input ENCA0,
        input ENCB0,
        output STP1,
        output DIR1,
        output STP2,
        output DIR2,
        output STP3,
        output DIR3,
        output STP4,
        output DIR4,
        output STP5,
        output DIR5,
        output STP6,
        output DIR6,
        output STP7,
        output DIR7
    );


    parameter BUFFER_SIZE = 400;

    wire[399:0] rx_data;
    wire[399:0] tx_data;
    reg signed [31:0] header_tx = 32'h64617461;

    // fake din's to fit byte
    reg DIN6 = 0;
    reg DIN7 = 0;

    // vouts 6
    wire [15:0] setPoint0;
    wire [15:0] setPoint1;
    wire [15:0] setPoint2;
    wire [15:0] setPoint3;
    wire [15:0] setPoint4;
    wire [15:0] setPoint5;

    // vins 0

    // joints 8
    wire signed [31:0] jointFreqCmd0;
    wire signed [31:0] jointFreqCmd1;
    wire signed [31:0] jointFreqCmd2;
    wire signed [31:0] jointFreqCmd3;
    wire signed [31:0] jointFreqCmd4;
    wire signed [31:0] jointFreqCmd5;
    wire signed [31:0] jointFreqCmd6;
    wire signed [31:0] jointFreqCmd7;
    wire signed [31:0] jointFeedback0;
    wire signed [31:0] jointFeedback1;
    wire signed [31:0] jointFeedback2;
    wire signed [31:0] jointFeedback3;
    wire signed [31:0] jointFeedback4;
    wire signed [31:0] jointFeedback5;
    wire signed [31:0] jointFeedback6;
    wire signed [31:0] jointFeedback7;

    // rx_data 400
    assign header_rx = {rx_data[375:368], rx_data[383:376], rx_data[391:384], rx_data[399:392]};
    assign jointFreqCmd0 = {rx_data[343:336], rx_data[351:344], rx_data[359:352], rx_data[367:360]};
    assign jointFreqCmd1 = {rx_data[311:304], rx_data[319:312], rx_data[327:320], rx_data[335:328]};
    assign jointFreqCmd2 = {rx_data[279:272], rx_data[287:280], rx_data[295:288], rx_data[303:296]};
    assign jointFreqCmd3 = {rx_data[247:240], rx_data[255:248], rx_data[263:256], rx_data[271:264]};
    assign jointFreqCmd4 = {rx_data[215:208], rx_data[223:216], rx_data[231:224], rx_data[239:232]};
    assign jointFreqCmd5 = {rx_data[183:176], rx_data[191:184], rx_data[199:192], rx_data[207:200]};
    assign jointFreqCmd6 = {rx_data[151:144], rx_data[159:152], rx_data[167:160], rx_data[175:168]};
    assign jointFreqCmd7 = {rx_data[119:112], rx_data[127:120], rx_data[135:128], rx_data[143:136]};
    assign setPoint0 = {rx_data[103:96], rx_data[111:104]};
    assign setPoint1 = {rx_data[87:80], rx_data[95:88]};
    assign setPoint2 = {rx_data[71:64], rx_data[79:72]};
    assign setPoint3 = {rx_data[55:48], rx_data[63:56]};
    assign setPoint4 = {rx_data[39:32], rx_data[47:40]};
    assign setPoint5 = {rx_data[23:16], rx_data[31:24]};
    assign jointEnable0 = rx_data[15];
    assign jointEnable1 = rx_data[14];
    assign jointEnable2 = rx_data[13];
    assign jointEnable3 = rx_data[12];
    assign jointEnable4 = rx_data[11];
    assign jointEnable5 = rx_data[10];
    assign jointEnable6 = rx_data[9];
    assign jointEnable7 = rx_data[8];
    assign DOUT7 = rx_data[7];
    assign DOUT6 = rx_data[6];
    assign DOUT5 = rx_data[5];
    assign DOUT4 = rx_data[4];
    assign DOUT3 = rx_data[3];
    assign DOUT2 = rx_data[2];
    assign DOUT1 = rx_data[1];
    assign DOUT0 = rx_data[0];

    // tx_data 296
    assign tx_data = {
        header_tx[7:0], header_tx[15:8], header_tx[23:16], header_tx[31:24],
        jointFeedback0[7:0], jointFeedback0[15:8], jointFeedback0[23:16], jointFeedback0[31:24],
        jointFeedback1[7:0], jointFeedback1[15:8], jointFeedback1[23:16], jointFeedback1[31:24],
        jointFeedback2[7:0], jointFeedback2[15:8], jointFeedback2[23:16], jointFeedback2[31:24],
        jointFeedback3[7:0], jointFeedback3[15:8], jointFeedback3[23:16], jointFeedback3[31:24],
        jointFeedback4[7:0], jointFeedback4[15:8], jointFeedback4[23:16], jointFeedback4[31:24],
        jointFeedback5[7:0], jointFeedback5[15:8], jointFeedback5[23:16], jointFeedback5[31:24],
        jointFeedback6[7:0], jointFeedback6[15:8], jointFeedback6[23:16], jointFeedback6[31:24],
        jointFeedback7[7:0], jointFeedback7[15:8], jointFeedback7[23:16], jointFeedback7[31:24],
        DIN7,
        DIN6,
        DIN5,
        DIN4,
        DIN3,
        DIN2,
        DIN1,
        DIN0,
        104'd0
    };

    // spi interface
    spidev #(BUFFER_SIZE) spi1 (
        .clk (sysclk),
        .SPI_SCK (SPI_SCK),
        .SPI_SSEL (SPI_SSEL),
        .SPI_MOSI (SPI_MOSI),
        .SPI_MISO (SPI_MISO),
        .rx_data (rx_data),
        .tx_data (tx_data)
    );

    // pwm's
    pwm pwm0 (
        .clk (sysclk),
        .dty (setPoint0),
        .pwm (PWMOUT0)
    );
    pwm pwm1 (
        .clk (sysclk),
        .dty (setPoint1),
        .pwm (PWMOUT1)
    );
    pwm pwm2 (
        .clk (sysclk),
        .dty (setPoint2),
        .pwm (PWMOUT2)
    );
    pwm pwm3 (
        .clk (sysclk),
        .dty (setPoint3),
        .pwm (PWMOUT3)
    );
    pwm pwm4 (
        .clk (sysclk),
        .dty (setPoint4),
        .pwm (PWMOUT4)
    );
    pwm pwm5 (
        .clk (sysclk),
        .dty (setPoint5),
        .pwm (PWMOUT5)
    );

    // rcservo's

    // stepgen's
    quad quad0 (
        .clk (sysclk),
        .quadA (ENCA0),
        .quadB (ENCB0),
        .pos (jointFeedback0)
    );
    stepgen_nf stepgen0 (
        .clk (sysclk),
        .jointFreqCmd (jointFreqCmd0),
        .DIR (DIR0),
        .STP (STP0)
    );
    stepgen stepgen1 (
        .clk (sysclk),
        .jointFreqCmd (jointFreqCmd1),
        .jointFeedback (jointFeedback1),
        .DIR (DIR1),
        .STP (STP1)
    );
    stepgen stepgen2 (
        .clk (sysclk),
        .jointFreqCmd (jointFreqCmd2),
        .jointFeedback (jointFeedback2),
        .DIR (DIR2),
        .STP (STP2)
    );
    stepgen stepgen3 (
        .clk (sysclk),
        .jointFreqCmd (jointFreqCmd3),
        .jointFeedback (jointFeedback3),
        .DIR (DIR3),
        .STP (STP3)
    );
    stepgen stepgen4 (
        .clk (sysclk),
        .jointFreqCmd (jointFreqCmd4),
        .jointFeedback (jointFeedback4),
        .DIR (DIR4),
        .STP (STP4)
    );
    stepgen stepgen5 (
        .clk (sysclk),
        .jointFreqCmd (jointFreqCmd5),
        .jointFeedback (jointFeedback5),
        .DIR (DIR5),
        .STP (STP5)
    );
    stepgen stepgen6 (
        .clk (sysclk),
        .jointFreqCmd (jointFreqCmd6),
        .jointFeedback (jointFeedback6),
        .DIR (DIR6),
        .STP (STP6)
    );
    stepgen stepgen7 (
        .clk (sysclk),
        .jointFreqCmd (jointFreqCmd7),
        .jointFeedback (jointFeedback7),
        .DIR (DIR7),
        .STP (STP7)
    );

endmodule
