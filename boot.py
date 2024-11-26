
from lib.wifi_connector import wifiConnect
import machine, gc


def startUp():
    import lib.start

def update():
    from lib.ota_updater import OTAUpdater
    otaUpdater = OTAUpdater('https://github.com/rcaller/kegscales-device', main_dir='lib')
    hasUpdated = otaUpdater.install_update_if_available()
    if hasUpdated:
        machine.reset()
    else:
        del(otaUpdater)
        gc.collect()

if wifiConnect():
    update()
startUp()


