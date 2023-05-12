

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



    spitest_data.append("""

class WinForm(QWidget):
    def __init__(self,parent=None):
        super(WinForm, self).__init__(parent)
        self.setWindowTitle('SPI-Test')
        self.listFile=QListWidget()
        layout=QGridLayout()
        self.widgets = {}
        
        gpy = 2
        for jn in range(JOINTS):
            key = f'jcs{jn}'
            self.widgets[key] = QSlider(Qt.Horizontal)
            self.widgets[key].setMinimum(-jointcalcs[jn][1])
            self.widgets[key].setMaximum(jointcalcs[jn][1])
            self.widgets[key].setValue(0)
            layout.addWidget(self.widgets[key], gpy, jn + 1)
        gpy += 1
        for jn in range(JOINTS):
            key = f'jcraw{jn}'
            self.widgets[key] = QLabel(f'cmd: {jn}')
            layout.addWidget(self.widgets[key], gpy, jn + 1)
        gpy += 1
        for jn in range(JOINTS):
            key = f'jc{jn}'
            self.widgets[key] = QLabel(f'cmd: {jn}')
            layout.addWidget(self.widgets[key], gpy, jn + 1)
        gpy += 1

        for vn in range(VOUTS):
            key = f'vos{vn}'
            self.widgets[key] = QSlider(Qt.Horizontal)
            self.widgets[key].setMinimum(0)
            self.widgets[key].setMaximum(65535)
            self.widgets[key].setValue(0)
            layout.addWidget(self.widgets[key], gpy, vn + 1)
        gpy += 1
        for vn in range(VOUTS):
            key = f'vo{vn}'
            self.widgets[key] = QLabel(f'vo: {vn}')
            layout.addWidget(self.widgets[key], gpy, vn + 1)
        gpy += 1

        for dn in range(DOUTS):
            key = f'doc{dn}'
            self.widgets[key] = QCheckBox()
            self.widgets[key].setChecked(False)
            layout.addWidget(self.widgets[key], gpy, dn + 1)
        gpy += 1

        for jn in range(JOINTS):
            key = f'jf{jn}'
            self.widgets[key] = QLabel(f'joint: {jn}')
            layout.addWidget(self.widgets[key], gpy, jn + 1)
        gpy += 1

        for vn in range(VINS):
            key = f'vi{vn}'
            self.widgets[key] = QLabel(f'vin: {vn}')
            layout.addWidget(self.widgets[key], gpy, vn + 1)
        gpy += 1

        for dn in range(8):
            key = f'dic{dn}'
            self.widgets[key] = QLabel("0")
            layout.addWidget(self.widgets[key], gpy, dn + 1)
        gpy += 1

        self.setLayout(layout)

        self.timer=QTimer()
        self.timer.timeout.connect(self.runTimer)
        self.timer.start(500)

    def runTimer(self):

        data = [0] * 30
        data[0] = 0x74
        data[1] = 0x69
        data[2] = 0x72
        data[3] = 0x77

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

        douts = 0
        for dn in range(DOUTS):
            key = f"doc{dn}"
            if self.widgets[key].isChecked():
                douts |= (1<<dn)


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

        for value in vouts:
            vout = list(pack('<H', (value)))
            for byte in range(2):
                data[bn + byte] = vout[byte]
            bn += 2


        # jointEnable and dout (TODO: split in bits)
        data[bn] = 0xFF
        bn += 1

        # dout
        data[bn] = douts
        bn += 1


        print("tx:", data)
        rec = spi.xfer2(data)
        print("rx:", rec)



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
                print(f' Joint({num}): {jointFeedback[num]} // 1')
            for num in range(VINS):
                print(f' Var({num}): {processVariable[num]}')
            print(f'inputs {inputs:08b}')
        else:
            print(f'Header: 0x{header:x}')



        for jn, value in enumerate(joints):
            key = f"jf{jn}"
            self.widgets[key].setText(str(jointFeedback[jn]))


        for vn in range(VINS):
            key = f"vi{vn}"
            self.widgets[key].setText(str(processVariable[vn]))


        for dn in range(8):
            key = f"dic{dn}"

            value = "0"
            if inputs & (1<<dn) != 0:
                value = "1"

            self.widgets[key].setText(value)



if __name__ == '__main__':
    app=QApplication(sys.argv)
    form=WinForm()
    form.show()
    sys.exit(app.exec_())


    """)

    open(f"{project['FIRMWARE_PATH']}/qt_spitest.py", "w").write("\n".join(spitest_data))



