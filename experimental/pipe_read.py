"""
Example of using FIFO asynchronously. This file reads from the FIFO.

Janus, Nov. 5, 2020

"""

import os
import time
from select import select


def open_fifo_and_read_slow():

    fifo_name = "test_fifo"
    p = os.path.abspath(fifo_name)

    print("Attempt to open fifo to read.")
    try:
        with open(p, 'r') as fifo:
            print("Reading from FIFO. Blocks until done. Path: {}".format(p))

            while True:
                msg = fifo.readline()
                if msg:
                    print("Message: {}".format(msg.strip()))        # Without line break
                if msg.strip() == "dienowplease":                   # send "dienowplease" to stop
                    print("Exiting.")
                    exit(0)

                time.sleep(0.4)                             # Simulate slower reading
                select([fifo], [], [])                      # polls and wait for data ready for read on fifo

    except OSError as e:
        print("Can't open FIFO. Exiting.")
        exit(e.errno)


if __name__ == '__main__':
    open_fifo_and_read_slow()
