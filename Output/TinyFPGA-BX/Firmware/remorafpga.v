/*
    ######### TinyFPGA-BX #########
*/


module top (
        input sysclk_in,
        output ERROR_OUT,
        input VIN0,
        input VIN1,
        input SPI_MOSI,
        output SPI_MISO,
        input SPI_SCK,
        input SPI_SSEL,
        output STP0,
        output DIR0,
        output STP1,
        output DIR1,
        output STP2,
        output DIR2,
        output STP3,
        output DIR3,
        output STP4,
        output DIR4,
        output DOUT0,
        output DOUT1,
        output DOUT2,
        output DOUT3,
        output DOUT4,
        output DOUT5,
        input DIN0,
        input DIN1,
        input DIN2,
        input DIN3,
        input DIN4,
        output PWMOUT0,
        output PWMOUT1,
        output ENA
    );


    reg ESTOP = 0;
    wire ERROR;
    wire INTERFACE_TIMEOUT;
    assign ERROR = (INTERFACE_TIMEOUT | ESTOP);
    wire sysclk;
    wire locked;
    pll mypll(sysclk_in, sysclk, locked);

    assign ERROR_OUT = ERROR;

    parameter BUFFER_SIZE = 240;

    wire[239:0] rx_data;
    wire[239:0] tx_data;

    reg signed [31:0] header_tx;
    always @(posedge sysclk) begin
        if (ESTOP) begin
            header_tx = 32'h65737470;
        end else begin
            header_tx = 32'h64617461;
        end
    end

    wire jointEnable0;
    wire jointEnable1;
    wire jointEnable2;
    wire jointEnable3;
    wire jointEnable4;

    assign ENA = (jointEnable0 || jointEnable1 || jointEnable2 || jointEnable3 || jointEnable4) && ~ERROR;

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
    // assign jointEnable7 = rx_data[15];
    // assign jointEnable6 = rx_data[14];
    // assign jointEnable5 = rx_data[13];
    assign jointEnable4 = rx_data[12];
    assign jointEnable3 = rx_data[11];
    assign jointEnable2 = rx_data[10];
    assign jointEnable1 = rx_data[9];
    assign jointEnable0 = rx_data[8];
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



    // vin's
    freq_counter #(48000000) freq_counter0 (
        .clk (sysclk),
        .frequency (processVariable0),
        .SIGNAL (VIN0)
    );
    freq_counter #(48000000) freq_counter1 (
        .clk (sysclk),
        .frequency (processVariable1),
        .SIGNAL (VIN1)
    );

    // spi interface
    wire pkg_ok;
    spi_slave #(BUFFER_SIZE, 32'h74697277, 48000000) spi1 (
        .clk (sysclk),
        .SPI_SCK (SPI_SCK),
        .SPI_SSEL (SPI_SSEL),
        .SPI_MOSI (SPI_MOSI),
        .SPI_MISO (SPI_MISO),
        .rx_data (rx_data),
        .tx_data (tx_data),
        .pkg_timeout (INTERFACE_TIMEOUT)
    );

    // stepgen's
    stepgen stepgen0 (
        .clk (sysclk),
        .jointEnable (jointEnable0 && !ERROR),
        .jointFreqCmd (jointFreqCmd0),
        .jointFeedback (jointFeedback0),
        .DIR (DIR0),
        .STP (STP0)
    );
    stepgen stepgen1 (
        .clk (sysclk),
        .jointEnable (jointEnable1 && !ERROR),
        .jointFreqCmd (jointFreqCmd1),
        .jointFeedback (jointFeedback1),
        .DIR (DIR1),
        .STP (STP1)
    );
    stepgen stepgen2 (
        .clk (sysclk),
        .jointEnable (jointEnable2 && !ERROR),
        .jointFreqCmd (jointFreqCmd2),
        .jointFeedback (jointFeedback2),
        .DIR (DIR2),
        .STP (STP2)
    );
    stepgen stepgen3 (
        .clk (sysclk),
        .jointEnable (jointEnable3 && !ERROR),
        .jointFreqCmd (jointFreqCmd3),
        .jointFeedback (jointFeedback3),
        .DIR (DIR3),
        .STP (STP3)
    );
    stepgen stepgen4 (
        .clk (sysclk),
        .jointEnable (jointEnable4 && !ERROR),
        .jointFreqCmd (jointFreqCmd4),
        .jointFeedback (jointFeedback4),
        .DIR (DIR4),
        .STP (STP4)
    );

    // rcservos's

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

    // pwmdir's

endmodule
