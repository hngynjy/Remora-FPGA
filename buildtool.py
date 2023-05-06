
import os
import glob
import importlib
import sys
import json

data = open(sys.argv[1], "r").read()
jdata = json.loads(data)

# loading plugins
plugins = {}
for path in glob.glob("plugins/*.py"):
    plugin = path.split(".")[0].split("/")[1]
    vplugin = importlib.import_module(
        f".{plugin}", "plugins"
    )
    plugins[plugin] = vplugin.Plugin(jdata)


pinlists = {}

if jdata['toolchain'] == "icestorm":
    pinlists["main"] = (("sysclk", jdata['clock']['pin'], "INPUT"),)

if 'blink' in jdata:
    pinlists["main"] = (("BLINK_LED", jdata['blink']['pin'], "OUTPUT"),)

for plugin in plugins:
    if hasattr(plugins[plugin], "pinlist"):
        pinlists[plugin] = plugins[plugin].pinlist()

top_arguments = []
for pname, pins in pinlists.items():
    for pin in pins:
        top_arguments.append(f"{pin[2].lower()} {pin[0]}")

dins = 0
for plugin in plugins:
    if hasattr(plugins[plugin], "dins"):
        dins += plugins[plugin].dins()

douts = 0
for plugin in plugins:
    if hasattr(plugins[plugin], "douts"):
        douts += plugins[plugin].douts()

vouts = 0
for plugin in plugins:
    if hasattr(plugins[plugin], "vouts"):
        vouts += plugins[plugin].vouts()

vins = 0
for plugin in plugins:
    if hasattr(plugins[plugin], "vins"):
        vins += plugins[plugin].vins()

joints = 0
for plugin in plugins:
    if hasattr(plugins[plugin], "joints"):
        joints += plugins[plugin].joints()

joints_en_total = (joints + 7) // 8 * 8
douts_total = (douts + 7) // 8 * 8
dins_total = (dins + 7) // 8 * 8
tx_data_size = 32
tx_data_size += joints * 32
tx_data_size += vins * 16
tx_data_size += dins_total
rx_data_size = 32
rx_data_size += joints * 32
rx_data_size += vouts * 16
rx_data_size += joints_en_total
rx_data_size += douts_total
data_size = max(tx_data_size, rx_data_size)


# file structure
OUTPUT_PATH=f"Output/{jdata['name'].replace(' ', '_').replace('/', '_')}"
FIRMWARE_PATH=f"{OUTPUT_PATH}/Firmware"
SOURCE_PATH=f"{FIRMWARE_PATH}"
PINS_PATH=f"{FIRMWARE_PATH}"
LINUXCNC_PATH=f"{OUTPUT_PATH}/LinuxCNC"
os.system(f"mkdir -p {OUTPUT_PATH}")
os.system(f"mkdir -p {SOURCE_PATH}")
os.system(f"mkdir -p {PINS_PATH}")
os.system(f"mkdir -p {LINUXCNC_PATH}")

os.system(f"mkdir -p {LINUXCNC_PATH}/Components/")
os.system(f"cp -a files/LinuxCNC/Components/* {LINUXCNC_PATH}/Components/")
os.system(f"mkdir -p {LINUXCNC_PATH}/ConfigSamples/")
os.system(f"cp -a files/LinuxCNC/ConfigSamples/* {LINUXCNC_PATH}/ConfigSamples/")

if jdata['toolchain'] == "diamond":
    SOURCE_PATH=f"{FIRMWARE_PATH}/impl1/source"
    PINS_PATH=f"{FIRMWARE_PATH}/impl1/source"
    os.system(f"mkdir -p {SOURCE_PATH}")
    os.system(f"mkdir -p {PINS_PATH}")



if jdata['toolchain'] == "icestorm":
    # pins.pcf (icestorm)
    pcf_data = []
    for pname, pins in pinlists.items():
        pcf_data.append(f"### {pname} ###")
        for pin in pins:
            pcf_data.append(f"set_io {pin[0]} {pin[1]}")
        pcf_data.append("")
    open(f"{PINS_PATH}/pins.pcf", "w").write("\n".join(pcf_data))

    makefile_data = []
    makefile_data.append("")
    makefile_data.append(f"FAMILY  := {jdata['family']}")
    makefile_data.append(f"TYPE    := {jdata['type']}")
    makefile_data.append(f"PACKAGE := {jdata['package']}")
    makefile_data.append("")
    makefile_data.append("all: remorafpga.bin")
    makefile_data.append("")
    makefile_data.append("remorafpga.json: remorafpga.v")
    makefile_data.append("	yosys -q -l yosys.log -p 'synth_${FAMILY} -top top -json remorafpga.json' remorafpga.v")
    makefile_data.append("")
    makefile_data.append("remorafpga.asc: remorafpga.json pins.pcf")
    makefile_data.append("	nextpnr-${FAMILY} -q -l nextpnr.log --${TYPE} --package ${PACKAGE} --json remorafpga.json --pcf pins.pcf --asc remorafpga.asc")
    makefile_data.append("	@echo \"\"")
    makefile_data.append("	@grep -B 1 \"%$$\" nextpnr.log")
    makefile_data.append("	@echo \"\"")
    makefile_data.append("")
    makefile_data.append("remorafpga.bin: remorafpga.asc")
    makefile_data.append("	icepack remorafpga.asc remorafpga.bin")
    makefile_data.append("")
    makefile_data.append("clean:")
    makefile_data.append("	rm -rf remorafpga.bin remorafpga.asc remorafpga.json yosys.log nextpnr.log")
    makefile_data.append("")
    open(f"{FIRMWARE_PATH}/Makefile", "w").write("\n".join(makefile_data))


