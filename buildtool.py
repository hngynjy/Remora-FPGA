import glob
import importlib
import json
import os
import sys

data = open(sys.argv[1], "r").read()
jdata = json.loads(data)

# loading plugins
plugins = {}
for path in glob.glob("plugins/*"):
    plugin = path.split("/")[1]
    vplugin = importlib.import_module(f".{plugin}", f"plugins.{plugin}")
    plugins[plugin] = vplugin.Plugin(jdata)


verilog_files = []
pinlists = {}

osc_clock = False
if jdata["toolchain"] == "icestorm":
    osc_clock = jdata["clock"].get("osc")
    if osc_clock:
        pinlists["main"] = (("sysclk_in", jdata["clock"]["pin"], "INPUT"),)
    else:
        pinlists["main"] = (("sysclk", jdata["clock"]["pin"], "INPUT"),)


if "blink" in jdata:
    pinlists["blink"] = (("BLINK_LED", jdata["blink"]["pin"], "OUTPUT"),)

if "error" in jdata:
    pinlists["error"] = (("ERROR_OUT", jdata["error"]["pin"], "OUTPUT"),)

for plugin in plugins:
    if hasattr(plugins[plugin], "pinlist"):
        pinlists[plugin] = plugins[plugin].pinlist()

top_arguments = []
for _pname, pins in pinlists.items():
    for pin in pins:
        top_arguments.append(f"{pin[2].lower()} {pin[0]}")

if "enable" in jdata:
    top_arguments.append(f"output ENA")
    pinlists["enable"] = (("ENA", jdata["enable"]["pin"], "OUTPUT"),)

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
OUTPUT_PATH = f"Output/{jdata['name'].replace(' ', '_').replace('/', '_')}"

print(f"generating files in {OUTPUT_PATH}")

FIRMWARE_PATH = f"{OUTPUT_PATH}/Firmware"
SOURCE_PATH = f"{FIRMWARE_PATH}"
PINS_PATH = f"{FIRMWARE_PATH}"
LINUXCNC_PATH = f"{OUTPUT_PATH}/LinuxCNC"
os.system(f"mkdir -p {OUTPUT_PATH}")
os.system(f"mkdir -p {SOURCE_PATH}")
os.system(f"mkdir -p {PINS_PATH}")
os.system(f"mkdir -p {LINUXCNC_PATH}")

os.system(f"mkdir -p {LINUXCNC_PATH}/Components/")
os.system(f"cp -a files/LinuxCNC/Components/* {LINUXCNC_PATH}/Components/")
os.system(f"mkdir -p {LINUXCNC_PATH}/ConfigSamples/")
os.system(f"cp -a files/LinuxCNC/ConfigSamples/* {LINUXCNC_PATH}/ConfigSamples/")

if jdata["toolchain"] == "diamond":
    SOURCE_PATH = f"{FIRMWARE_PATH}/impl1/source"
    PINS_PATH = f"{FIRMWARE_PATH}/impl1/source"
    os.system(f"mkdir -p {SOURCE_PATH}")
    os.system(f"mkdir -p {PINS_PATH}")


remora_data = []
remora_data.append("#ifndef REMORA_H")
remora_data.append("#define REMORA_H")
remora_data.append("")
remora_data.append(f"#define JOINTS              {joints}")
remora_data.append(f"#define VARIABLE_OUTPUTS    {vouts}")
remora_data.append(f"#define VARIABLE_INPUTS     {vins}")
remora_data.append(f"#define VARIABLES           {max(vins, vouts)}")
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
remora_data.append("#define PRU_BASEFREQ        PRU_BASEFREQ")
remora_data.append("")
remora_data.append("typedef union {")
remora_data.append("    struct {")
remora_data.append("        uint8_t txBuffer[SPIBUFSIZE];")
remora_data.append("    };")
remora_data.append("    struct {")
remora_data.append("        int32_t header;")
remora_data.append("        int32_t jointFreqCmd[JOINTS];")
remora_data.append("        int16_t setPoint[VARIABLE_OUTPUTS];")
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
remora_data.append("        int16_t processVariable[VARIABLE_INPUTS];")
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
top_data.append("/*")
top_data.append(f"    ######### {jdata['name']} #########")
top_data.append("*/")
top_data.append("")


