
from wifi_config import ssid, password


def wifiConnect():
    import network

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
