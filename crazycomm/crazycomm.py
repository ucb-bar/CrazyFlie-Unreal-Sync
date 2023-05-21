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
        

    def abs_position_control(scf):
        with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
            target_position = [0, 0, 0]
            while 1:
                print(target_position[0], "\t", position_estimate[0])
                target_position[0] = 0.5 * math.sin(time.time())

                err_x = target_position[0] - position_estimate[0]
                err_y = target_position[1] - position_estimate[1]

                kp = 1

                vel_x = kp * err_x
                vel_y = kp * err_y

                mc.start_linear_motion(vel_x, vel_y, 0)

                time.sleep(0.1)

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
    bridge = UnrealBridge(port=8000)

    client.start()
    bridge.start()

    try:
        with MotionCommander(client.scf, default_height=0.5) as mc:
            while True:
                
                # if not client.checkWatchdog():
                #     print("false")
                #     client.stop()
                #     client.start()
                #     continue
                    
                if not client.data:
                    continue
                
                cf_x = client.data["stateEstimate.x"]
                cf_y = client.data["stateEstimate.y"]
                cf_z = client.data["stateEstimate.z"]
                pitch = client.data["stateEstimate.pitch"]
                roll = client.data["stateEstimate.roll"]
                yaw = client.data["stateEstimate.yaw"]

                # CrazyFlie frame to Our Frame
                x = -cf_y
                y = cf_x
                z = cf_z

                # print("{:3f}\t {:3f}\t {:3f}".format(x, y, z))
                # print("{:3f}\t {:3f}\t {:3f}".format(pitch, roll, yaw))


                bridge.setData("/x", x)
                bridge.setData("/y", y)
                bridge.setData("/z", z)
                bridge.setData("/pitch", pitch)
                bridge.setData("/roll", roll)
                bridge.setData("/yaw", yaw)

                
                cmd_x = bridge.getData("/cmd_x", 0)
                cmd_y = bridge.getData("/cmd_y", 0)
                cmd_z = bridge.getData("/cmd_z", 0)
                cmd_yaw = bridge.getData("/cmd_yaw", 0)
                cmd_is_stopped = bridge.getData("/cmd_is_stopped", False)

                if cmd_is_stopped:
                    break
                
                keep_off_distance = 0.2

                cmd_x += keep_off_distance * math.sin(cmd_yaw * math.pi / 180)
                cmd_y += keep_off_distance * math.cos(cmd_yaw * math.pi / 180)
                # cmd_z += 0.2

                err_x = cmd_x - x
                err_y = cmd_y - y
                err_z = cmd_z - z

                # kp_xy = 2.25
                # kp_z = 1.75
                
                kp_xy = 2.5
                kp_z = 2

                vel_x = kp_xy * err_x
                vel_y = kp_xy * err_y
                vel_z = kp_z * err_z

                # Our frame to CrazyFlie Frame
                cf_vel_x = vel_y
                cf_vel_y = -vel_x
                cf_vel_z = vel_z

                mc.start_linear_motion(cf_vel_x, cf_vel_y, cf_vel_z)

                print(cmd_x, x, cmd_is_stopped, cmd_yaw)
                time.sleep(0.05)


    except KeyboardInterrupt:
        print("interrupted")
    except Exception as e:
        print(e)
    
    client.stop()
    bridge.stop()