for plugin in plugins:
    if hasattr(plugins[plugin], "ips"):
        for ipv in plugins[plugin].ips():
            verilog_files.append(ipv)
            os.system(f"cp -a plugins/{plugin}/{ipv}* {SOURCE_PATH}/{ipv}")


if osc_clock:
    os.system(
        f"icepll -q -m -f '{SOURCE_PATH}/pll.v' -i {float(osc_clock) / 1000000} -o {float(jdata['clock']['speed']) / 1000000}"
    )
    verilog_files.append("pll.v")


top_data.append("")
argsstr = ",\n        ".join(top_arguments)
top_data.append(f"module top (\n        {argsstr}")
top_data.append("    );")
top_data.append("")
top_data.append("")

top_data.append("    wire ERROR = 0;")
top_data.append("    wire INTERFACE_TIMEOUT;")

if osc_clock:
    top_data.append("    wire sysclk;")
    top_data.append("    wire locked;")
    top_data.append("    pll mypll(sysclk_in, sysclk, locked);")
    top_data.append("")


if jdata["toolchain"] == "diamond":
    top_data.append("    // Internal Oscillator")
    top_data.append('    defparam OSCH_inst.NOM_FREQ = "133.00";')
    top_data.append("    OSCH OSCH_inst ( ")
    top_data.append("        .STDBY(1'b0),")
    top_data.append("        .OSC(sysclk),")
    top_data.append("        .SEDSTDBY()")
    top_data.append("    );")
    top_data.append("")


if "blink" in jdata:
    top_data.append("    blink blink1 (")
    top_data.append("        .clk (sysclk),")
    top_data.append(f"        .speed ({int(jdata['clock']['speed']) // 1 // 2}),")
    top_data.append("        .led (BLINK_LED)")
    top_data.append("    );")
    top_data.append("")
    verilog_files.append("blink.v")
    os.system(f"cp -a files/blink.v* {SOURCE_PATH}/blink.v")


if "error" in jdata:
    top_data.append("    assign ERROR_OUT = ERROR;")
    top_data.append("")


top_data.append(f"    parameter BUFFER_SIZE = {data_size};")
top_data.append("")

top_data.append(f"    wire[{data_size - 1}:0] rx_data;")
top_data.append(f"    wire[{data_size - 1}:0] tx_data;")
top_data.append("")

top_data.append("    reg signed [31:0] header_tx;")
top_data.append("    always @(posedge sysclk) begin")
top_data.append("        if (ERROR) begin")
top_data.append("            header_tx = 32'h00000000;")
top_data.append("        end else begin")
top_data.append("            header_tx = 32'h64617461;")
top_data.append("        end")
top_data.append("    end")
top_data.append("")

jointEnables = []
for num in range(joints):
    top_data.append(f"    wire jointEnable{num};")
    jointEnables.append(f"jointEnable{num}")
top_data.append("")

if "enable" in jdata:
    jointEnablesStr = " || ".join(jointEnables)
    top_data.append(f"    assign ENA = ({jointEnablesStr}) && ~ERROR;")
    top_data.append("")


if dins_total > dins:
    top_data.append("    // fake din's to fit byte")
    for num in range(dins_total - dins):
        top_data.append(f"    reg DIN{dins + num} = 0;")
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

top_data.append("    wire [31:0] header_rx;")
top_data.append(
    f"    assign header_rx = {{rx_data[{pos-3*8-1}:{pos-3*8-8}], rx_data[{pos-2*8-1}:{pos-2*8-8}], rx_data[{pos-1*8-1}:{pos-1*8-8}], rx_data[{pos-1}:{pos-8}]}};"
)
pos -= 32

for num in range(joints):
    top_data.append(
        f"    assign jointFreqCmd{num} = {{rx_data[{pos-3*8-1}:{pos-3*8-8}], rx_data[{pos-2*8-1}:{pos-2*8-8}], rx_data[{pos-1*8-1}:{pos-1*8-8}], rx_data[{pos-1}:{pos-8}]}};"
    )
    pos -= 32

