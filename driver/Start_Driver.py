"""
Runs the IM871A dongle driver, starting it as a daemon.
The path of where to put the pipe is created before creating the daemon,
to put it in the driver folder.
Mode for IM871A is set to 'c1a'.

Call kill -15 <pid> to send SIGTERM and leave program nicely.
"""

import daemon   # type: ignore
from driver.DriverClass import IM871A
import time, signal
import os
from utils.log import get_logger


# Main_program will be run as daemon
def main_program():
    log = get_logger()
    log.info("Start daemon")

    # Instantialte driver object
    myIM871A = IM871A(path)

    if(myIM871A.reset_module()):      
        # Needs time after reset before being able to setup linkmode
        time.sleep(2)
        myIM871A.setup_linkmode('c1a')
        myIM871A.open_pipe()
        while True:
            myIM871A.read_data()   


if __name__ == "__main__":
    # Get program directory
    path = os.path.dirname(os.path.abspath(__file__))

    context = daemon.DaemonContext()
    context.signal_map = { signal.SIGTERM: 'terminate' }

    # Daemon starts here
    context.open()

    with context:
        main_program()
