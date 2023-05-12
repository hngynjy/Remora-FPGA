

def generate(project):
    print("generating spitest")

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
    spitest_data.append(f"spi.max_speed_hz = {project['jdata']['interface'].get('max', 5000000)}")
    spitest_data.append("spi.mode = 0")
    spitest_data.append("spi.lsbfirst = False")
    spitest_data.append("")
    spitest_data.append(f"data = [0] * {project['data_size'] // 8}")

    spitest_data.append("data[0] = 0x74")
    spitest_data.append("data[1] = 0x69")
    spitest_data.append("data[2] = 0x72")
    spitest_data.append("data[3] = 0x77")


    spitest_data.append("")
    spitest_data.append(f"JOINTS = {project['joints']}")
    spitest_data.append(f"VOUTS = {project['vouts']}")
    spitest_data.append(f"VINS = {project['vins']}")
    spitest_data.append(f"DOUTS = {project['douts']}")
    spitest_data.append(f"DINS = {project['douts']}")
    spitest_data.append("")


    spitest_data.append("joints = [")
    for _num in range(project['joints']):
        spitest_data.append("    500,")
    spitest_data.append("]")
    spitest_data.append("")
    spitest_data.append("vouts = [")
    for _num in range(project['vouts']):
        spitest_data.append("    0xFFFF // 2,")
    spitest_data.append("]")
    spitest_data.append("")


    spitest_data.append(f"FREQ = {project['jdata']['clock']['speed']}")
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

    enc_scale = 1
    for num, joint in enumerate(project['jdata']["joints"]):
        if joint["type"] == "stepper":
            if joint.get("cl", False):
                enc_scale = joint.get("enc_scale", 1)
    spitest_data.append(f"        print(f' Joint({{num}}): {{jointFeedback[num]}} // {enc_scale}')")


    spitest_data.append("    for num in range(VINS):")
    spitest_data.append("        print(f' Var({num}): {processVariable[num]}')")
    spitest_data.append("    print(f'inputs {inputs:08b}')")
    spitest_data.append("else:")
    spitest_data.append("    print(f'Header: 0x{header:x}')")
    spitest_data.append("")


    spitest_data.append("")
    spitest_data.append("")


    open(f"{project['FIRMWARE_PATH']}/spitest.py", "w").write("\n".join(spitest_data))



