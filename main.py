# Import necessary modules
import time
from random import random

from machine import Pin
import bluetooth
import machine
import ubinascii
from ble_kegscale import BLEKegScale
from hx711_kegscale import HX711KegScale

hx = HX711KegScale()

my_id = "keg-"+(ubinascii.hexlify(machine.unique_id()).decode())[:10]
# Create a Bluetooth Low Energy (BLE) object
ble = bluetooth.BLE()
print(my_id)
# Create an instance of the BLEKegScale class with the BLE object
ks = BLEKegScale(ble, "kegscale")
ks.set_scales(hx)


ks.register_calibration_callback(hx.update_calibration)


# Start an infinite loop
while True:
    measure_end_time = time.time()+5
    while(time.time() < measure_end_time):
        hx.take_measurements()
    measurement = hx.measure()
    ks.update_remaining(measurement)

