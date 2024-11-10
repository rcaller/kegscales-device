import network
from wifi_config import ssid, password
from ota import OTAUpdater

network.hostname('kegscales')

station = network.WLAN(network.STA_IF)
station.config(hostname="kegscales")
station.active(True)
networks = station.scan()
network_exists = False
for network in networks:
  detected_ssid, bssid, channel, RSSI, authmode, hidden = network
  if (detected_ssid.decode('utf-8') == ssid):
    print("Connecting to "+ssid)
    station.connect(ssid, password)
    while station.isconnected() == False:
      pass
    print('Connection successful')
    print(station.ifconfig())
    continue
if station.isconnected() == False:
  print("Wifi "+ssid+" not detected")
else:
  firmware_url = "https://raw.githubusercontent.com/rcaller/kegscales-device/main"
  ota = OTAUpdater(firmware_url)
  ota.download_and_install_update_if_available()