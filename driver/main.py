import daemon   # type: ignore
from driver.DriverClass import IM871A
import time
import os

# Get program directory
path = os.path.dirname(os.path.abspath(__file__))

# Run as daemon
with daemon.DaemonContext():
    myUSB = IM871A('/dev/ttyUSB0', path)
    if(myUSB.reset_module()):      
        # Needs time after reset before being able to setup linkmode
        time.sleep(2)
        myUSB.setup_linkmode('c1a')
        while True:
            myUSB.read_data()   
        
    
