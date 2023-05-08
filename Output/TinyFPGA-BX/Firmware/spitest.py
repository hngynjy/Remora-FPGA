
import time
import spidev
from struct import *

bus = 0
device = 1
spi = spidev.SpiDev()
spi.open(bus, device)
spi.max_speed_hz = 4000000
spi.mode = 0
spi.lsbfirst = False

data = [0] * 30
data[0] = 0x74
data[1] = 0x69
data[2] = 0x72
data[3] = 0x77

JOINTS = 5
VOUTS = 2
VINS = 2
DOUTS = 6
DINS = 6

joints = [
    500,
    500,
    500,
    500,
    500,
]

vouts = [
    0xFFFF // 2,
    0xFFFF // 2,
]

FREQ = 48000000

bn = 4
for value in joints:
    if value == 0:
        joint = list(pack('<i', (0)))
    else:
        joint = list(pack('<i', (FREQ // value)))
    for byte in range(4):
        data[bn + byte] = joint[byte]
    bn += 4

for value in vouts:
    vout = list(pack('<H', (value)))
    for byte in range(2):
        data[bn + byte] = vout[byte]
    bn += 2

# jointEnable and dout (TODO: split in bits)
data[bn] = 0xFF
bn += 1

# dout
data[bn] = 0xFF
bn += 1


print(data)
rec = spi.xfer2(data)
print(rec)



jointFeedback = [0] * JOINTS
processVariable = [0] * VOUTS

pos = 0
header = unpack('<i', bytes(rec[pos:pos+4]))[0]
pos += 4
for num in range(JOINTS):
    jointFeedback[num] = unpack('<i', bytes(rec[pos:pos+4]))[0]
    pos += 4
for num in range(VINS):
    processVariable[num] = unpack('<h', bytes(rec[pos:pos+2]))[0]
    pos += 2
inputs = unpack('<B', bytes(rec[pos:pos+1]))[0]
pos += 1

if header == 0x64617461:
    print(f'PRU_DATA: 0x{header:x}')
    for num in range(JOINTS):
        print(f' Joint({num}): {jointFeedback[num]}')
    for num in range(VINS):
        print(f' Var({num}): {processVariable[num]}')
    print(f'inputs {inputs:08b}')
else:
    print(f'Header: 0x{header:x}')


