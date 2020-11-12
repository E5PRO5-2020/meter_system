import daemon   # type: ignore
from driver.DriverClass import IM871A
import time, signal
import os
from utils.log import get_logger

"""
Runs the IM871A dongle driver, starting it as a daemon.
The path of where to put the pipe is created before creating the daemon, 
to put it in the driver folder.
Mode for IM871A is set to 'c1a'.
"""

# Get program directory
path = os.path.dirname(os.path.abspath(__file__))

# Get logging instance
log = get_logger()

# Instantiate new driver
myIM871A = IM871A(path)

# Run as daemon
def run_daemon():
    context = daemon.DaemonContext()
    context.signal_map = { signal.SIGTERM: program_cleanup }
    log.info("IM871A-Driver daemon started")

    context.open()
    with context:
        main_program()

def main_program():
    
    if(myIM871A.reset_module()):      
        # Needs time after reset before being able to setup linkmode
        time.sleep(2)
        myIM871A.setup_linkmode('c1a')
        while True:
            myIM871A.read_data()   
        
    
def program_cleanup():
    myIM871A.close()
    log.info("IM871A-Driver daemon stopped")

if __name__ == "__main__":
    run_daemon()
