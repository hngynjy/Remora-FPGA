
FAMILY  := ice40
TYPE    := lp8k
PACKAGE := cm81

all: remorafpga.bin

remorafpga.json: freq_counter.v spi_slave.v quad_encoder.v stepgen.v rcservo.v pwm_out.v pwm_counter.v pwm_dir.v pll.v remorafpga.v
	yosys -q -l yosys.log -p 'synth_${FAMILY} -top top -json remorafpga.json' freq_counter.v spi_slave.v quad_encoder.v stepgen.v rcservo.v pwm_out.v pwm_counter.v pwm_dir.v pll.v remorafpga.v

remorafpga.asc: remorafpga.json pins.pcf
	nextpnr-${FAMILY} -q -l nextpnr.log --${TYPE} --package ${PACKAGE} --json remorafpga.json --pcf pins.pcf --asc remorafpga.asc
	@echo ""
	@grep -B 1 "%$$" nextpnr.log
	@echo ""

remorafpga.bin: remorafpga.asc
	icepack remorafpga.asc remorafpga.bin

clean:
	rm -rf remorafpga.bin remorafpga.asc remorafpga.json yosys.log nextpnr.log

tinyprog: remorafpga.bin
	tinyprog -p remorafpga.bin
