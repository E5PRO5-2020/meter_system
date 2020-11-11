import daemon   # type: ignore
from DriverClass import IM871A
import time
import os

"""
Runs the IM871A dongle driver, starting it as a daemon.
The path of where to put the pipe is created before creating the daemon, 
to put it in the driver folder.
Mode for IM871A is set to 'c1a'.
"""

# Get program directory
path = os.path.dirname(os.path.abspath(__file__))

# Run as daemon
with daemon.DaemonContext():
    myUSB = IM871A(path)
    if(myUSB.reset_module()):      
        # Needs time after reset before being able to setup linkmode
        time.sleep(2)
        myUSB.setup_linkmode('c1a')
        while True:
            myUSB.read_data()   
        
    
