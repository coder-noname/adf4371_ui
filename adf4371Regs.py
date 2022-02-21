# -*- coding=utf-8 -*-

import os
import subprocess
import time

import serial

def runcmd(cmd):
    subprocess.call(cmd)


class adf4371_regs():

    def find_addr_data(self, addr):
        for a in range(self.reg_len):
            if addr == self.reg_addr_def[a]:
                return self.reg_data_def[a]

    def update_addr_data(self, addr, data):
        for a in range(self.reg_len):
            if addr == self.reg_addr_def[a]:
                self.reg_data_def[a] = data

    def calc_pfd(self, rfin, divby2, r_counter, doubler):
        return rfin * (1 + doubler) / (1 + divby2) / r_counter

    def calc_N(self, INT, FRAC1, FRAC2, MOD1, MOD2):
        return INT + ((FRAC1 + FRAC2 / MOD2) / MOD1)

    def __init__(self):
        self.reg_len = 61
        self.reg_addr_def = [0x00, 0x01, 0x03, 0x04, 0x05, 0x06, 0x10, 0x11, 0x12, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A,
                        0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2A, 0x2B, 0x2C,
                        0x2D, 0x2E, 0x2F, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3D, 0x3E,
                        0x3F, 0x40, 0x41, 0x42, 0x47, 0x52, 0x6E, 0x6F, 0x70, 0x71, 0x72, 0x73, 0x7C]
        self.reg_data_def = [0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x32, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0xE8, 0x03,
                        0x00, 0x00, 0x00, 0x48, 0x01, 0x14, 0x00, 0x00, 0x80, 0x07, 0x32, 0xC5, 0x03, 0x00, 0x01, 0x44,
                        0x11, 0x12, 0x94, 0x3f, 0xa7, 0x04, 0x0c, 0x9e, 0x4C, 0x30, 0x00, 0x00, 0x07, 0x55, 0x00, 0x0C,
                        0x80, 0x50, 0x28, 0x00, 0xC0, 0xF4, 0x00, 0x00, 0x03, 0x60, 0x32, 0x00, 0x00]

        self.SynthLockTimeout = self.find_addr_data(0x33) & 0x1f
        self.Timeout = self.find_addr_data(0x31) | (self.find_addr_data(0x32) & 0x3 << 8)
        self.VCOAclTimeout = self.find_addr_data(0x34) & 0x1f
        self.VCOBandDiv = self.find_addr_data(0x30) & 0xff

        self.BleedCurrent = self.find_addr_data(0x26)
        self.BleedEnable = (self.find_addr_data(0x27) >> 3) & 0x1
        self.BleedPolarity = (self.find_addr_data(0x2a) >> 5) & 0x1
        print("bleed", self.BleedEnable, "-", self.BleedPolarity, "-", self.BleedCurrent)

        self.AutoCalEnable = (self.find_addr_data(0x12) >> 6) & 0x1
        self.ChargePumpCurrent = (self.find_addr_data(0x1e) >> 4) & 0xf
        self.ChargePumpTristate = (self.find_addr_data(0x3e) >> 2) & 0x3
        self.ClkDivTimeout = self.find_addr_data(0x35)
        self.ClockDivider = (self.find_addr_data(0x23) >> 4) & 0x3
        self.CounterReset = self.find_addr_data(0x1e) & 0x1
        self.FeedbackSelect = (self.find_addr_data(0x24) >> 7) & 0x1
        self.FilterMode = (self.find_addr_data(0x23) >> 1) & 0x1
        self.FracInt = (self.find_addr_data(0x2b) >> 0) & 0x1
        self.MuteToLockDetect = (self.find_addr_data(0x25) >> 7) & 0x1
        self.PhaseAdjust = (self.find_addr_data(0x1a) >> 6) & 0x1
        self.PhaseDetectorPolarity = (self.find_addr_data(0x1e) >> 3) & 0x1
        self.PhaseWord = self.find_addr_data(0x1d) << 16 | self.find_addr_data(0x1c) << 8 | self.find_addr_data(0x1b)
        self.Prescaler = (self.find_addr_data(0x12) >> 5) & 0x1
        self.SDLoadEnable = (self.find_addr_data(0x2b) >> 2) & 0x1
        self.SynthPowerDown = (self.find_addr_data(0x1e) >> 2) & 0x1
        self.VariableModulus = (self.find_addr_data(0x2b) >> 4) & 0x1
        print("vm", self.VariableModulus)

        self.MuxEnable = (self.find_addr_data(0x20) >> 3) & 0x1
        self.MuxLevel = (self.find_addr_data(0x20) >> 2) & 0x1
        self.MuxMode = (self.find_addr_data(0x20) >> 4) & 0xf
        print(self.MuxEnable, "-", self.MuxMode, "-", self.MuxLevel)

        self.DivideBy2 = (self.find_addr_data(0x22) >> 4) & 0x1
        self.Doubler = (self.find_addr_data(0x22) >> 5) & 0x1
        self.RDivider = self.find_addr_data(0x1f) & 0x1f
        self.RF = 100.0
        self.RFMode = (self.find_addr_data(0x22) >> 6) & 0x1
        print("pfd", self.DivideBy2, self.Doubler, self.RDivider, self.RF, self.RFMode)

        self.RF16Bias = (self.find_addr_data(0x70) >> 0) & 0x3
        self.RF16Enable = (self.find_addr_data(0x25) >> 3) & 0x1
        self.RF16Filter = (self.find_addr_data(0x70) >> 5) & 0x7
        print("rf16", self.RF16Enable, self.RF16Filter, self.RF16Bias)

        self.RF32Bias = (self.find_addr_data(0x71) >> 0) & 0x3
        self.RF32Enable = (self.find_addr_data(0x25) >> 4) & 0x1
        self.RF32Filter = (self.find_addr_data(0x71) >> 5) & 0x7
        print("rf32", self.RF32Enable, self.RF32Filter, self.RF32Bias)

        self.RF8Enable = (self.find_addr_data(0x25) >> 2) & 0x1
        self.RF8Power = (self.find_addr_data(0x25) >> 0) & 0x3
        print("rf8", self.RF8Enable, self.RF8Power)

        self.RF8AUXEnable = (self.find_addr_data(0x72) >> 3) & 0x1
        self.RF8AUXFreqSel = (self.find_addr_data(0x72) >> 6) & 0x1
        self.RF8AUXPower = (self.find_addr_data(0x72) >> 4) & 0x3
        print("rf8aux", self.RF8AUXEnable, self.RF8AUXFreqSel, self.RF8AUXPower)

        self.Divider = (self.find_addr_data(0x24) >> 4) & 0x7
        self.FRAC1 = self.find_addr_data(0x14) | (self.find_addr_data(0x15) << 8) | (self.find_addr_data(0x16) << 16) | ((self.find_addr_data(0x17) & 0x1) << 24)
        self.FRAC2 = (self.find_addr_data(0x17) >> 1) | (self.find_addr_data(0x18) << 7)
        self.INT = self.find_addr_data(0x10) | (self.find_addr_data(0x11) << 8)
        self.MOD1 = 33554432
        self.MOD2 = self.find_addr_data(0x19) | ((self.find_addr_data(0x1a) & 0x3f) << 8)
        self.N = self.calc_N(self.INT, self.FRAC1, self.FRAC2, self.MOD1, self.MOD2)
        self.PFD = self.calc_pfd(self.RF, self.DivideBy2, self.RDivider, self.Doubler)
        self.VCOFreq = self.PFD * self.N
        self.RF16Freq = self.VCOFreq * 2
        self.RF32Freq = self.VCOFreq * 4
        self.RF8Freq = self.VCOFreq / pow(2, self.Divider)
        print(self.PFD, "-", self.VCOFreq)

    def update_regs(self):
        print("update regs begin begin begin")
