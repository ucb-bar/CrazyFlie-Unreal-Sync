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


URI = uri_helper.uri_from_env(default="radio://0/80/2M/E7E7E7E7E7")

DEFAULT_HEIGHT = 0.5
BOX_LIMIT = 0.05

deck_attached_event = Event()

logging.basicConfig(level=logging.ERROR)

position_estimate = [0, 0, 0]


def log_pos_callback(timestamp, data, logconf):
    global position_estimate
    
    x = data["stateEstimate.x"]
    y = data["stateEstimate.y"]
    z = data["stateEstimate.z"]

    x *= 0.7071
    y *= 0.7071
    z *= 0.7071

    theta = -0.25 * math.pi
    x_ = x * math.cos(theta) + y * math.sin(theta)
    y_ = x * -math.sin(theta) + y * math.cos(theta)
    
    position_estimate[0] = x_
    position_estimate[1] = y_
    position_estimate[2] = z

    print(position_estimate)

def param_deck_lighthouse(_, value_str):
    value = int(value_str)
    print(value)
    if value:
        deck_attached_event.set()
        print("Deck is attached!")
    else:
        print("Deck is NOT attached!")


if __name__ == "__main__":
    cflib.crtp.init_drivers()
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache="./cache")) as scf:
        scf.cf.param.add_update_callback(group="deck", name="bcLighthouse4", cb=param_deck_lighthouse)
        time.sleep(1)

        logconf = LogConfig(name="Position", period_in_ms=10)
        logconf.add_variable("stateEstimate.x", "float")
        logconf.add_variable("stateEstimate.y", "float")
        logconf.add_variable("stateEstimate.z", "float")
        scf.cf.log.add_config(logconf)
        logconf.data_received_cb.add_callback(log_pos_callback)


        if not deck_attached_event.wait(timeout=5):
            print("No flow deck detected!")
            sys.exit(1)

        logconf.start()

        while (1):
            pass

        logconf.stop()
        