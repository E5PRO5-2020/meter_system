import os
import time


def start_fifo_and_write_fast():

    print("Open fifo and block")

    try:
        os.mkfifo("test_fifo")
    except:
        print("Didn't make FIFO, probably already exists. Trying to write to it.")

    fifo = open("test_fifo", 'w')

    for i in range(0,10):
        print("Putting message {} of 10 in FIFO".format(i))
        fifo.write(str(i) + '\n')
        time.sleep(0.2)

    fifo.close()


if __name__ == '__main__':
    start_fifo_and_write_fast()
