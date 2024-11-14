# Import necessary modules
import time
import bluetooth
import machine
import ubinascii
from lib.ble_kegscale import BLEKegScale
from lib.hx711_kegscale import HX711KegScale
import logserver
logger = logserver.LogServer()
hx = HX711KegScale(logger)


my_id = "keg-"+(ubinascii.hexlify(machine.unique_id()).decode())[:10]
# Create a Bluetooth Low Energy (BLE) object
ble = bluetooth.BLE()
# Create an instance of the BLEKegScale class with the BLE object
ks = BLEKegScale(ble, logger)
ks.set_scales(hx)
ks.register_calibration_callback(hx.update_calibration)
logger.log("NEW!!!")

while True:
    measure_end_time = time.time()+5
    while(time.time() < measure_end_time):
        hx.take_measurements()
    logger.log("Measuring")
    measurement = hx.measure()
    ks.update_remaining(measurement)
    logger.log("Connect attempt")
    logger.connect()
    logger.log("Loop End")