elif jdata['toolchain'] == "diamond":
    os.system(f"cp files/pif21.sty {FIRMWARE_PATH}/")

    ldf_data = []
    ldf_data.append('<?xml version="1.0" encoding="UTF-8"?>')
    ldf_data.append(f'<BaliProject version="3.2" title="remorafpga" device="{jdata["type"]}" default_implementation="impl1">')
    ldf_data.append('    <Options/>')
    ldf_data.append('    <Implementation title="impl1" dir="impl1" description="impl1" synthesis="lse" default_strategy="Strategy1">')
    ldf_data.append('        <Options def_top="top"/>')
    ldf_data.append('        <Source name="impl1/source/remorafpga.v" type="Verilog" type_short="Verilog">')
    ldf_data.append('            <Options/>')
    ldf_data.append('        </Source>')
    ldf_data.append('        <Source name="impl1/source/pins.lpf" type="Logic Preference" type_short="LPF">')
    ldf_data.append('            <Options/>')
    ldf_data.append('        </Source>')
    ldf_data.append('    </Implementation>')
    ldf_data.append('    <Strategy name="Strategy1" file="pif21.sty"/>')
    ldf_data.append('</BaliProject>')
    ldf_data.append('')
    open(f"{FIRMWARE_PATH}/remorafpga.ldf", "w").write("\n".join(ldf_data))

    # pins.lpf (diamond)
    pcf_data = []
    pcf_data.append('')
    pcf_data.append('BLOCK RESETPATHS;')
    pcf_data.append('BLOCK ASYNCPATHS;')
    pcf_data.append('')
    pcf_data.append('BANK 0 VCCIO 3.3 V;')
    pcf_data.append('BANK 1 VCCIO 3.3 V;')
    pcf_data.append('BANK 2 VCCIO 3.3 V;')
    pcf_data.append('BANK 3 VCCIO 3.3 V;')
    pcf_data.append('BANK 5 VCCIO 3.3 V;')
    pcf_data.append('BANK 6 VCCIO 3.3 V;')
    pcf_data.append('')
    pcf_data.append('TRACEID "00111100" ;')
    pcf_data.append('IOBUF ALLPORTS IO_TYPE=LVCMOS33 ;')
    #pcf_data.append('SYSCONFIG JTAG_PORT=DISABLE  SDM_PORT=PROGRAMN  I2C_PORT=DISABLE  SLAVE_SPI_PORT=ENABLE  MCCLK_FREQ=10.23 ;')
    pcf_data.append('SYSCONFIG JTAG_PORT=ENABLE  SDM_PORT=PROGRAMN  I2C_PORT=DISABLE  SLAVE_SPI_PORT=DISABLE  MCCLK_FREQ=10.23 ;')
    pcf_data.append('USERCODE ASCII  "PIF2"      ;')
    pcf_data.append('')
    pcf_data.append('# LOCATE COMP "FDONE"           SITE "109";')
    pcf_data.append('# LOCATE COMP "FINITn"          SITE "110";')
    pcf_data.append('# LOCATE COMP "FPROGn"          SITE "119";')
    pcf_data.append('# LOCATE COMP "FJTAGn"          SITE "120";')
    pcf_data.append('# LOCATE COMP "FTMS"            SITE "130";')
    pcf_data.append('# LOCATE COMP "FTCK"            SITE "131";')
    pcf_data.append('# LOCATE COMP "FTDI"            SITE "136";')
    pcf_data.append('# LOCATE COMP "FTDO"            SITE "137";')
    pcf_data.append('')
    pcf_data.append('LOCATE COMP "GSRn"              SITE "136";')
    pcf_data.append('LOCATE COMP "LEDR"              SITE "112";')
    pcf_data.append('LOCATE COMP "LEDG"              SITE "113";')
    pcf_data.append('LOCATE COMP "SDA"               SITE "125";')
    pcf_data.append('LOCATE COMP "SCL"               SITE "126";')
    pcf_data.append('IOBUF  PORT "GSRn"              IO_TYPE=LVCMOS33 PULLMODE=UP;')
    pcf_data.append('IOBUF  PORT "LEDR"              IO_TYPE=LVCMOS33 PULLMODE=DOWN;')
    pcf_data.append('IOBUF  PORT "LEDG"              IO_TYPE=LVCMOS33 PULLMODE=DOWN;')
    pcf_data.append('IOBUF  PORT "SCL"               IO_TYPE=LVCMOS33 PULLMODE=UP;')
    pcf_data.append('IOBUF  PORT "SDA"               IO_TYPE=LVCMOS33 PULLMODE=UP;')
    pcf_data.append('')
    for pname, pins in pinlists.items():
        pcf_data.append(f"### {pname} ###")
        for pin in pins:
            pcf_data.append(f'LOCATE COMP "{pin[0]}"           SITE "{pin[1]}";')
        pcf_data.append("")
    pcf_data.append('')
    open(f"{PINS_PATH}/pins.lpf", "w").write("\n".join(pcf_data))




