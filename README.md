# Remora-FPGA
port of Remora to FPGA's using Verilog

* no soft IP Cores
* logic only
* no jitter
* fast and small
* generated verilog-code / setup via json files (free pin-selection)


only for research / untested on real machines

the Bugblat PIF_2 (machxo2) will not work - warning chip gets hot !


## Structure:

buildtool.py plugins:  this are python scripts to generates the verilog files from a configuration

configs: here are the config files for a specific setup (Target-FPGA / Pins)

Output: the generated files per config


## the exciting part:

https://github.com/multigcs/Remora-FPGA/blob/main/Output/ICE40HX8K-EVB/Firmware/remorafpga.v


## Demo-Video on TinyFPGA-BX board:

https://www.youtube.com/shorts/0nTmo4afwWs


## TinyFPGA-BX board with 5axis BOB:

![test](https://raw.githubusercontent.com/multigcs/Remora-FPGA/main/files/4x.jpg)


## Original-Project:

 https://github.com/scottalford75/Remora