#   timeout
        self.update_addr_data(0x30, self.VCOBandDiv & 0xff)
        self.update_addr_data(0x31, self.Timeout & 0xff)
        defdata = self.find_addr_data(0x32)
        defdata |= self.Timeout >> 8 & 0x3
        self.update_addr_data(0x32, defdata)

        self.update_addr_data(0x33, self.SynthLockTimeout & 0x1f)
        self.update_addr_data(0x34, self.VCOAclTimeout & 0x1f)
        print("VCOBandDiv", self.VCOBandDiv)
        print("Timeout", self.Timeout)
        print("SynthLockTimeout", self.SynthLockTimeout)
        print("VCOAclTimeout", self.VCOAclTimeout)

#   bleed
        defdata = self.find_addr_data(0x26)
        defdata = self.BleedCurrent
        self.update_addr_data(0x26, defdata)

        defdata = self.find_addr_data(0x27)
        defdata |= self.BleedEnable << 3
        self.update_addr_data(0x27, defdata)

        defdata = self.find_addr_data(0x2a)
        defdata |= self.BleedPolarity << 5
        self.update_addr_data(0x2a, defdata)

        print("BleedEnable", self.BleedEnable)
        print("BleedCurrent", self.BleedCurrent)
        print("BleedPolarity", self.BleedPolarity)