remora_data = []
remora_data.append("#ifndef REMORA_H")
remora_data.append("#define REMORA_H")
remora_data.append("")
remora_data.append(f"#define JOINTS              {joints}")
remora_data.append(f"#define VARIABLE_OUTPUTS    {vouts}")
remora_data.append(f"#define VARIABLE_INPUTS     {vins}")
remora_data.append(f"#define DIGITAL_OUTPUTS     {douts_total}")
remora_data.append(f"#define DIGITAL_INPUTS      {dins_total}")
remora_data.append(f"#define SPIBUFSIZE          {data_size // 8}")
remora_data.append("")
remora_data.append("#define PRU_DATA            0x64617461")
remora_data.append("#define PRU_READ            0x72656164")
remora_data.append("#define PRU_WRITE           0x77726974")
remora_data.append("#define PRU_ESTOP           0x65737470")
remora_data.append("#define STEPBIT             22")
remora_data.append("#define STEP_MASK           (1L<<STEPBIT)")
remora_data.append("#define STEP_OFFSET         (1L<<(STEPBIT-1))")
remora_data.append("#define PRU_BASEFREQ        40000")
remora_data.append("")
remora_data.append("typedef union {")
remora_data.append("    struct {")
remora_data.append("        uint8_t txBuffer[SPIBUFSIZE];")
remora_data.append("    };")
remora_data.append("    struct {")
remora_data.append("        int32_t header;")
remora_data.append("        int32_t jointFreqCmd[JOINTS];")
remora_data.append("        int16_t setPoint[VARIABLES];")
remora_data.append("        uint8_t jointEnable;")
remora_data.append("        uint8_t outputs;")
remora_data.append("    };")
remora_data.append("} txData_t;")
remora_data.append("static txData_t txData;")
remora_data.append("")
remora_data.append("typedef union")
remora_data.append("{")
remora_data.append("    struct {")
remora_data.append("        uint8_t rxBuffer[SPIBUFSIZE];")
remora_data.append("    };")
remora_data.append("    struct {")
remora_data.append("        int32_t header;")
remora_data.append("        int32_t jointFeedback[JOINTS];")
remora_data.append("        int16_t processVariable[VARIABLES];")
remora_data.append("        uint8_t inputs;")
remora_data.append("    };")
remora_data.append("} rxData_t;")
remora_data.append("static rxData_t rxData;")
remora_data.append("")
remora_data.append("#endif")
remora_data.append("")
open(f"{LINUXCNC_PATH}/Components/remora.h", "w").write("\n".join(remora_data))



# verilog
top_data = []
top_data.append("")
top_data.append(f"/*")
top_data.append(f"    ######### {jdata['name']} #########")
top_data.append(f"*/")
top_data.append("")


for plugin in plugins:
    if hasattr(plugins[plugin], "ips"):
        top_data.append(plugins[plugin].ips())


top_data.append("")
argsstr = ",\n        ".join(top_arguments)
top_data.append(f"module top (\n        {argsstr}")
top_data.append("    );")
top_data.append("")
top_data.append("")



if jdata['toolchain'] == "diamond":
    top_data.append("    // Internal Oscillator")
    top_data.append("    defparam OSCH_inst.NOM_FREQ = \"133.00\";")
    top_data.append("    OSCH OSCH_inst ( ")
    top_data.append("        .STDBY(1'b0),")
    top_data.append("        .OSC(sysclk),")
    top_data.append("        .SEDSTDBY()")
    top_data.append("    );")
    top_data.append("")


