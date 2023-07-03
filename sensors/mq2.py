import math
import time
from collections import namedtuple

import adafruit_mcp3xxx.mcp3008 as MCP
import board
import busio
import digitalio
from adafruit_mcp3xxx.analog_in import AnalogIn


class MQ2Sensor:
    # ---------------- Hardware Related ----------------
    RL_VALUE = 10  # define the load resistance on the board, in kilo ohms
    RO_CLEAN_AIR_FACTOR = 9.83  # Sensor resistance in clean air/RO, which is derived from the chart in datasheet

    # ---------------- Software Related ----------------
    CALIBRATION_SAMPLE_TIMES = 50  # how many samples you are going to take in the calibration phase
    CALIBRATION_SAMPLE_INTERVAL = 50  # the time interval(in millisecond) between each samples in the calibration phase
    READ_SAMPLE_INTERVAL = 50  # the time interval(in millisecond) between each samples in
    READ_SAMPLE_TIMES = 5  # how many samples you are going to take in normal operation

    # ---------------- Application Related ----------------
    GAS_LPG = 0
    GAS_CO = 1
    GAS_SMOKE = 2
    GAS_PROPANE = 3
    GAS_H2 = 4
    GAS_ALCOHOL = 5
    GAS_CH4 = 6

    def __init__(self, ro=10):
        self.ro = ro
        # create the spi bus
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

        # create the cs (chip select)
        cs = digitalio.DigitalInOut(board.D5)

        # create the mcp object
        mcp = MCP.MCP3008(spi, cs)

        # create an analog input channel on pin 0 for MQ2
        self.chan_MQ2 = AnalogIn(mcp, MCP.P0)

        self.LPGCurve = [2.3, 0.21, -0.47]  # two points are taken from the curve.
        # with these two points, a line is formed which is "approximately equivalent"
        # to the original curve.
        # data format:{ x, y, slope}; point1: (lg200, 0.21), point2: (lg10000, -0.59)
        self.COCurve = [2.3, 0.72, -0.34]  # two points are taken from the curve.
        # with these two points, a line is formed which is "approximately equivalent"
        # to the original curve.
        # data format:[ x, y, slope]; point1: (lg200, 0.72), point2: (lg10000,  0.15)
        self.SmokeCurve = [2.3, 0.53, -0.44]  # two points are taken from the curve.
        # with these two points, a line is formed which is "approximately equivalent"
        # to the original curve.
        # data format:[ x, y, slope]; point1: (lg200, 0.53), point2: (lg10000,  -0.22)
        self.PropaneCurve = [2.3, 0.24, -0.47]  # two points are taken from the curve.
        # with these two points, a line is formed which is "approximately equivalent"
        # to the original curve.
        # data format:[ x, y, slope]; point1: (lg200, 0.24), point2: (lg10000,  -0.55)
        self.H2Curve = [2.3, 0.33, -0.47]  # two points are taken from the curve.
        # with these two points, a line is formed which is "approximately equivalent"
        # to the original curve.
        # data format:[ x, y, slope]; point1: (lg200, 0.33), point2: (lg10000,  -0.47)
        self.AlcoholCurve = [2.3, 0.45, -0.37]  # two points are taken from the curve.
        # with these two points, a line is formed which is "approximately equivalent"
        # to the original curve.
        # data format:[ x, y, slope]; point1: (lg200, 0.33), point2: (lg10000,  -0.18)
        self.CH4Curve = [2.3, 0.49, -0.38]  # two points are taken from the curve.
        # with these two points, a line is formed which is "approximately equivalent"
        # to the original curve.
        # data format:[ x, y, slope]; point1: (lg200, 0.33), point2: (lg10000,  -0.15)

        print("Calibrating MQ-2...")
        self.ro = self.mq_calibration()
        print("Calibration of MQ-2 is done...")
        print("MQ-2 Ro=%f kohm" % self.ro)
        print("\n")

    ######################### MQCalibration ####################################
    # Input:   mq_pin - analog channel
    # Output:  Ro of the sensor
    # Remarks: This function assumes that the sensor is in clean air. It use
    #          MQResistanceCalculation to calculates the sensor resistance in clean air
    #          and then divides it with RO_CLEAN_AIR_FACTOR. RO_CLEAN_AIR_FACTOR is about
    #          9.83, which differs slightly between different sensors.
    ############################################################################
    def mq_calibration(self):
        val = 0.0
        for i in range(self.CALIBRATION_SAMPLE_TIMES):  # take multiple samples
            val += self.mq_resistance_calculation(self.chan_MQ2.value)
            time.sleep(self.CALIBRATION_SAMPLE_INTERVAL / 1000.0)

        val = val / self.CALIBRATION_SAMPLE_TIMES  # calculate the average value
        val = val / self.RO_CLEAN_AIR_FACTOR  # divided by RO_CLEAN_AIR_FACTOR yields the ro according to the chart
        return val

    ######################### MQResistanceCalculation #########################
    # Input:   raw_adc - raw value read from adc, which represents the voltage
    # Output:  the calculated sensor resistance
    # Remarks: The sensor and the load resistor forms a voltage divider. Given the voltage
    #          across the load resistor and its resistance, the resistance of the sensor
    #          could be derived.
    ############################################################################
    def mq_resistance_calculation(self, raw_adc):
        # print(raw_adc)
        # 1023 for 3008()
        # https://github.com/tutRPi/Raspberry-Pi-Gas-Sensor-MQ

        # 65472 for circuit python
        # Even though the MCP3008 is a 10-bit ADC, the value returned is a 16-bit number to provide a consistent interface across ADCs in CircuitPython
        # https://github.com/adafruit/Adafruit_CircuitPython_MCP3xxx/blob/main/adafruit_mcp3xxx/analog_in.py#L50-L54

        if raw_adc == 0:
            raw_adc = 1

        return float(self.RL_VALUE * (65472.0 - raw_adc) / float(raw_adc))

    #########################  MQRead ##########################################
    # Input:   mq_pin - analog channel
    # Output:  Rs of the sensor
    # Remarks: This function use MQResistanceCalculation to caculate the sensor resistenc (Rs).
    #          The Rs changes as the sensor is in the different consentration of the target
    #          gas. The sample times and the time interval between samples could be configured
    #          by changing the definition of the macros.
    ############################################################################
    def mq_read(self):
        rs = 0.0
        raw_value = 0.0
        for i in range(self.READ_SAMPLE_TIMES):
            raw_value += self.chan_MQ2.value
            rs += self.mq_resistance_calculation(self.chan_MQ2.value)
            time.sleep(self.READ_SAMPLE_INTERVAL / 1000.0)

        rs = rs / self.READ_SAMPLE_TIMES
        raw_value = raw_value / self.READ_SAMPLE_TIMES

        return rs, raw_value

    def mq_percentage(self):
        MQ_Data = namedtuple("MQ_Data", "lpg co smoke propane hydrogen alcohol methane")
        read, _ = self.mq_read()
        lpg = self.mq_get_gas_percentage(read / self.ro, self.GAS_LPG)
        co = self.mq_get_gas_percentage(read / self.ro, self.GAS_CO)
        smoke = self.mq_get_gas_percentage(read / self.ro, self.GAS_SMOKE)
        propane = self.mq_get_gas_percentage(read / self.ro, self.GAS_PROPANE)
        hydrogen = self.mq_get_gas_percentage(read / self.ro, self.GAS_H2)
        alcohol = self.mq_get_gas_percentage(read / self.ro, self.GAS_ALCOHOL)
        methane = self.mq_get_gas_percentage(read / self.ro, self.GAS_CH4)
        return MQ_Data(lpg, co, smoke, propane, hydrogen, alcohol, methane)

    #########################  MQGetGasPercentage ##############################
    # Input:   rs_ro_ratio - Rs divided by Ro
    #          gas_id      - target gas type
    # Output:  ppm of the target gas
    # Remarks: This function passes different curves to the MQGetPercentage function which
    #          calculates the ppm (parts per million) of the target gas.
    ############################################################################
    def mq_get_gas_percentage(self, rs_ro_ratio, gas_id):
        if gas_id == self.GAS_LPG:
            return self.mq_get_percentage(rs_ro_ratio, self.LPGCurve)
        elif gas_id == self.GAS_CO:
            return self.mq_get_percentage(rs_ro_ratio, self.COCurve)
        elif gas_id == self.GAS_SMOKE:
            return self.mq_get_percentage(rs_ro_ratio, self.SmokeCurve)
        elif gas_id == self.GAS_PROPANE:
            return self.mq_get_percentage(rs_ro_ratio, self.PropaneCurve)
        elif gas_id == self.GAS_H2:
            return self.mq_get_percentage(rs_ro_ratio, self.H2Curve)
        elif gas_id == self.GAS_ALCOHOL:
            return self.mq_get_percentage(rs_ro_ratio, self.AlcoholCurve)
        elif gas_id == self.GAS_CH4:
            return self.mq_get_percentage(rs_ro_ratio, self.CH4Curve)
        else:
            return 0

    #########################  MQGetPercentage #################################
    # Input:   rs_ro_ratio - Rs divided by Ro
    #          pcurve      - pointer to the curve of the target gas
    # Output:  ppm of the target gas
    # Remarks: By using the slope and a point of the line. The x(logarithmic value of ppm)
    #          of the line could be derived if y(rs_ro_ratio) is provided. As it is a
    #          logarithmic coordinate, power of 10 is used to convert the result to non-logarithmic
    #          value.
    ############################################################################
    def mq_get_percentage(self, rs_ro_ratio, pcurve):
        # print(rs_ro_ratio)
        # print((math.log(rs_ro_ratio)-pcurve[1]))
        # print(((math.log(rs_ro_ratio)-pcurve[1])/ pcurve[2]) + pcurve[0]))

        # This is the natural logarithm -> log(rs_ro_ratio)
        return math.pow(10, (((math.log(rs_ro_ratio) - pcurve[1]) / pcurve[2]) + pcurve[0]))
