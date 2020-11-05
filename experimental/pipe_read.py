import time


def open_fifo_and_read_slow():

    print("Open fifo to read")
    fifo = open("test_fifo", 'r')

    for i in range(0,10):
        print("Reading from FIFO")
        print(fifo.read(2))
        time.sleep(0.5)

    fifo.close()


if __name__ == '__main__':
    open_fifo_and_read_slow()
