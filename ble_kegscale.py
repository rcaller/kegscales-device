import os
import bluetooth
import struct
from collections import deque
from ble_advertising import advertising_payload
from micropython import const

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
_KEGSCALE_SERVICE = (
    _KEGSCALE_UUID,
    [_KEGSCALE_REMAINING,
     _KEGSCALE_POURED,
     _KEGSCALE_CALIBRATION_STATUS,
     _KEGSCALE_CALIBRATION_VOLUME,
     _KEGSCALE_SETCALIBRATION,
     _KEGSCALE_NAME],
)


class BLEKegScale:
    def __init__(self, ble, name="kegscale"):
        self._scales = None
        self._calibration_callback = None
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_remaining, self._handle_poured, self._handle_calibration_status, self._handle_calibration_volume, self._handle_setcalibration, self._handle_name),) = self._ble.gatts_register_services((_KEGSCALE_SERVICE,))

        self._connections = set()
        self._name = self.get_name()
        self._payload = advertising_payload(name=name, services=[_KEGSCALE_UUID])
        self._advertise()
        self._data_history = deque([0]*25, 25)
        self._pouring = False
        self._pour_start = 0


        self._testData = iter([15000,5000,15000,15000,14990,14980,14950,14930,14920,14910,14900,14900,14900,14900,14900])


    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            print("New connection", conn_handle)
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            print("Disconnected", conn_handle)
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, attr_handle = data
            print("Write event "+str(attr_handle))
            if (attr_handle == self._handle_setcalibration):
                data = self._ble.gatts_read(attr_handle).decode()
                print("Written data " + str(data))
                if(str(data) == "update"):
                    calState = self._calibration_callback(str(data))
                    self.set_calibration_state(calState)
                else:
                    self._calibration_callback(str(data))
            elif (attr_handle == self._handle_name):
                self.update_name(str(self._ble.gatts_read(attr_handle).decode()))

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=500000):
        print("Starting advertising")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def register_calibration_callback(self, callback):
        self._calibration_callback = callback


    def update_remaining(self, data):
        print("remaining - " + str(data))
        print("handle - " + str(self._handle_remaining))
        change = self._data_history[0] - int(data)
        self._data_history.appendleft(int(data))
        print("change "+str(change))
        if (change<-(50) or change>(500)) :
            print("rejected large change")
            return

        if (not self._pouring and (change)>30):
            print("Pour Started")
            self._pouring = True
            self._pour_start = self._data_history[0]
        elif (change>30):
            print("Pouring")
            poured_volume = self._pour_start - int(data)
            if (poured_volume > 50):
                self._ble.gatts_write(self._handle_poured, struct.pack(">I", poured_volume), True)
        elif (self._pouring and change<30) :
            self._pouring = False
            poured_volume = self._pour_start - int(data)
            if (poured_volume > 50):
                self._ble.gatts_write(self._handle_poured, struct.pack(">I", poured_volume), True)
                print("poured " + str(self._pour_start - int(data)))

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
                print("Name saved")
        except Exception as e:
            print("Name save failed " + str(e))

    def get_name(self):
        os.chdir("/")
        try:
            with open('name.txt', "r", encoding="utf-8") as f:
                name = f.read()
                print("Name read")
                return name
        except Exception as e:
            print("Name read failed " + str(e))
        return "Keg Scale"

    def set_name(self):
        print("Setting name " + str(self._name))
        self._ble.gatts_write(self._handle_name, self._name.encode("utf-8"))




