
FAMILY  := ice40
TYPE    := hx8k
PACKAGE := ct256

all: remorafpga.bin

remorafpga.json: remorafpga.v
	yosys -p 'synth_${FAMILY} -top top -json remorafpga.json' remorafpga.v

remorafpga.asc: remorafpga.json pins.pcf
	nextpnr-${FAMILY} --${TYPE} --package ${PACKAGE} --json remorafpga.json --pcf pins.pcf --asc remorafpga.asc

remorafpga.bin: remorafpga.asc
	icepack remorafpga.asc remorafpga.bin

