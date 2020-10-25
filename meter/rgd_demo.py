"""
This file is a demo for RGD
"""

from termcolor import colored
from datetime import datetime

from meter.OmniPower import OmniPower, C1Telegram
from utils.timezone import ZuluTime, zulu_time_str


def demo_0():

    # Set up timezone
    zulu_time = ZuluTime()

    # Set up OmniPower with our default settings
    omnipower = OmniPower()

    # Simulate receiving a set of mixed encrypted telegrams from IM871-A
    telegrams = [b'27442D2C5768663230028D202E21870320D3A4F149B1B8F5783DF7434B8A66A55786499ABE7BAB59ffff',
                 b'27442d2c5768663230028d206360dd0320c42b87f46fc048d42498b44b5e34f083e93e6af16176313d9c',
                 b'2d442d2c5768663230028d206461dd032038931d14b405536e0250592f8b908138d58602eca676ff79e0caf0b14d0e7d',
                 b'27442d2c5768663230028d206562dd03200ac3aea1e613dd9af1a75c68cdedd5fdd2617c1e71a9d0b3b1',
                 b'2d442d2c5768663230028d206c81dd03202dcd10989cd870e4439ee09a309f7114681d40570623dfae7b3c6214679786',
                 b'27442d2c5768663230028d206e90dd03201dfbbd7871e6ec990f60ee940532c09e505bd4cac5728e2864']

    # Process the telegrams
    for telegram in telegrams:
        # Profiling
        # TODO: Profile this on Raspberry Pi
        now1 = datetime.now(tz=zulu_time)

        # Parse the telegram as C1-type telegram
        t = C1Telegram(telegram)

        # Let OmniPower process it fully, including entering in log
        omnipower.process_telegram(t)

        # Profiling
        now2 = omnipower.measurement_log[-1].timestamp
        delta = (now2 - now1).microseconds

        print("Delay from start to timestamp {} ms".format(delta))

    # See items now stored in the log
    print(colored("Representation of entire measurement log:", 'red'))
    print(omnipower.measurement_log)

    print(colored("Representation of first object from log:", 'red'))
    print(omnipower.measurement_log[0])

    print(colored("Representation of last object from log:", 'red'))
    print(omnipower.measurement_log[len(omnipower.measurement_log)-1])

    print(colored("Dump to JSON:", 'red'))
    print(omnipower.dump_log_to_json())

    print(colored("Example of time with Zoneinfo:", 'red'))
    print(zulu_time_str(omnipower.measurement_log[0].timestamp))

    print(colored("Demonstrate corrupted telegram with failed CRC check:", 'red'))
    # Correct encrypted payload portion is 1dfbbd7871e6ec990f60ee940532c09e505bd4cac5728e
    # Changed last hex digit to f, so erroneously received 1dfbbd7871e6ec990f60ee940532c09e505bd4cac5728f
    t = C1Telegram(b'27442d2c5768663230028d206e90dd03201dfbbd7871e6ec990f60ee940532c09e505bd4cac5728f2864')
    omnipower.process_telegram(t)


if __name__ == "__main__":
    demo_0()
