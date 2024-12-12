
import time
from machine import freq
from ucollections import deque

freq(160000000)
from lib.hx711 import HX711
from machine import Pin
import os
import json





class HX711KegScale:
    def __init__(self, logger):
        self.logger=logger
        pin_OUT = Pin(0, Pin.IN, pull=Pin.PULL_DOWN)
        pin_SCK = Pin(1, Pin.OUT)
        self.hx = HX711(
            pin_OUT, pin_SCK
        )
        self.hx.channel = HX711.CHANNEL_A_64
        self.rollingArray = deque([], 200)
        self.tempRollingArray = deque([], 200)
        self.calibrationState = 0
        self.zero = 0
        self.full = 20000
        self.volume = 20000
        self.load_calibration()

    def load_calibration(self):
        os.chdir("/")
        try:
            with open('calibration.txt', "r") as f:
                data = json.load(f)
                self.logger.log("data " + str(data))
                self.zero = data["zero"]
                self.logger.log("zero " + str(self.zero))
                self.full = (data["full"] or 1)
                self.volume = data["volume"]

                self.calibrationState = data["calibrationState"]
                self.logger.log("cal state " + str(self.calibrationState))
        except Exception as e:
            self.logger.log("calibration not loaded: " + str(e))
        return self.calibrationState


    def save_calibration(self):
        os.chdir("/")
        try:
            data = {"zero": self.zero, "full": self.full, "volume": self.volume, "calibrationState": self.calibrationState}
            with open('calibration.txt', "w", encoding="utf-8") as f:
                json.dump(data, f)
                self.logger.log("calibration saved - " + str(data))
        except Exception as e:
            self.logger.log("calibration save failed "+str(e))
        self.rollingArray=deque([], 50)
        return self.calibrationState

    def set_zero(self):
        self.zero = self.measure()
        self.calibrationState = 1
        self.save_calibration()

    def set_full(self):
        current = self.measure()
        if current==0:
            return
        self.full = current
        self.calibrationState = 2
        self.save_calibration()

    def set_volume(self, volume):
        self.volume = volume
        self.save_calibration()

    def reset(self):
        self.zero = 0
        self.full = self.volume
        self.calibrationState = 0
        self.save_calibration()

    def get_calibration_state(self):
        return self.calibrationState

    def get_calibration_volume(self):
        return self.volume

    def update_calibration(self, data):
        if (data != "update") :
            self.set_volume(int(data))
        else:
            if(self.calibrationState == 0):
                self.set_zero()
            elif(self.calibrationState == 1):
                self.set_full()
            elif(self.calibrationState ==2):
                self.reset()
            else:
                self.logger.log("Calibration state error")

        self.logger.log("Updating calibration")
        return self.calibrationState

    def take_measurements(self):
        new = int((self.volume / self.full) * (self.hx.read() - self.zero))
        if (new ==0):
            self.logger.log("Zero rejected" + str(new))
            return
        if (len(self.rollingArray) < 20):
            self.rollingArray.append(new)
            return
        avg = sum(self.rollingArray) / (len(self.rollingArray))
        if avg==0:
            self.rollingArray.append(new)
            return
        if abs(((new - avg) / avg))<0.25 or abs(new-avg)<100:
            self.rollingArray.append(new)
            self.logger.log("Accepted " + str(new))
            self.tempRollingArray = deque([], 200)
        else:
            self.logger.log("Rejected "+str(new) + " - " + str(avg) + " - " + str(abs(((new - avg) / avg))))
            self.tempRollingArray.append(new)
            if (len(self.tempRollingArray)>10):
                self.logger.log("Reset to new value")
                self.rollingArray = self.tempRollingArray
                self.tempRollingArray = deque([], 200)

        time.sleep(0.05)



    def measure(self):
        measurement = sum(self.rollingArray)/(len(self.rollingArray)-1)
        self.logger.log("Average "+str(measurement))

        return measurement




