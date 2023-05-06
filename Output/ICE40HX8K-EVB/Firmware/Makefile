
FAMILY  := ice40
TYPE    := hx8k
PACKAGE := ct256

all: remorafpga.bin

remorafpga.json: remorafpga.v
	yosys -q -l yosys.log -p 'synth_${FAMILY} -top top -json remorafpga.json' remorafpga.v

remorafpga.asc: remorafpga.json pins.pcf
	nextpnr-${FAMILY} -q -l nextpnr.log --${TYPE} --package ${PACKAGE} --json remorafpga.json --pcf pins.pcf --asc remorafpga.asc
	@echo ""
	@grep -B 1 "%$$" nextpnr.log
	@echo ""

remorafpga.bin: remorafpga.asc
	icepack remorafpga.asc remorafpga.bin

clean:
	rm -rf remorafpga.bin remorafpga.asc remorafpga.json yosys.log nextpnr.log
