
import time
from machine import freq
from ucollections import deque

freq(160000000)
from hx711 import HX711
from machine import Pin
import os
import json





class HX711KegScale:
    def __init__(self):
        pin_OUT = Pin(0, Pin.IN, pull=Pin.PULL_DOWN)
        pin_SCK = Pin(1, Pin.OUT)
        self.hx = HX711(
            pin_OUT, pin_SCK
        )
        self.hx.channel = HX711.CHANNEL_A_64
        self.rollingArray = deque([], 200)
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
                print("data " + str(data))
                self.zero = data["zero"]
                print("zero " + str(self.zero))
                self.full = data["full"]
                self.volume = data["volume"]

                self.calibrationState = data["calibrationState"]
                print("cal state " + str(self.calibrationState))
        except Exception as e:
            print("calibration not loaded: " + str(e))
        return self.calibrationState

    def save_calibration(self):
        os.chdir("/")
        try:
            data = {"zero": self.zero, "full": self.full, "volume": self.volume, "calibrationState": self.calibrationState}
            with open('calibration.txt', "w", encoding="utf-8") as f:
                json.dump(data, f)
                print("calibration saved")
        except Exception as e:
            print("calibration save failed "+str(e))
        return self.calibrationState

    def set_zero(self):
        self.zero = self.measure()
        self.calibrationState = 1
        self.save_calibration()

    def set_full(self):
        self.full = self.measure()
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
                print("Calibration state error")

        print("Updating calibration")
        return self.calibrationState

    def take_measurements(self):
        self.rollingArray.append(int((self.volume / self.full) * (self.hx.read() - self.zero)))
        time.sleep(0.1)



    def measure(self):
        measurement = sum(self.rollingArray)/(len(self.rollingArray)-1)
        print("Average "+str(measurement))

        return measurement




