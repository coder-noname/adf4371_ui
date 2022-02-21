#-*- coding : utf-8-*-
# coding:unicode_escape
import json
import os.path
import subprocess
import sys
import math
import time

import serial
import serial.tools.list_ports

from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QMessageBox
from adf4371_7 import Ui_adf4371
from PyQt5 import QtCore, QtGui, QtWidgets
from adf4371Regs import adf4371_regs

class App(QMainWindow, Ui_adf4371):
    adf4371 = adf4371_regs()

    def __init__(self):
        super(App, self).__init__()
        self.setupUi(self)
        self.rFinModeComboBox.currentIndexChanged.connect(self.slot_rf8aux_power)
        self.writeReg.clicked.connect(self.slot_write_clicked)
        self.refresh.clicked.connect(self.slot_update_com)
        self.phaseAdjustComboBox_2.currentIndexChanged.connect(self.slot_phase_adjust)
        self.vCOLineEdit.textChanged.connect(self.slot_VCOFreq_changed)
        self.lockStatus.clicked.connect(self.slot_get_lock_detect_status)
        self.enableLineEdit_bleed.currentIndexChanged.connect(self.slot_bleed_enable_changed)
        self.update_ui_values()
        self.powerComboBox.currentIndexChanged.connect(self.debug_ui)

    def debug_ui(self):
        print("index ", self.powerComboBox.count(), self.powerComboBox.currentIndex())

    def slot_bleed_enable_changed(self):
        if self.enableLineEdit_bleed.currentText() == "Enable":
            self.currentLineEdit.setEnabled(True)
        else:
            self.currentLineEdit.setEnabled(False)

    def slot_get_lock_detect_status(self):
        print(self.sPIMasterComboBox.currentText())
        err, data = self.get_reg(self.sPIMasterComboBox.currentText(), "0x007c")
        if err == 0:
            self.checkLockLineEdit_2.setText(str(data))
        else:
            self.log.setText("get lock status failed")

    def gcd(m, n):
        while m != n:
            if m > n:
                m = m - n
            else:
                n = n - m
        return m

    def slot_VCOFreq_changed(self):
        vco = float(self.vCOLineEdit.text())
        if vco <= 8000 and vco >= 4000:
            # update PFD here
            D = self.doublerComboBox.currentIndex()
            T = self.divideBy2ComboBox.currentIndex()
            R = int(self.rDividerLineEdit.text())
            pfd_local = (float(self.rFInputLineEdit.text()) * (1 + D) / (R * (1 + T)))
            print(pfd_local)
            self.pFDFreqLineEdit_PFD.setText(str(pfd_local))

            # update vco
            N = float(self.vCOLineEdit.text()) / pfd_local
            self.nLineEdit.setText(str(N))

            INT = int(N)
            self.iNTLineEdit.setText(str(INT))
            frac = N - INT;
            mod1 = 33554432
            self.mOD1LineEdit.setText(str(mod1))
            frac1 = int(mod1 * frac)
            self.fRAC1LineEdit.setText(str(frac1))
            print(math.gcd(int(pfd_local) * 1000, 100))
            mod2 = pfd_local * 1000 / math.gcd(int(pfd_local) * 1000, 100)
            self.mOD2LineEdit.setText(str(mod2))

            if mod2 < 2:
                mod2 = 2;
            if mod2 > 16383:
                mod2 = 16383;

            frac2 = ((frac * mod1) - frac1) * mod2;
            self.fRAC2LineEdit.setText(str(frac2))

            vco = float(self.vCOLineEdit.text())
            vco_divider = int(self.outputDividerComboBox.currentText())
            print(vco)
            print(vco_divider)
            rf8freq = vco / vco_divider
            self.pFDFreqLineEditRF8.setText(str(rf8freq))
            self.rF16FreqLineEdit.setText(str(vco * 2))
            self.rF32FreqLineEdit.setText((str(vco * 4)))

            r16freq = float(self.vCOLineEdit.text()) * 2
            if r16freq < 8400.0:
                self.biasLineEdit.setText(str(3))
                self.filterLineEdit.setText(str(7))
            elif r16freq >= 8400.0 and r16freq < 9400.0:
                self.biasLineEdit.setText(str(3))
                self.filterLineEdit.setText(str(6))
            elif r16freq >= 9400.0 and r16freq < 10000.0:
                self.biasLineEdit.setText(str(3))
                self.filterLineEdit.setText(str(5))
            elif r16freq >= 10000.0 and r16freq < 11500.0:
                self.biasLineEdit.setText(str(3))
                self.filterLineEdit.setText(str(4))
            elif r16freq >= 11500.0 and r16freq < 12200.0:
                self.biasLineEdit.setText(str(3))
                self.filterLineEdit.setText(str(3))
            elif r16freq >= 12200.0 and r16freq < 13700.0:
                self.biasLineEdit.setText(str(3))
                self.filterLineEdit.setText(str(2))
            elif r16freq >= 13700.0 and r16freq < 14500.0:
                self.biasLineEdit.setText(str(3))
                self.filterLineEdit.setText(str(1))
            else:
                self.biasLineEdit.setText(str(3))
                self.filterLineEdit.setText(str(0))

            r32freq = float(self.vCOLineEdit.text()) * 4
            if r32freq < 18000.0:
                self.biasLineEdit_rf32.setText(str(3))
                self.filterLineEdit_rf32.setText(str(7))
            elif r32freq >= 18000.0 and r32freq < 19000.0:
                self.biasLineEdit_rf32.setText(str(3))
                self.filterLineEdit_rf32.setText(str(3))
            elif r32freq >= 19000.0 and r32freq < 20500.0:
                self.biasLineEdit_rf32.setText(str(0))
                self.filterLineEdit_rf32.setText(str(1))
            elif r32freq >= 20500.0 and r32freq < 26000.0:
                self.biasLineEdit_rf32.setText(str(0))
                self.filterLineEdit_rf32.setText(str(0))
            else:
                self.biasLineEdit_rf32.setText(str(1))
                self.filterLineEdit_rf32.setText(str(0))

    def slot_phase_adjust(self):
        if self.phaseAdjustComboBox_2.currentText() == "Enable":
            self.phaseWordLineEdit_2.setEnabled(True)
        else:
            self.phaseWordLineEdit_2.setDisabled(True)

    def update_ui_values(self):
        # PFD Frequency Area
        self.rFInputLineEdit.setText(str(self.adf4371.RF))
        self.rFinModeComboBox.setCurrentIndex(self.adf4371.RFMode)
        self.doublerComboBox.setCurrentIndex(self.adf4371.Doubler)
        self.rDividerLineEdit.setText(str(self.adf4371.RDivider))
        self.divideBy2ComboBox.setCurrentIndex(self.adf4371.DivideBy2)

        # VCO Area
        self.vCOLineEdit.setText(str(self.adf4371.VCOFreq))
        self.outputDividerComboBox.setCurrentIndex(self.adf4371.Divider)
        self.pFDFreqLineEditRF8.setText(str(self.adf4371.RF8Freq))
        self.rF16FreqLineEdit.setText(str(self.adf4371.RF16Freq))
        self.rF32FreqLineEdit.setText(str(self.adf4371.RF32Freq))
        self.pFDFreqLineEdit_PFD.setText(str(self.adf4371.PFD))
        self.nLineEdit.setText(str(self.adf4371.N))
        self.iNTLineEdit.setText(str(self.adf4371.INT))
        self.fRAC1LineEdit.setText(str(self.adf4371.FRAC1))
        self.fRAC2LineEdit.setText(str(self.adf4371.FRAC2))
        self.mOD1LineEdit.setText(str(self.adf4371.MOD1))
        self.mOD2LineEdit.setText(str(self.adf4371.MOD2))

        # Features
        self.chargePumpCurrentComboBox.setCurrentIndex(self.adf4371.ChargePumpCurrent)
        self.phaseDetectorPolarityComboBox.setCurrentIndex(self.adf4371.PhaseDetectorPolarity)
        self.counterResetComboBox.setCurrentIndex(self.adf4371.CounterReset)
        self.muteTilLockDetectComboBox.setCurrentIndex(self.adf4371.MuteToLockDetect)
        self.synthPowerdownComboBox.setCurrentIndex(self.adf4371.SynthPowerDown)
        if self.adf4371.ChargePumpTristate == 0:
            self.chargePumpTriStateComboBox.setCurrentIndex(0)
        else:
            self.chargePumpTriStateComboBox.setCurrentIndex(1)
        self.prescalerComboBox.setCurrentIndex(self.adf4371.Prescaler)
        self.feedbackSelectComboBox.setCurrentIndex(self.adf4371.FeedbackSelect)
        self.SDLoadCombo.setCurrentIndex(self.adf4371.SDLoadEnable)
        self.variableModulusComboBox.setCurrentIndex(self.adf4371.VariableModulus)
        self.fracIntOperationComboBox.setCurrentIndex(self.adf4371.FracInt)

        self.phaseAdjustComboBox_2.setCurrentIndex(self.adf4371.PhaseAdjust)
        if self.adf4371.PhaseAdjust == "Disable":
            self.phaseWordLineEdit_2.setDisabled(True)
        self.phaseWordLineEdit_2.setText(str(self.adf4371.PhaseWord))
        self.autoCalEnableComboBox.setCurrentIndex(self.adf4371.AutoCalEnable)
        self.clockDividerComboBox_2.setCurrentIndex(self.adf4371.ClockDivider)
        self.clkDivTimeoutUsLineEdit.setText(str(self.adf4371.ClkDivTimeout))
        self.filterModeComboBox.setCurrentIndex(self.adf4371.FilterMode)

        # RF8
        self.rF8EnableComboBox.setCurrentIndex(self.adf4371.RF8Enable)
        self.rF8outPowerComboBox.setCurrentIndex(self.adf4371.RF8Power)

        # AUXRF8
        self.powerComboBox.addItem("")
        self.powerComboBox.addItem("")
        self.powerComboBox.addItem("")
        self.powerComboBox.addItem("")

        if self.rFinModeComboBox.currentText() == "Single":
            self.powerComboBox.setItemText(0, "-4.5dBm")
            self.powerComboBox.setItemText(1, "1dBm")
            self.powerComboBox.setItemText(2, "4dBm")
            self.powerComboBox.setItemText(3, "6dBm")
        else:
            self.powerComboBox.setItemText(0, "-1.5dBm")
            self.powerComboBox.setItemText(1, "4dBm")
            self.powerComboBox.setItemText(2, "7dBm")
            self.powerComboBox.setItemText(3, "9dBm")
        self.enableComboBox_rf8aux.setCurrentIndex(self.adf4371.RF8AUXEnable)
        self.powerComboBox.setCurrentIndex(self.adf4371.RF8AUXPower)
        self.freqSelComboBox.setCurrentIndex(self.adf4371.RF8AUXFreqSel)

        # RF16
        self.enableComboBox_rf16.setCurrentIndex(self.adf4371.RF16Enable)
        self.biasLineEdit.setEnabled(False)
        self.biasLineEdit.setText(str(self.adf4371.RF16Bias))
        self.filterLineEdit.setEnabled(False)
        self.filterLineEdit.setText(str(self.adf4371.RF16Filter))

        # RF32
        self.enableComboBox_rf32.setCurrentIndex(self.adf4371.RF32Enable)
        self.biasLineEdit_rf32.setEnabled(False)
        self.biasLineEdit_rf32.setText(str(self.adf4371.RF32Bias))
        self.filterLineEdit_rf32.setEnabled(False)
        self.filterLineEdit_rf32.setText(str(self.adf4371.RF32Filter))

        # ACL Timeout
        self.vCOBandDivLineEdit.setText(str(self.adf4371.VCOBandDiv))
        self.timeoutLineEdit.setText(str(self.adf4371.Timeout))
        self.vCOACLTimeoutLineEdit.setText(str(self.adf4371.VCOAclTimeout))
        self.synthLockTimeoutLineEdit.setText(str(self.adf4371.SynthLockTimeout))

        # Muxout
        self.modeComboBox.setCurrentIndex(self.adf4371.MuxMode)
        self.enableComboBox.setCurrentIndex(self.adf4371.MuxEnable)
        self.muxoutLevelComboBox.setCurrentIndex(self.adf4371.MuxLevel)

        # bleed
        self.enableLineEdit_bleed.setCurrentIndex(self.adf4371.BleedEnable)
        if self.adf4371.BleedEnable == "Enable":
            self.currentLineEdit.setEnabled(True)
        else:
            self.currentLineEdit.setDisabled(True)
        self.currentLineEdit.setText(str(self.adf4371.BleedCurrent))
        self.polarityComboBox.setCurrentIndex(self.adf4371.BleedPolarity)

    def slot_update_com(self):
        self.uartcombox.clear()
        portList = list(serial.tools.list_ports.comports())
        portListName = []
        if len(portList) > 0:
            for eachPort in portList:
                portListName.append(eachPort[0])
        print(portListName)
        self.uartcombox.addItems(portListName)

    def slot_rf8aux_power(self):
        if self.rFinModeComboBox.currentText() == "Single":
            self.powerComboBox.setItemText(0, "-4.5dBm")
            self.powerComboBox.setItemText(1, "1dBm")
            self.powerComboBox.setItemText(2, "4dBm")
            self.powerComboBox.setItemText(3, "6dBm")
        else:
            self.powerComboBox.setItemText(0, "-1.5dBm")
            self.powerComboBox.setItemText(1, "4dBm")
            self.powerComboBox.setItemText(2, "7dBm")
            self.powerComboBox.setItemText(3, "9dBm")

    def reset_chip(self):
        uartIndexStr = self.uartcombox.currentText()
        uartIndexList = uartIndexStr.split("COM")
        cmdoff = "gpio.exe" + " -c " + " -g C -p 0 " + " -u " + uartIndexList[1]
        cmdon = "gpio.exe" + " -s " + " -g C -p 0 " + " -u " + uartIndexList[1]
        if os.path.exists("gpio.exe"):
            os.system(cmdoff)
            time.sleep(1)
            os.system(cmdon)
        else:
            self.log.setText("no spi.exe exist")

    def slot_write_clicked(self):
        print("000000000000")
        # Step0 reset 芯片
        self.reset_chip()

        print("1111111111111")
        # Step1 修改寄存器变量的值
        input_str = self.rFInputLineEdit.text()
        if float(input_str) < 0 or float(input_str) > 600:
            msg_box = QMessageBox(QMessageBox.Warning, '警告', 'RF is [0, 600]')
            msg_box.exec_()
            return
        self.adf4371.RF = float(input_str)

        self.adf4371.RFMode = self.rFinModeComboBox.currentIndex()
        self.adf4371.Doubler = self.doublerComboBox.currentIndex()

        input_str = self.rDividerLineEdit.text()
        print("fsldjflds", input_str)
        if int(input_str, base=10) < 0 or int(input_str, base=10) >= 32:
            msg_box = QMessageBox(QMessageBox.Warning, '警告', 'RDivider is [0, 31]')
            msg_box.exec_()
            return
        self.adf4371.RDivider = int(input_str)
        self.adf4371.DivideBy2 = self.divideBy2ComboBox.currentIndex()

        input_str = self.vCOLineEdit.text()
        if float(input_str) < 4000 or float(input_str) > 8000:
            msg_box = QMessageBox(QMessageBox.Warning, '警告', 'VCOFreq is [4000, 8000]')
            msg_box.exec_()
            return
        self.adf4371.VCOFreq = float(input_str)
        self.adf4371.Divider = self.outputDividerComboBox.currentIndex()
        self.adf4371.RF8Freq = float(self.pFDFreqLineEditRF8.text())
        self.adf4371.RF16Freq = float(self.rF16FreqLineEdit.text())
        self.adf4371.RF32Freq = float(self.rF32FreqLineEdit.text())
        self.adf4371.PFD = float(self.pFDFreqLineEdit_PFD.text())
        self.adf4371.N = float(self.nLineEdit.text())
        self.adf4371.INT = int(self.iNTLineEdit.text())
        self.adf4371.FRAC1 = int(self.fRAC1LineEdit.text())
        self.adf4371.FRAC2 = int(self.fRAC2LineEdit.text())
        self.adf4371.MOD1 = int(self.mOD1LineEdit.text())
        self.adf4371.MOD2 = int(self.mOD2LineEdit.text())

        self.adf4371.ChargePumpCurrent = self.chargePumpCurrentComboBox.currentIndex()
        self.adf4371.PhaseDetectorPolarity = self.phaseDetectorPolarityComboBox.currentIndex()
        self.adf4371.CounterReset = self.counterResetComboBox.currentIndex()
        self.adf4371.MuteToLockDetect = self.muteTilLockDetectComboBox.currentIndex()
        self.adf4371.SynthPowerDown = self.synthPowerdownComboBox.currentIndex()
        self.adf4371.ChargePumpTristate = self.chargePumpTriStateComboBox.currentIndex()
        self.adf4371.Prescaler = self.prescalerComboBox.currentIndex()
        self.adf4371.FeedbackSelect = self.feedbackSelectComboBox.currentIndex()
        self.adf4371.SDLoadEnable = self.SDLoadCombo.currentIndex()
        self.adf4371.VariableModulus = self.variableModulusComboBox.currentIndex()
        self.adf4371.FracInt = self.fracIntOperationComboBox.currentIndex()

        self.adf4371.PhaseAdjust = self.phaseAdjustComboBox_2.currentIndex()
        if self.phaseAdjustComboBox_2.currentText() == "Enable":
            input_str = self.phaseWordLineEdit_2.text()
            if int(input_str, base=10) < 0 or int(input_str, base=10) >= math.pow(2, 24):
                msg_box = QMessageBox(QMessageBox.Warning, '警告', 'PhaseWord is [0, 16777216]')
                msg_box.exec_()
                return
            else:
                self.adf4371.PhaseWord = int(input_str)
        else:
            self.adf4371.PhaseWord = 0

        self.adf4371.AutoCalEnable = self.autoCalEnableComboBox.currentIndex()
        self.adf4371.ClkDivTimeout = int(self.clkDivTimeoutUsLineEdit.text())
        self.adf4371.FilterMode = self.filterModeComboBox.currentIndex()

        self.adf4371.RF8Enable = self.rF8EnableComboBox.currentIndex()
        self.adf4371.RF8Power = self.rF8outPowerComboBox.currentIndex()

        self.adf4371.RF8AUXEnable = self.enableComboBox_rf8aux.currentIndex()
        self.adf4371.RF8AUXPower = self.powerComboBox.currentIndex()

        if self.freqSelComboBox.currentText() == "VCO":
            self.adf4371.RF8AUXFreqSel = 1
        else:
            self.adf4371.RF8AUXFreqSel = 0

        self.adf4371.RF16Enable = self.enableComboBox_rf16.currentIndex()
        self.adf4371.RF16Bias = int(self.biasLineEdit.text())
        self.adf4371.RF16Filter = int(self.filterLineEdit.text())

        self.adf4371.RF32Enable = self.enableComboBox_rf32.currentIndex()
        self.adf4371.RF32Bias = int(self.biasLineEdit_rf32.text())
        self.adf4371.RF32Filter = int(self.filterLineEdit_rf32.text())

        input_str = self.vCOBandDivLineEdit.text()
        if int(input_str) < 1 or int(input_str) > 255:
            msg_box = QMessageBox(QMessageBox.Warning, '警告', 'VCOBandDiv is [1, 255]')
            msg_box.exec_()
            return
        self.adf4371.VCOBandDiv = int(input_str)

        input_str = self.timeoutLineEdit.text()
        if int(input_str) < 0 or int(input_str) >= math.pow(2, 10):
            msg_box = QMessageBox(QMessageBox.Warning, '警告', 'Timeout is [1, 1024]')
            msg_box.exec_()
            return
        self.adf4371.Timeout = int(input_str)

        input_str = self.vCOACLTimeoutLineEdit.text()
        if int(input_str) < 2 or int(input_str) >= 64:
            msg_box = QMessageBox(QMessageBox.Warning, '警告', 'VCOAclTimeout is [1, 64]')
            msg_box.exec_()
            return
        self.adf4371.VCOAclTimeout = int(input_str)

        input_str = self.synthLockTimeoutLineEdit.text()
        if int(input_str) < 0 or int(input_str) >= 32:
            msg_box = QMessageBox(QMessageBox.Warning, '警告', 'SynthLockTimeout is [1, 32]')
            msg_box.exec_()
            return
        self.adf4371.SynthLockTimeout = int(input_str)

