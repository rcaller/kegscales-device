import json
import os


def wifiConnect():
    import network
    os.chdir("/")
    ssid=""
    password=""
    try:
        with open('wifi.txt', "r", encoding="utf-8") as f:
            wifiJson = json.load(f)
            print(str(wifiJson))
            ssid=wifiJson["ssid"]
            password = wifiJson["pwd"]

    except Exception as e:
        print("Wifi read failed " + str(e))
        return False
    if (ssid==""):
        print("Wifi not defined")
        return False
    network.hostname('kegscales')

    station = network.WLAN(network.STA_IF)
    station.config(hostname="kegscales")
    station.active(True)
    networks = station.scan()
    for network in networks:
        detected_ssid, bssid, channel, RSSI, authmode, hidden = network
        if (detected_ssid.decode('utf-8') == ssid):
            print("Connecting to " + ssid)
            station.connect(ssid, password)
            while station.isconnected() == False:
                pass
            print('Connection successful')
            print(station.ifconfig())
            continue
    if station.isconnected() == False:
        print("Wifi " + ssid + " not connected")
        return False
    else:
        return True