if 'blink' in jdata:
    top_data.append("    reg led;")
    top_data.append("    reg [31:0] counter;")
    top_data.append("    reg [31:0] ledclk;")
    top_data.append("    assign BLINK_LED = led;")
    top_data.append("")
    top_data.append("    always @(posedge sysclk) begin")
    top_data.append("        if (counter == 0) begin")
    top_data.append("            counter <= 10000000;")
    top_data.append("            ledclk <= ~ledclk;")
    top_data.append("        end else begin")
    top_data.append("            counter <= counter - 1;")
    top_data.append("        end")
    top_data.append("    end")
    top_data.append("")
    top_data.append("    always @(posedge ledclk) begin")
    top_data.append("        led <= ~led;")
    top_data.append("    end")
    top_data.append("")




top_data.append(f"    parameter BUFFER_SIZE = {data_size};")
top_data.append("")

top_data.append(f"    wire[{data_size - 1}:0] rx_data;")
top_data.append(f"    wire[{data_size - 1}:0] tx_data;")
top_data.append("    reg signed [31:0] header_tx = 32'h64617461;")
top_data.append("")

for num in range(joints):
    top_data.append(f"    wire jointEnable{num};")
top_data.append("")


if dins_total > dins:
    top_data.append("    // fake din's to fit byte")
    for num in range(dins_total - dins):
        top_data.append(f"    reg DIN{dins + num} = 0;")
    top_data.append("")

if douts_total > douts:
    top_data.append("    // fake dout's to fit byte")
    for num in range(douts_total - douts):
        top_data.append(f"    reg DOUT{douts + num} = 0;")
    top_data.append("")


top_data.append(f"    // vouts {vouts}")
for num in range(vouts):
    top_data.append(f"    wire [15:0] setPoint{num};")
top_data.append("")
top_data.append(f"    // vins {vins}")
for num in range(vins):
    top_data.append(f"    wire [15:0] processVariable{num};")
top_data.append("")
top_data.append(f"    // joints {joints}")
for num in range(joints):
    top_data.append(f"    wire signed [31:0] jointFreqCmd{num};")

for num in range(joints):
    top_data.append(f"    wire signed [31:0] jointFeedback{num};")
top_data.append("")


top_data.append(f"    // rx_data {rx_data_size}")
pos = data_size

top_data.append(f"    wire [31:0] header_rx;")
top_data.append(f"    assign header_rx = {{rx_data[{pos-3*8-1}:{pos-3*8-8}], rx_data[{pos-2*8-1}:{pos-2*8-8}], rx_data[{pos-1*8-1}:{pos-1*8-8}], rx_data[{pos-1}:{pos-8}]}};")
pos -= 32

for num in range(joints):
    top_data.append(f"    assign jointFreqCmd{num} = {{rx_data[{pos-3*8-1}:{pos-3*8-8}], rx_data[{pos-2*8-1}:{pos-2*8-8}], rx_data[{pos-1*8-1}:{pos-1*8-8}], rx_data[{pos-1}:{pos-8}]}};")
    pos -= 32

for num in range(vouts):
    top_data.append(f"    assign setPoint{num} = {{rx_data[{pos-1*8-1}:{pos-1*8-8}], rx_data[{pos-1}:{pos-8}]}};")
    pos -= 16

for num in range(joints_en_total):
    if num < joints:
        top_data.append(f"    assign jointEnable{num} = rx_data[{pos-1}];")
    else:
        top_data.append(f"    // assign jointEnable{num} = rx_data[{pos-1}];")
    pos -= 1


for num in range((douts_total + 7) // 8 * 8):
    top_data.append(f"    assign DOUT{douts_total - num - 1} = rx_data[{pos-1}];")
    pos -= 1




top_data.append("")
top_data.append(f"    // tx_data {tx_data_size}")
top_data.append("    assign tx_data = {")
top_data.append("        header_tx[7:0], header_tx[15:8], header_tx[23:16], header_tx[31:24],")

for num in range(joints):
    top_data.append(f"        jointFeedback{num}[7:0], jointFeedback{num}[15:8], jointFeedback{num}[23:16], jointFeedback{num}[31:24],")

for num in range(vins):
    top_data.append(f"        processVariable{num}[7:0], processVariable{num}[15:8],")

for num in range(dins_total):
    top_data.append(f"        DIN{dins_total - num - 1},")

fill = (data_size - tx_data_size)
if fill > 0:
    top_data.append(f"        {fill}'d0")
top_data.append("    };")

top_data.append("")



for plugin in plugins:
    if hasattr(plugins[plugin], "funcs"):
        funcs = plugins[plugin].funcs()
        top_data.append("\n".join(funcs))
        top_data.append("")


top_data.append("endmodule")
top_data.append("")


#print("\n".join(top_data))
open(f"{SOURCE_PATH}/remorafpga.v", "w").write("\n".join(top_data))












