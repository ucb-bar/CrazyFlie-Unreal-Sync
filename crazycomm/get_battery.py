import logging
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger

# URI to the Crazyflie to connect to
uri = "radio://0/80/1M/E7E7E7E7E7"

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

def simple_log(scf, logconf):
    with SyncLogger(scf, lg_stab) as logger:
        
        for log_entry in logger:
            timestamp, data, logconf_name = log_entry
            print("  Battery Voltage:  \t{:.2f} V".format(data.get("pm.vbat")))
            print("  Battery Level:    \t{:.2f} %".format(data.get("pm.batteryLevel")))
            print("  Charging Current: \t{:.2f} mA".format(data.get("pm.chargeCurrent") * 1000))
            break

if __name__ == "__main__":
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    lg_stab = LogConfig(name="PM", period_in_ms=10)
    
    lg_stab.add_variable("pm.vbat", "float")
    lg_stab.add_variable("pm.chargeCurrent", "float")
    lg_stab.add_variable("pm.batteryLevel", "float")
    
    group = "stabilizer"
    name = "estimator"

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache="./cache")) as scf:
        simple_log(scf, lg_stab)