#   features
        defdata = self.find_addr_data(0x3e)
        defdata |= self.ChargePumpTristate << 2
        self.update_addr_data(0x3e, defdata)

        self.update_addr_data(0x35, self.ClkDivTimeout)

        defdata = self.find_addr_data(0x24)
        defdata |= self.FeedbackSelect << 7
        self.update_addr_data(0x24, defdata)

        defdata = self.find_addr_data(0x25)
        defdata |= self.MuteToLockDetect << 7
        self.update_addr_data(0x25, defdata)

        self.update_addr_data(0x1d, (self.PhaseWord >> 16) & 0xff)
        self.update_addr_data(0x1c, (self.PhaseWord >> 8) & 0xff)
        self.update_addr_data(0x1b, self.PhaseWord & 0xff)

        defdata = self.find_addr_data(0x1a)
        defdata |= self.PhaseAdjust << 6
        self.update_addr_data(0x1a, defdata)

        defdata = self.find_addr_data(0x23)
        defdata |= self.ClockDivider << 4
        defdata |= self.FilterMode << 1
        self.update_addr_data(0x23, defdata)

        defdata = self.find_addr_data(0x12)
        defdata |= self.AutoCalEnable << 6
        defdata |= self.Prescaler << 5
        self.update_addr_data(0x12, defdata)

        defdata = self.find_addr_data(0x1e)
        defdata |= self.ChargePumpCurrent << 4
        defdata |= self.CounterReset & 0x1
        defdata |= self.PhaseDetectorPolarity << 3
        defdata |= self.SynthPowerDown << 2
        self.update_addr_data(0x1e, defdata)

        defdata = self.find_addr_data(0x2b)
        defdata |= self.FracInt & 0x1
        defdata |= self.SDLoadEnable << 2
        defdata |= self.VariableModulus << 4
        self.update_addr_data(0x2b, defdata)
#   MUXOUT
        defdata = self.find_addr_data(0x20)
        defdata |= self.MuxEnable << 3
        defdata |= self.MuxLevel << 2
        defdata |= self.MuxMode << 4
        self.update_addr_data(0x20, defdata)
        print("MuxEnable", self.MuxEnable)
        print("MuxLevel", self.MuxLevel)
        print("MuxMode", self.MuxMode)
#   pfd
        defdata = self.find_addr_data(0x22)
        defdata |= self.DivideBy2 << 4
        defdata |= self.Doubler << 5
        defdata |= self.RFMode << 6
        self.update_addr_data(0x22, defdata)

        defdata = self.find_addr_data(0x1f)
        defdata = self.RDivider
        self.update_addr_data(0x1f, defdata)
        print("DivideBy2", self.DivideBy2)
        print("Doubler", self.Doubler)
        print("RFMode", self.RFMode)
        print("RDivider", self.RDivider)
        print("RF", self.RF)

#   RF 8 aux 16 32
        defdata = self.find_addr_data(0x25)
        defdata |= self.RF16Enable << 3
        defdata |= self.RF32Enable << 4
        defdata |= self.RF8Enable << 2
        defdata |= self.RF8Power
        self.update_addr_data(0x25, defdata)

        defdata = self.find_addr_data(0x70)
        defdata |= self.RF16Bias
        defdata |= self.RF16Filter << 5
        self.update_addr_data(0x70, defdata)

        defdata = self.find_addr_data(0x71)
        defdata |= self.RF32Bias
        defdata |= self.RF32Filter << 5
        self.update_addr_data(0x71, defdata)

        defdata = self.find_addr_data(0x72)
        defdata |= self.RF8AUXEnable << 3
        defdata |= self.RF8AUXFreqSel << 6
        defdata |= self.RF8AUXPower << 4
        self.update_addr_data(0x72, defdata)
#   VCO
        defdata = self.find_addr_data(0x24)
        defdata |= self.Divider << 4
        self.update_addr_data(0x24, defdata)

        self.update_addr_data(0x10, self.INT & 0xff)
        self.update_addr_data(0x11, (self.INT >> 8) & 0xff)

        self.update_addr_data(0x14, self.FRAC1 & 0xff)
        self.update_addr_data(0x15, (self.FRAC1 >> 8) & 0xff)
        self.update_addr_data(0x16, (self.FRAC1 >> 16) & 0xff)
        defdata = self.find_addr_data(0x17)
        defdata |= (self.FRAC1 >> 24) & 0x1
        defdata |= (self.FRAC2 & 0x7f) << 1
        self.update_addr_data(0x17, defdata)
        self.update_addr_data(0x18, self.FRAC2 >> 7)

        self.update_addr_data(0x19, self.MOD2 & 0xff)
        defdata = self.find_addr_data(0x1a)
        defdata |= (self.MOD2 >> 8) & 0x3f
        self.update_addr_data(0x1a, defdata)