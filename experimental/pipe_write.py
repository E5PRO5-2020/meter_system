"""
Example of using FIFO asynchronously. This file writes to the FIFO.

- The POSIX FIFO (named pipe) uses a block buffer by default.
- By default then, a "reader" will wait for the buffer to be full before anything is read.
- Or, will wait for the "writer" to close the FIFO.
- One way is to change the buffer type of the reader open(fifo, 'r', 0).
- A better way is to just call flush on the writer side, to signify ready.
- Then read is performed immediately.

Janus, Nov. 5, 2020

"""

import os
import time
import errno


def start_fifo_and_write_fast():

    fifo_name = "test_fifo"
    p = os.path.abspath(fifo_name)

    try:
        os.mkfifo(p)
    except OSError as e:
        if e.errno == errno.EEXIST:
            print("FIFO already exists.")
        else:
            print("Couldn't make FIFO. Exiting.")
            exit()

    print("Open fifo, will block. Path: {}".format(p))
    with open(p, 'w') as fifo:
        for i in range(1, 11):
            msg = "Hello #{}".format(i)
            print("Putting message {} of 10 in FIFO: {}".format(i, msg))
            fifo.write(msg + os.linesep)
            fifo.flush()                    # This is important!
            time.sleep(0.2)                 # Simulate faster writing

    time.sleep(2)                           # Simulate keeping FIFO open but inactive


if __name__ == '__main__':
    start_fifo_and_write_fast()
