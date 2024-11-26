import json
import os

import bluetooth
import struct
from machine import Pin, Timer
from collections import deque
from lib.ble_advertising import advertising_payload
from micropython import const
import machine

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_KEGSCALE_UUID = bluetooth.UUID("28f273ff-9f53-45d4-852a-bfb214442d44")
_KEGSCALE_REMAINING = (
    bluetooth.UUID("28f273fe-9f53-45d4-852a-bfb214442d44"),
    _FLAG_READ,
)
_KEGSCALE_POURED = (
    bluetooth.UUID("28f273fd-9f53-45d4-852a-bfb214442d44"),
    (_FLAG_READ |_FLAG_NOTIFY),
)
_KEGSCALE_CALIBRATION_STATUS = (
    bluetooth.UUID("28f273fc-9f53-45d4-852a-bfb214442d44"),
    _FLAG_READ,
)
_KEGSCALE_CALIBRATION_VOLUME = (
    bluetooth.UUID("28f273fa-9f53-45d4-852a-bfb214442d44"),
    _FLAG_READ,
)
_KEGSCALE_NAME = (
    bluetooth.UUID("28f273f9-9f53-45d4-852a-bfb214442d44"),
    (_FLAG_READ| _FLAG_WRITE),
)
_KEGSCALE_SETCALIBRATION = (
    bluetooth.UUID("28f273fb-9f53-45d4-852a-bfb214442d44"),
    _FLAG_WRITE,
)
_KEGSCALE_SETWIFI = (
    bluetooth.UUID("28f273f8-9f53-45d4-852a-bfb214442d44"),
    _FLAG_WRITE,
)
_KEGSCALE_SERVICE = (
    _KEGSCALE_UUID,
    [_KEGSCALE_REMAINING,
     _KEGSCALE_POURED,
     _KEGSCALE_CALIBRATION_STATUS,
     _KEGSCALE_CALIBRATION_VOLUME,
     _KEGSCALE_SETCALIBRATION,
     _KEGSCALE_NAME,
     _KEGSCALE_SETWIFI],
)


class BLEKegScale:
    def __init__(self, ble, logger):
        self.logger = logger
        self._scales = None
        self._calibration_callback = None
        self._ble = ble
        self._ble.active(True)
        ble.config(mtu=517)

        self._ble.irq(self._irq)
        ((self._handle_remaining, self._handle_poured, self._handle_calibration_status, self._handle_calibration_volume, self._handle_setcalibration, self._handle_name, self._handle_wifi),) = self._ble.gatts_register_services((_KEGSCALE_SERVICE,))
        self._connections = set()
        self._name = self.get_name()
        self._payload = advertising_payload(name="kegscale", services=[_KEGSCALE_UUID])
        self._ble.gatts_set_buffer(self._handle_wifi, 100, True)
        self._data_history = deque([0]*25, 25)
        self._pouring = False
        self._pour_start = 0
        self._testData = iter([15000,5000,15000,15000,14990,14980,14950,14930,14920,14910,14900,14900,14900,14900,14900])
        self.led = Pin('LED', Pin.OUT)
        self.led_state = False
        self.ledtimer=Timer()
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self.logger.log("New connection " + str(conn_handle))
            self.stop_flash()
            self.led.value(True)
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self.logger.log("Disconnected "+ str(conn_handle))
            self._connections.remove(conn_handle)
            self.led.value(False)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, attr_handle = data
            self.logger.log("Write event "+str(attr_handle))
            if (attr_handle == self._handle_setcalibration):
                data = self._ble.gatts_read(attr_handle).decode()
                self.logger.log("Written data " + str(data))
                if(str(data) == "update"):
                    calState = self._calibration_callback(str(data))
                    self.set_calibration_state(calState)
                else:
                    self._calibration_callback(str(data))
            elif (attr_handle == self._handle_name):
                self.update_name(str(self._ble.gatts_read(attr_handle).decode()))
            elif (attr_handle == self._handle_wifi):
                self.set_wifi(str(self._ble.gatts_read(attr_handle).decode()))

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=500000):
        self.logger.log("Starting advertising")
        self.start_flash()
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def register_calibration_callback(self, callback):
        self._calibration_callback = callback


    def update_remaining(self, data):
        self.logger.log("remaining - " + str(data))
        self.logger.log("handle - " + str(self._handle_remaining))
        change=0
        if (self._data_history[0]):
            change = abs((self._data_history[0] - int(data))/self._data_history[0])
        self._data_history.appendleft(int(data))
        self.logger.log("change "+str(change))

        if (not self._pouring and (change)>0.002):
            self.logger.log("Pour Started")
            self._pouring = True
            self._pour_start = self._data_history[0]
        if (change>0.002):
            self.logger.log("Pouring")
            poured_volume = self._pour_start - int(data)
            if (poured_volume > 0):
                for conn_handle in self._connections:
                    print("notifying "+ str(conn_handle))
                    self._ble.gatts_notify(conn_handle, self._handle_poured)
                self._ble.gatts_write(self._handle_poured, struct.pack(">I", poured_volume), True)
        elif (self._pouring and change<0.002) :
            self._pouring = False
            poured_volume = self._pour_start - int(data)
            if (poured_volume > 0):
                gwo = self._ble.gatts_write(self._handle_poured, struct.pack(">I", poured_volume), True)
                for conn_handle in self._connections:
                    print("notifying "+ str(conn_handle))
                    self._ble.gatts_notify(conn_handle, self._handle_poured)
                print("poured " + str(self._pour_start - int(data)) + " " + str(gwo))

        self._ble.gatts_write(self._handle_remaining, struct.pack(">I", int(data)))

    def set_calibration_state(self, calibration_state):
        self._ble.gatts_write(self._handle_calibration_status, struct.pack(">I", int(calibration_state)))

    def set_calibration_volume(self, volume):
        self._ble.gatts_write(self._handle_calibration_volume, struct.pack(">I", int(volume)))

    def test_keg_data(self):
        return next(self._testData)

    def set_scales(self, hx):
        self._scales = hx
        self.set_calibration_state(hx.get_calibration_state())
        self.set_calibration_volume(hx.get_calibration_volume())
        self.set_name()

    def update_name(self, name):
        self._name = name
        os.chdir("/")
        try:
            with open('name.txt', "w", encoding="utf-8") as f:
                f.write(name)
                self.logger.log("Name saved")
        except Exception as e:
            self.logger.log("Name save failed " + str(e))

    def get_name(self):
        os.chdir("/")
        try:
            with open('name.txt', "r", encoding="utf-8") as f:
                name = f.read()
                self.logger.log("Name read")
                return name
        except Exception as e:
            self.logger.log("Name read failed " + str(e))
        return "Keg Scale"

    def set_name(self):
        self.logger.log("Setting name " + str(self._name))
        self._ble.gatts_write(self._handle_name, self._name.encode("utf-8"))

    def blink_led(self, timer):
        if self.led_state:
            self.led.toggle()


    def start_flash(self):
        self.led_state = True
        self.ledtimer.init(period=500, mode=Timer.PERIODIC, callback=self.blink_led)

    def stop_flash(self):
        led_state = False
        self.ledtimer.deinit()  # Stop the timer
        self.led.value(0)

    def set_wifi(self, wifiJsonString):
        self.logger.log("wifi json: "+wifiJsonString)
        wifiJson = json.loads(wifiJsonString)
        os.chdir("/")
        try:
            with open('wifi.txt', "w", encoding="utf-8") as f:
                json.dump(wifiJson, f)
                self.logger.log("Wifi saved")
                #machine.reset()
        except Exception as e:
            self.logger.log("Wifi save failed " + str(e))