for num in range(vouts):
    top_data.append(
        f"    assign setPoint{num} = {{rx_data[{pos-1*8-1}:{pos-1*8-8}], rx_data[{pos-1}:{pos-8}]}};"
    )
    pos -= 16

for num in range(joints_en_total):
    if num < joints:
        top_data.append(f"    assign jointEnable{num} = rx_data[{pos-1}];")
    else:
        top_data.append(f"    // assign jointEnable{num} = rx_data[{pos-1}];")
    pos -= 1


for num in range((douts_total + 7) // 8 * 8):
    if douts_total - num - 1 < douts:
        top_data.append(f"    assign DOUT{douts_total - num - 1} = rx_data[{pos-1}];")
    else:
        top_data.append(
            f"    // assign DOUT{douts_total - num - 1} = rx_data[{pos-1}];"
        )
    pos -= 1


top_data.append("")
top_data.append(f"    // tx_data {tx_data_size}")
top_data.append("    assign tx_data = {")
top_data.append(
    "        header_tx[7:0], header_tx[15:8], header_tx[23:16], header_tx[31:24],"
)

for num in range(joints):
    top_data.append(
        f"        jointFeedback{num}[7:0], jointFeedback{num}[15:8], jointFeedback{num}[23:16], jointFeedback{num}[31:24],"
    )

for num in range(vins):
    top_data.append(f"        processVariable{num}[7:0], processVariable{num}[15:8],")

for num in range(dins_total):
    top_data.append(f"        DIN{dins_total - num - 1},")

fill = data_size - tx_data_size
if fill > 0:
    top_data.append(f"        {fill}'d0")
top_data.append("    };")

top_data.append("")


for plugin in plugins:
    if hasattr(plugins[plugin], "funcs"):
        funcs = plugins[plugin].funcs()
        top_data.append("\n".join(funcs))
        top_data.append("")


top_data.append("    // checking interface timeouts ")
top_data.append("    assign INTERFACE_TIMEOUT = (timeout_counter > 100000);")
top_data.append("    reg [31:0] timeout_counter = 0;")
top_data.append("    wire pkg_ok_risingedge = (pkg_ok==1);")
top_data.append("    always @(posedge sysclk) begin")
top_data.append("        if (pkg_ok_risingedge) begin")
top_data.append("            timeout_counter <= 0;")
top_data.append("        end else if (!INTERFACE_TIMEOUT) begin")
top_data.append("            timeout_counter <= timeout_counter + 1;")
top_data.append("        end")
top_data.append("    end")
top_data.append("")
top_data.append("    assign ERROR = INTERFACE_TIMEOUT;")
top_data.append("")

top_data.append("endmodule")
top_data.append("")


# print("\n".join(top_data))
open(f"{SOURCE_PATH}/remorafpga.v", "w").write("\n".join(top_data))
verilog_files.append("remorafpga.v")


if jdata["toolchain"] == "icestorm" and jdata["family"] == "ecp5":

    lpf_data = []
    lpf_data.append("")

    lpf_data.append("")
    for pname, pins in pinlists.items():
        lpf_data.append(f"### {pname} ###")
        for pin in pins:
            lpf_data.append(f'LOCATE COMP "{pin[0]}"           SITE "{pin[1]}";')
            lpf_data.append(f'IOBUF PORT "{pin[0]}" IO_TYPE=LVCMOS33;')

        lpf_data.append("")
    lpf_data.append("")
    open(f"{PINS_PATH}/pins.lpf", "w").write("\n".join(lpf_data))

    verilogs = " ".join(verilog_files)
    makefile_data = []
    makefile_data.append("")
    makefile_data.append(f"FAMILY  := {jdata['family']}")
    makefile_data.append(f"TYPE    := {jdata['type']}")
    makefile_data.append(f"PACKAGE := {jdata['package']}")
    makefile_data.append("")

    makefile_data.append("")
    makefile_data.append("all: remorafpga.bit")
    makefile_data.append("")
    makefile_data.append(f"remorafpga.json: {verilogs}")
    makefile_data.append(
        f"	yosys -q -l yosys.log -p 'synth_${{FAMILY}} -top top -json remorafpga.json' {verilogs}"
    )
    makefile_data.append("")
    makefile_data.append("remorafpga.config: remorafpga.json pins.lpf")
    makefile_data.append(
        "	nextpnr-${FAMILY} -q -l nextpnr.log --${TYPE} --package ${PACKAGE} --json remorafpga.json --lpf pins.lpf --textcfg remorafpga.config"
    )
    makefile_data.append('	@echo ""')
    makefile_data.append('	@grep -B 1 "%$$" nextpnr.log')
    makefile_data.append('	@echo ""')
    makefile_data.append("")
    makefile_data.append("remorafpga.bit: remorafpga.config")
    makefile_data.append(
        "	ecppack --svf remorafpga.svf remorafpga.config remorafpga.bit"
    )
    makefile_data.append("	")
    makefile_data.append("remorafpga.svf: remorafpga.bit")
    makefile_data.append("")
    makefile_data.append("clean:")
    makefile_data.append(
        "	rm -rf remorafpga.bit remorafpga.svf remorafpga.config remorafpga.json yosys.log nextpnr.log"
    )
    makefile_data.append("")
    makefile_data.append("tinyprog: remorafpga.bin")
    makefile_data.append("	tinyprog -p remorafpga.bin")
    makefile_data.append("")
    open(f"{FIRMWARE_PATH}/Makefile", "w").write("\n".join(makefile_data))


elif jdata["toolchain"] == "icestorm":
    # pins.pcf (icestorm)
    pcf_data = []
    for pname, pins in pinlists.items():
        pcf_data.append(f"### {pname} ###")
        for pin in pins:
            pcf_data.append(f"set_io {pin[0]} {pin[1]}")
        pcf_data.append("")
    open(f"{PINS_PATH}/pins.pcf", "w").write("\n".join(pcf_data))

    verilogs = " ".join(verilog_files)
    makefile_data = []
    makefile_data.append("")
    makefile_data.append(f"FAMILY  := {jdata['family']}")
    makefile_data.append(f"TYPE    := {jdata['type']}")
    makefile_data.append(f"PACKAGE := {jdata['package']}")
    makefile_data.append("")
    makefile_data.append("all: remorafpga.bin")
    makefile_data.append("")
    makefile_data.append(f"remorafpga.json: {verilogs}")
    makefile_data.append(
        f"	yosys -q -l yosys.log -p 'synth_${{FAMILY}} -top top -json remorafpga.json' {verilogs}"
    )
    makefile_data.append("")
    makefile_data.append("remorafpga.asc: remorafpga.json pins.pcf")
    makefile_data.append(
        "	nextpnr-${FAMILY} -q -l nextpnr.log --${TYPE} --package ${PACKAGE} --json remorafpga.json --pcf pins.pcf --asc remorafpga.asc"
    )
    makefile_data.append('	@echo ""')
    makefile_data.append('	@grep -B 1 "%$$" nextpnr.log')
    makefile_data.append('	@echo ""')
    makefile_data.append("")
    makefile_data.append("remorafpga.bin: remorafpga.asc")
    makefile_data.append("	icepack remorafpga.asc remorafpga.bin")
    makefile_data.append("")
    makefile_data.append("clean:")
    makefile_data.append(
        "	rm -rf remorafpga.bin remorafpga.asc remorafpga.json yosys.log nextpnr.log"
    )
    makefile_data.append("")
    makefile_data.append("tinyprog: remorafpga.bin")
    makefile_data.append("	tinyprog -p remorafpga.bin")
    makefile_data.append("")
    open(f"{FIRMWARE_PATH}/Makefile", "w").write("\n".join(makefile_data))


elif jdata["toolchain"] == "diamond":
    os.system(f"cp files/pif21.sty {FIRMWARE_PATH}/")

    ldf_data = []
    ldf_data.append('<?xml version="1.0" encoding="UTF-8"?>')
    ldf_data.append(
        f'<BaliProject version="3.2" title="remorafpga" device="{jdata["type"]}" default_implementation="impl1">'
    )
    ldf_data.append("    <Options/>")
    ldf_data.append(
        '    <Implementation title="impl1" dir="impl1" description="impl1" synthesis="lse" default_strategy="Strategy1">'
    )
    ldf_data.append('        <Options def_top="top"/>')
    for vfile in verilog_files:
        ldf_data.append(
            f'        <Source name="impl1/source/{vfile}" type="Verilog" type_short="Verilog">'
        )
        ldf_data.append("            <Options/>")
        ldf_data.append("        </Source>")
    ldf_data.append(
        '        <Source name="impl1/source/pins.lpf" type="Logic Preference" type_short="LPF">'
    )
    ldf_data.append("            <Options/>")
    ldf_data.append("        </Source>")
    ldf_data.append("    </Implementation>")
    ldf_data.append('    <Strategy name="Strategy1" file="pif21.sty"/>')
    ldf_data.append("</BaliProject>")
    ldf_data.append("")
    open(f"{FIRMWARE_PATH}/remorafpga.ldf", "w").write("\n".join(ldf_data))

    # pins.lpf (diamond)
    pcf_data = []
    pcf_data.append("")
    pcf_data.append("BLOCK RESETPATHS;")
    pcf_data.append("BLOCK ASYNCPATHS;")
    pcf_data.append("")
    pcf_data.append("BANK 0 VCCIO 3.3 V;")
    pcf_data.append("BANK 1 VCCIO 3.3 V;")
    pcf_data.append("BANK 2 VCCIO 3.3 V;")
    pcf_data.append("BANK 3 VCCIO 3.3 V;")
    pcf_data.append("BANK 5 VCCIO 3.3 V;")
    pcf_data.append("BANK 6 VCCIO 3.3 V;")
    pcf_data.append("")
    pcf_data.append('TRACEID "00111100" ;')
    pcf_data.append("IOBUF ALLPORTS IO_TYPE=LVCMOS33 ;")
    # pcf_data.append('SYSCONFIG JTAG_PORT=DISABLE  SDM_PORT=PROGRAMN  I2C_PORT=DISABLE  SLAVE_SPI_PORT=ENABLE  MCCLK_FREQ=10.23 ;')
    pcf_data.append(
        "SYSCONFIG JTAG_PORT=ENABLE  SDM_PORT=PROGRAMN  I2C_PORT=DISABLE  SLAVE_SPI_PORT=DISABLE  MCCLK_FREQ=10.23 ;"
    )
    pcf_data.append('USERCODE ASCII  "PIF2"      ;')
    pcf_data.append("")
    pcf_data.append('# LOCATE COMP "FDONE"           SITE "109";')
    pcf_data.append('# LOCATE COMP "FINITn"          SITE "110";')
    pcf_data.append('# LOCATE COMP "FPROGn"          SITE "119";')
    pcf_data.append('# LOCATE COMP "FJTAGn"          SITE "120";')
    pcf_data.append('# LOCATE COMP "FTMS"            SITE "130";')
    pcf_data.append('# LOCATE COMP "FTCK"            SITE "131";')
    pcf_data.append('# LOCATE COMP "FTDI"            SITE "136";')
    pcf_data.append('# LOCATE COMP "FTDO"            SITE "137";')
    pcf_data.append("")
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
    pcf_data.append("")
    for pname, pins in pinlists.items():
        pcf_data.append(f"### {pname} ###")
        for pin in pins:
            pcf_data.append(f'LOCATE COMP "{pin[0]}"           SITE "{pin[1]}";')
        pcf_data.append("")
    pcf_data.append("")
    open(f"{PINS_PATH}/pins.lpf", "w").write("\n".join(pcf_data))


spitest_data = []
spitest_data.append("")
spitest_data.append("import time")
spitest_data.append("import spidev")
spitest_data.append("from struct import *")
spitest_data.append("")
spitest_data.append("bus = 0")
spitest_data.append("device = 1")
spitest_data.append("spi = spidev.SpiDev()")
spitest_data.append("spi.open(bus, device)")
spitest_data.append(f"spi.max_speed_hz = {jdata['interface'].get('max', 5000000)}")
spitest_data.append("spi.mode = 0")
spitest_data.append("spi.lsbfirst = False")
spitest_data.append("")
spitest_data.append(f"data = [0] * {data_size // 8}")

spitest_data.append("data[0] = 0x74")
spitest_data.append("data[1] = 0x69")
spitest_data.append("data[2] = 0x72")
spitest_data.append("data[3] = 0x77")


spitest_data.append("")
spitest_data.append(f"JOINTS = {joints}")
spitest_data.append(f"VOUTS = {vouts}")
spitest_data.append(f"VINS = {vins}")
spitest_data.append(f"DOUTS = {douts}")
spitest_data.append(f"DINS = {douts}")
spitest_data.append("")


spitest_data.append("joints = [")
for _num in range(joints):
    spitest_data.append("    500,")
spitest_data.append("]")
spitest_data.append("")
spitest_data.append("vouts = [")
for _num in range(vouts):
    spitest_data.append("    0xFFFF // 2,")
spitest_data.append("]")
spitest_data.append("")


spitest_data.append(f"FREQ = {jdata['clock']['speed']}")
spitest_data.append("")
spitest_data.append("bn = 4")
spitest_data.append("for value in joints:")
spitest_data.append("    if value == 0:")
spitest_data.append("        joint = list(pack('<i', (0)))")
spitest_data.append("    else:")
spitest_data.append("        joint = list(pack('<i', (FREQ // value)))")
spitest_data.append("    for byte in range(4):")
spitest_data.append("        data[bn + byte] = joint[byte]")
spitest_data.append("    bn += 4")
spitest_data.append("")
spitest_data.append("for value in vouts:")
spitest_data.append("    vout = list(pack('<H', (value)))")
spitest_data.append("    for byte in range(2):")
spitest_data.append("        data[bn + byte] = vout[byte]")
spitest_data.append("    bn += 2")
spitest_data.append("")
spitest_data.append("# jointEnable and dout (TODO: split in bits)")
spitest_data.append("data[bn] = 0xFF")
spitest_data.append("bn += 1")
spitest_data.append("")
spitest_data.append("# dout")
spitest_data.append("data[bn] = 0xFF")
spitest_data.append("bn += 1")
spitest_data.append("")

spitest_data.append("")
spitest_data.append("print(data)")
spitest_data.append("rec = spi.xfer2(data)")
spitest_data.append("print(rec)")
spitest_data.append("")
spitest_data.append("")
spitest_data.append("")


spitest_data.append("jointFeedback = [0] * JOINTS")
spitest_data.append("processVariable = [0] * VOUTS")
spitest_data.append("")
spitest_data.append("pos = 0")
spitest_data.append("header = unpack('<i', bytes(rec[pos:pos+4]))[0]")
spitest_data.append("pos += 4")
spitest_data.append("for num in range(JOINTS):")
spitest_data.append("    jointFeedback[num] = unpack('<i', bytes(rec[pos:pos+4]))[0]")
spitest_data.append("    pos += 4")
spitest_data.append("for num in range(VINS):")
spitest_data.append("    processVariable[num] = unpack('<h', bytes(rec[pos:pos+2]))[0]")
spitest_data.append("    pos += 2")
spitest_data.append("inputs = unpack('<B', bytes(rec[pos:pos+1]))[0]")
spitest_data.append("pos += 1")
spitest_data.append("")


spitest_data.append("if header == 0x64617461:")
spitest_data.append("    print(f'PRU_DATA: 0x{header:x}')")
spitest_data.append("    for num in range(JOINTS):")
spitest_data.append("        print(f' Joint({num}): {jointFeedback[num]}')")
spitest_data.append("    for num in range(VINS):")
spitest_data.append("        print(f' Var({num}): {processVariable[num]}')")
spitest_data.append("    print(f'inputs {inputs:08b}')")
spitest_data.append("else:")
spitest_data.append("    print(f'Header: 0x{header:x}')")
spitest_data.append("")


spitest_data.append("")
spitest_data.append("")


open(f"{FIRMWARE_PATH}/spitest.py", "w").write("\n".join(spitest_data))
