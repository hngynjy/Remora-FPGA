
/*
    ######### TinyFPGA-BX #########
*/


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


module rcservo
    #(
        parameter servo_freq = 480000, // clk / 1000 * 10
        parameter servo_center = 72000, // clk / 1000 * 1.5
        parameter servo_scale = 64
    )
    (
        input clk,
        input signed [31:0] jointFreqCmd,
        output signed [31:0] jointFeedback,
        output PWM
    );
    reg [31:0] jointCounter = 32'd0;
    reg [31:0] jointFreqCmdAbs = 32'd0;
    reg signed [31:0] jointFeedbackMem = 32'd0;
    reg step = 0;
    assign jointFeedback = jointFeedbackMem;
    always @ (posedge clk) begin
        if (jointFreqCmd > 0) begin
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
                    if (jointFreqCmd > 0) begin
                        jointFeedbackMem = jointFeedbackMem + 1;
                    end else begin
                        jointFeedbackMem = jointFeedbackMem - 1;
                    end
                end
            end
        end
    end
    reg pulse;
    assign PWM = pulse;
    reg [31:0] counter = 0;
    always @ (posedge clk) begin
        counter = counter + 1;
        if (counter == servo_freq) begin
            pulse = 1;
            counter = 0;
        end else if (counter == servo_center + jointFeedbackMem / servo_scale) begin
            pulse = 0;
        end
    end
endmodule

module blink
    (
        input clk,
        input [31:0] speed,
        output led
    );
    reg rled;
    reg [31:0] counter;
    assign led = rled;
    always @(posedge clk) begin
        if (counter == 0) begin
            counter <= speed;
            rled <= ~rled;
        end else begin
            counter <= counter - 1;
        end
    end
endmodule


module top (
        input sysclk_in,
        output BLINK_LED,
        input DIN0,
        input DIN1,
        input DIN2,
        input DIN3,
        input DIN4,
        input SPI_MOSI,
        output SPI_MISO,
        input SPI_SCK,
        input SPI_SSEL,
        output DOUT0,
        output DOUT1,
        output DOUT2,
        output DOUT3,
        output DOUT4,
        output DOUT5,
        output PWMOUT0,
        output PWMOUT1,
        input VIN0,
        input VIN1,
        output STP0,
        output DIR0,
        output STP1,
        output DIR1,
        output STP2,
        output DIR2,
        output STP3,
        output DIR3,
        output STP4,
        output DIR4
    );


    wire sysclk;
    wire locked;
    pll mypll(sysclk_in, sysclk, locked);

    blink blink1 (
        .clk (sysclk),
        .speed (24000000),
        .led (BLINK_LED)
    );

    parameter BUFFER_SIZE = 240;

    wire[239:0] rx_data;
    wire[239:0] tx_data;
    reg signed [31:0] header_tx = 32'h64617461;

    wire jointEnable0;
    wire jointEnable1;
    wire jointEnable2;
    wire jointEnable3;
    wire jointEnable4;

    // fake din's to fit byte
    reg DIN5 = 0;
    reg DIN6 = 0;
    reg DIN7 = 0;

    // vouts 2
    wire [15:0] setPoint0;
    wire [15:0] setPoint1;

    // vins 2
    wire [15:0] processVariable0;
    wire [15:0] processVariable1;

    // joints 5
    wire signed [31:0] jointFreqCmd0;
    wire signed [31:0] jointFreqCmd1;
    wire signed [31:0] jointFreqCmd2;
    wire signed [31:0] jointFreqCmd3;
    wire signed [31:0] jointFreqCmd4;
    wire signed [31:0] jointFeedback0;
    wire signed [31:0] jointFeedback1;
    wire signed [31:0] jointFeedback2;
    wire signed [31:0] jointFeedback3;
    wire signed [31:0] jointFeedback4;

    // rx_data 240
    wire [31:0] header_rx;
    assign header_rx = {rx_data[215:208], rx_data[223:216], rx_data[231:224], rx_data[239:232]};
    assign jointFreqCmd0 = {rx_data[183:176], rx_data[191:184], rx_data[199:192], rx_data[207:200]};
    assign jointFreqCmd1 = {rx_data[151:144], rx_data[159:152], rx_data[167:160], rx_data[175:168]};
    assign jointFreqCmd2 = {rx_data[119:112], rx_data[127:120], rx_data[135:128], rx_data[143:136]};
    assign jointFreqCmd3 = {rx_data[87:80], rx_data[95:88], rx_data[103:96], rx_data[111:104]};
    assign jointFreqCmd4 = {rx_data[55:48], rx_data[63:56], rx_data[71:64], rx_data[79:72]};
    assign setPoint0 = {rx_data[39:32], rx_data[47:40]};
    assign setPoint1 = {rx_data[23:16], rx_data[31:24]};
    assign jointEnable0 = rx_data[15];
    assign jointEnable1 = rx_data[14];
    assign jointEnable2 = rx_data[13];
    assign jointEnable3 = rx_data[12];
    assign jointEnable4 = rx_data[11];
    // assign jointEnable5 = rx_data[10];
    // assign jointEnable6 = rx_data[9];
    // assign jointEnable7 = rx_data[8];
    // assign DOUT7 = rx_data[7];
    // assign DOUT6 = rx_data[6];
    assign DOUT5 = rx_data[5];
    assign DOUT4 = rx_data[4];
    assign DOUT3 = rx_data[3];
    assign DOUT2 = rx_data[2];
    assign DOUT1 = rx_data[1];
    assign DOUT0 = rx_data[0];

    // tx_data 232
    assign tx_data = {
        header_tx[7:0], header_tx[15:8], header_tx[23:16], header_tx[31:24],
        jointFeedback0[7:0], jointFeedback0[15:8], jointFeedback0[23:16], jointFeedback0[31:24],
        jointFeedback1[7:0], jointFeedback1[15:8], jointFeedback1[23:16], jointFeedback1[31:24],
        jointFeedback2[7:0], jointFeedback2[15:8], jointFeedback2[23:16], jointFeedback2[31:24],
        jointFeedback3[7:0], jointFeedback3[15:8], jointFeedback3[23:16], jointFeedback3[31:24],
        jointFeedback4[7:0], jointFeedback4[15:8], jointFeedback4[23:16], jointFeedback4[31:24],
        processVariable0[7:0], processVariable0[15:8],
        processVariable1[7:0], processVariable1[15:8],
        DIN7,
        DIN6,
        DIN5,
        DIN4,
        DIN3,
        DIN2,
        DIN1,
        DIN0,
        8'd0
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

    // vin's
    assign processVariable0 = 0;
    assign processVariable1 = 0;

    // stepgen's
    stepgen stepgen0 (
        .clk (sysclk),
        .jointFreqCmd (jointFreqCmd0),
        .jointFeedback (jointFeedback0),
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

    // stepgen's

endmodule