#        input_str = self.approxXTimeLineEdit.text()

#        self.adf4371._reg["adf4371"]["ACL_Timeout"]["TotalCalTime"] = self.approxXTimeLineEdit.text()
#        self.adf4371_reg["adf4371"]["ACL_Timeout"]["DieTemp"] = self.tempLineEdit_2.text()
#        self.adf4371_reg["adf4371"]["ACL_Timeout"]["LockStatus"] = self.checkLockLineEdit_2.text()

        self.adf4371.BleedEnable = self.enableLineEdit_bleed.currentIndex()
        if self.enableLineEdit_bleed.currentText() == "Enable":
            input_str = self.currentLineEdit.text()
            if int(input_str) < 0 or int(input_str) >= 256:
                msg_box = QMessageBox(QMessageBox.Warning, '警告', 'Bleed Current is [1, 32]')
                msg_box.exec_()
                return
        self.adf4371.BleedCurrent = int(input_str)
        self.adf4371.BleedPolarity = self.polarityComboBox.currentIndex()

        self.adf4371.MuxMode = self.modeComboBox.currentIndex()
        self.adf4371.MuxEnable = self.enableComboBox.currentIndex()
        self.adf4371.MuxLevel = self.muxoutLevelComboBox.currentIndex()

        print("2222222222222")
        # Step2 更新寄存器表
        self.adf4371.update_regs()

        print("3333333333333")
        # Step3 将寄存器表保存成特殊文件
        f = open("adf437x.txt", "w")
        for i in range(self.adf4371.reg_len):
            wstr = hex(self.adf4371.reg_addr_def[i]) + "\t" + hex(self.adf4371.reg_data_def[i]) + '''\tRegMap1\n'''
            f.write(wstr)
        f.close()

        print("444444444444444")
        # Step4 检查串口
        if not self.uartcombox.currentText():
            msg_box = QMessageBox(QMessageBox.Warning, '警告', 'Please Insert UART and Press Refresh')
            msg_box.exec_()
            return

        print("55555555555555")
        # Step5 调用spi.exe程序将adf437x.txt写入芯片
        uartIndexStr = self.uartcombox.currentText()
        uartIndexList = uartIndexStr.split("COM")
        cmd = "spi.exe" + \
              " -m " + self.sPIMasterComboBox.currentText() + \
              " -c 1" + \
              " -f adf437x.txt" + \
              " -u " + uartIndexList[1]
        print(cmd)
        if os.path.exists("spi.exe"):
            os.system(cmd)
        else:
            self.log.setText("no spi.exe exist")
        print("Set Done")

if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    ui = App()
    ui.show()
    sys.exit(app.exec_())
