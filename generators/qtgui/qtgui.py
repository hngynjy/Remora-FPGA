

def generate(project):
    print("generating qtgui")

    spitest_data = []
    spitest_data.append("")
    spitest_data.append("import time")
    spitest_data.append("import spidev")
    spitest_data.append("from struct import *")
    spitest_data.append("import sys")
    spitest_data.append("from PyQt5.QtWidgets import QWidget,QPushButton,QApplication,QListWidget,QGridLayout,QLabel,QSlider,QCheckBox")
    spitest_data.append("from PyQt5.QtCore import QTimer,QDateTime, Qt")
    spitest_data.append("")
    spitest_data.append("INTERVAL = 100")
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
        spitest_data.append("    0,")
    spitest_data.append("]")
    spitest_data.append("")

    spitest_data.append(f"jointcalcs = {project['jointcalcs']}")
    spitest_data.append("")

    spitest_data.append("vouts = [")
    for _num in range(project['vouts']):
        spitest_data.append("    0,")
    spitest_data.append("]")
    spitest_data.append("")

    spitest_data.append("douts = [")
    for _num in range(project['douts']):
        spitest_data.append("    0,")
    spitest_data.append("]")
    spitest_data.append("")

    spitest_data.append(f"PRU_OSC = {project['jdata']['clock']['speed']}")
    spitest_data.append("")

    spitest_data.append("voutminmax = [")
    for num, vout in enumerate(project['jdata']["vout"]):
        if vout.get('type') == "sine":
            spitest_data.append(f"    ({vout.get('min', 0)}, {vout.get('max', 100000)}, 'raw', 30),")
        else:
            spitest_data.append(f"    ({vout.get('min', 0)}, {vout.get('max', 10)}, 'scale', 1),")
    spitest_data.append("]")
    spitest_data.append("")

    spitest_data.append(f"JOINT_ENABLE_BYTES = {project['joints_en_total'] // 8}")
    spitest_data.append(f"DIGITAL_OUTPUT_BYTES = {project['douts_total'] // 8}")
    spitest_data.append(f"DIGITAL_INPUT_BYTES = {project['dins_total'] // 8}")
    spitest_data.append("")
    
    spitest_data.append("""

class WinForm(QWidget):
    def __init__(self,parent=None):
        super(WinForm, self).__init__(parent)
        self.setWindowTitle('SPI-Test')
        self.listFile=QListWidget()
        layout=QGridLayout()
        self.widgets = {}
        self.animation = 0

        COLS = max(JOINTS, DOUTS, VOUTS, DINS, VINS)

        gpy = 0
        for jn in range(COLS):
            label = QLabel(f'       {jn}     ')
            layout.addWidget(label, gpy, jn + 3)
        gpy += 1

        layout.addWidget(QLabel(f'JOINTS:'), gpy, 0)
        layout.addWidget(QLabel(f'OUT'), gpy, 1)
        for jn in range(JOINTS):
            key = f'jcs{jn}'
            self.widgets[key] = QSlider(Qt.Horizontal)
            self.widgets[key].setMinimum(-jointcalcs[jn][1])
            self.widgets[key].setMaximum(jointcalcs[jn][1])
            self.widgets[key].setValue(0)
            layout.addWidget(self.widgets[key], gpy, jn + 3)
        gpy += 1
        for jn in range(JOINTS):
            key = f'jcraw{jn}'
            self.widgets[key] = QLabel(f'cmd: {jn}')
            layout.addWidget(self.widgets[key], gpy, jn + 3)
        gpy += 1
        for jn in range(JOINTS):
            key = f'jc{jn}'
            self.widgets[key] = QLabel(f'cmd: {jn}')
            layout.addWidget(self.widgets[key], gpy, jn + 3)
        gpy += 1

        layout.addWidget(QLabel(f'VARIABLE:'), gpy, 0)
        layout.addWidget(QLabel(f'OUT'), gpy, 1)
        for vn in range(VOUTS):
            key = f'vos{vn}'
            self.widgets[key] = QSlider(Qt.Horizontal)
            self.widgets[key].setMinimum(voutminmax[vn][0])
            self.widgets[key].setMaximum(voutminmax[vn][1])
            self.widgets[key].setValue(0)
            layout.addWidget(self.widgets[key], gpy, vn + 3)
        gpy += 1

        for vn in range(VOUTS):
            key = f'vo{vn}'
            self.widgets[key] = QLabel(f'vo: {vn}')
            layout.addWidget(self.widgets[key], gpy, vn + 3)
        gpy += 1

        layout.addWidget(QLabel(f'DIGITAL:'), gpy, 0)
        layout.addWidget(QLabel(f'OUT'), gpy, 1)
        self.widgets["dout_auto"] = QCheckBox()
        layout.addWidget(self.widgets["dout_auto"], gpy, 2)
        for dbyte in range(DIGITAL_INPUT_BYTES):
            for dn in range(8):
                key = f'doc{dbyte}{dn}'
                self.widgets[key] = QCheckBox()
                self.widgets[key].setChecked(False)
                layout.addWidget(self.widgets[key], gpy, dbyte * 8 + dn + 3)
        gpy += 1

        layout.addWidget(QLabel(f'JOINTS:'), gpy, 0)
        layout.addWidget(QLabel(f'IN'), gpy, 1)
        for jn in range(JOINTS):
            key = f'jf{jn}'
            self.widgets[key] = QLabel(f'joint: {jn}')
            layout.addWidget(self.widgets[key], gpy, jn + 3)
        gpy += 1

        layout.addWidget(QLabel(f'VARIABLE:'), gpy, 0)
        layout.addWidget(QLabel(f'IN'), gpy, 1)
        for vn in range(VINS):
            key = f'vi{vn}'
            self.widgets[key] = QLabel(f'vin: {vn}')
            layout.addWidget(self.widgets[key], gpy, vn + 3)
        gpy += 1

        layout.addWidget(QLabel(f'DIGITAL:'), gpy, 0)
        layout.addWidget(QLabel(f'IN'), gpy, 1)
        for dbyte in range(DIGITAL_INPUT_BYTES):
            for dn in range(8):
                key = f'dic{dbyte}{dn}'
                self.widgets[key] = QLabel("0")
                layout.addWidget(self.widgets[key], gpy, dbyte * 8 + dn + 3)
        gpy += 1

        self.setLayout(layout)

        self.timer=QTimer()
        self.timer.timeout.connect(self.runTimer)
        self.timer.start(INTERVAL)

    def runTimer(self):

        #data = [0] * {project['data_size'] // 8}
        data[0] = 0x74
        data[1] = 0x69
        data[2] = 0x72
        data[3] = 0x77

        try:

            for jn in range(JOINTS):
                key = f"jcs{jn}"
                joints[jn] = int(self.widgets[key].value())

                key = f"jcraw{jn}"
                self.widgets[key].setText(str(joints[jn]))

            for vn in range(VOUTS):
                key = f"vos{vn}"
                vouts[vn] = int(self.widgets[key].value())
                key = f"vo{vn}"
                self.widgets[key].setText(str(vouts[vn]))

            if self.widgets["dout_auto"].isChecked():
                timer = int(time.time() * 50)
                for dbyte in range(DIGITAL_OUTPUT_BYTES):
                    for dn in range(8):
                        key = f"doc{dbyte}{dn}"

                        #stat = (timer & (dn+1) == 0)
                        stat = ((self.animation // 50) == dbyte * 8 + dn)
                        self.animation += 1
                        if self.animation // 50 > DOUTS:
                            self.animation = 0

                        self.widgets[key].setChecked(stat)

            douts = []
            for dbyte in range(DIGITAL_OUTPUT_BYTES):
                douts.append(0)
                for dn in range(8):
                    key = f"doc{dbyte}{dn}"
                    if self.widgets[key].isChecked():
                        douts[dbyte] |= (1<<(dn))


            bn = 4
            for jn, value in enumerate(joints):
                # precalc
                if value == 0:
                    value = 0
                elif jointcalcs[jn][0] == "oscdiv":
                    value = int(PRU_OSC / value)

                key = f"jc{jn}"
                self.widgets[key].setText(str(value))

                joint = list(pack('<i', value))
                for byte in range(4):
                    data[bn + byte] = joint[byte]
                bn += 4

            for vn, value in enumerate(vouts):
                if voutminmax[vn][2] == 'raw':
                    if value > 0:
                        value = int(PRU_OSC / value / voutminmax[vn][3])
                    else:
                        value = 0
                else:
                    value = int((value - voutminmax[vn][0]) * 0xFFFFFFFF / (voutminmax[vn][1] - voutminmax[vn][0]))

                print(vn, value)

                vout = list(pack('<I', (value)))
                for byte in range(4):
                    data[bn + byte] = vout[byte]
                bn += 4


            # jointEnable and dout (TODO: split in bits)
            for dbyte in range(JOINT_ENABLE_BYTES):
                data[bn] = 0xFF
                bn += 1

            # dout
            for dbyte in range(DIGITAL_OUTPUT_BYTES):
                data[bn] = douts[dbyte]
                bn += 1


            print("tx:", data)
            rec = spi.xfer2(data)
            print("rx:", rec)



            jointFeedback = [0] * JOINTS
            processVariable = [0] * VINS

            pos = 0
            header = unpack('<i', bytes(rec[pos:pos+4]))[0]
            pos += 4

            for num in range(JOINTS):
                jointFeedback[num] = unpack('<i', bytes(rec[pos:pos+4]))[0]
                pos += 4

            for num in range(VINS):
                processVariable[num] = unpack('<i', bytes(rec[pos:pos+4]))[0]
                pos += 4

            inputs = []
            for dbyte in range(DIGITAL_INPUT_BYTES):
                inputs.append(unpack('<B', bytes(rec[pos:pos+1]))[0])
                pos += 1

            if header == 0x64617461:
                print(f'PRU_DATA: 0x{header:x}')
                for num in range(JOINTS):
                    print(f' Joint({num}): {jointFeedback[num]} // 1')
                for num in range(VINS):
                    print(f' Var({num}): {processVariable[num]}')
                #print(f'inputs {inputs:08b}')
            else:
                print(f'Header: 0x{header:x}')



            for jn, value in enumerate(joints):
                key = f"jf{jn}"
                self.widgets[key].setText(str(jointFeedback[jn]))


            for vn in range(VINS):
                key = f"vi{vn}"
                self.widgets[key].setText(str(processVariable[vn]))


            for dbyte in range(DIGITAL_INPUT_BYTES):
                for dn in range(8):
                    key = f"dic{dbyte}{dn}"

                    value = "0"
                    if inputs[dbyte] & (1<<dn) != 0:
                        value = "1"

                    self.widgets[key].setText(value)
                    if value == "0":
                        self.widgets[key].setStyleSheet("background-color: lightgreen")
                    else:
                        self.widgets[key].setStyleSheet("background-color: yellow")


        except Exception as e:
            print("ERROR", e)


if __name__ == '__main__':
    app=QApplication(sys.argv)
    form=WinForm()
    form.show()
    sys.exit(app.exec_())


    """)

    open(f"{project['FIRMWARE_PATH']}/qt_spitest.py", "w").write("\n".join(spitest_data))



