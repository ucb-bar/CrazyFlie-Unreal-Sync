import logging
import sys
import time
from threading import Event
import math

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

from unrealbridge import UnrealBridge

class CrazyClient:
    def __init__(self, link="radio://0/80/1M/E7E7E7E7E7"):
        self.uri = uri_helper.uri_from_env(default=link)
        
        self.update_watchdog_timer = time.time()
        self.update_watchdog_enabled = False

        self.deck_attached_event = Event()

        logging.basicConfig(level=logging.ERROR)

        self.data = None

    def log_callback(self, timestamp, data, logconf):
        self.data = data
        if not self.update_watchdog_enabled:
            self.update_watchdog_enabled = True
        self.update_watchdog_timer = time.time()

    def lightHouseDeck_callback(self, _, value_str):
        value = int(value_str)
        print("<lightHouseDeck_callback>:", value)
        if value:
            self.deck_attached_event.set()
            print("<lightHouseDeck_callback>: Deck is attached!")
        else:
            print("<lightHouseDeck_callback>: Deck is NOT attached!")

    def checkWatchdog(self):
        if self.update_watchdog_enabled and time.time() - self.update_watchdog_timer > 4:
            print("Watchdog timeout! Restarting...")
            return False
        return True
        

    def start(self):
        self.update_watchdog_enabled = False
        cflib.crtp.init_drivers()
        self.scf = SyncCrazyflie(self.uri, cf=Crazyflie(rw_cache="./cache"))
        self.scf.open_link()
        self.scf.cf.param.add_update_callback(group="deck", name="bcLighthouse4", cb=self.lightHouseDeck_callback)
        time.sleep(1)

        self.logconf = LogConfig(name="Position", period_in_ms=100)
        self.logconf.add_variable("stateEstimate.x", "float")
        self.logconf.add_variable("stateEstimate.y", "float")
        self.logconf.add_variable("stateEstimate.z", "float")
        self.logconf.add_variable("stateEstimate.roll", "float")
        self.logconf.add_variable("stateEstimate.pitch", "float")
        self.logconf.add_variable("stateEstimate.yaw", "float")

        self.scf.cf.log.add_config(self.logconf)
        self.logconf.data_received_cb.add_callback(cb=self.log_callback)

        if not self.deck_attached_event.wait(timeout=5):
            print("No position tracking deck detected!")
            return 1

        self.logconf.start()
        return 0

    def stop(self):
        self.update_watchdog_enabled = False
        self.scf.close_link()
        self.logconf.stop()


if __name__ == "__main__":
    client = CrazyClient(link="radio://0/80/1M/E7E7E7E7E7")
    bridge = UnrealBridge(port=8080)

    client.start()
    bridge.start()

    try:
        while True:
            # if not client.checkWatchdog():
            #     print("false")
            #     client.stop()
            #     client.start()
            #     continue
                
            if not client.data:
                continue
            
            x = client.data["stateEstimate.x"]
            y = client.data["stateEstimate.y"]
            z = client.data["stateEstimate.z"]
            pitch = client.data["stateEstimate.pitch"]
            roll = client.data["stateEstimate.roll"]
            yaw = client.data["stateEstimate.yaw"]

            x_ = x
            x = -y
            y = x_

            # print("{:3f}\t {:3f}\t {:3f}".format(x, y, z))
            # print("{:3f}\t {:3f}\t {:3f}".format(pitch, roll, yaw))


            bridge.setData("/x", x)
            bridge.setData("/y", y)
            bridge.setData("/z", z)
            bridge.setData("/pitch", pitch)
            bridge.setData("/roll", roll)
            bridge.setData("/yaw", yaw)
            
            time.sleep(0.05)


    except KeyboardInterrupt:
        print("interrupted")
        client.stop()
        bridge.stop()
    except Exception as e:
        print(e)
        client.stop()
        bridge.stop()
