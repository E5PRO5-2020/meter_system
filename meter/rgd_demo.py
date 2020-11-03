"""
This file is a demo for RGD

Version 1: Demo of parsing short and long C1 telegrams for meeting 21 October 2020
Version 2: Demo of CRC16, timestamps, ell_sn and further exception handling for meeting 4 Nov 2020

Janus, October 2020
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
    # The last telegram is bad, and should be discarded silently
    telegrams = [b'27442D2C5768663230028D202E21870320D3A4F149B1B8F5783DF7434B8A66A55786499ABE7BAB59ffff',
                 b'27442d2c5768663230028d206360dd0320c42b87f46fc048d42498b44b5e34f083e93e6af16176313d9c',
                 b'2d442d2c5768663230028d206461dd032038931d14b405536e0250592f8b908138d58602eca676ff79e0caf0b14d0e7d',
                 b'27442d2c5768663230028d206562dd03200ac3aea1e613dd9af1a75c68cdedd5fdd2617c1e71a9d0b3b1',
                 b'2d442d2c5768663230028d206c81dd03202dcd10989cd870e4439ee09a309f7114681d40570623dfae7b3c6214679786',
                 b'27442d2c5768663230028d206e90dd03201dfbbd7871e6ec990f60ee940532c09e505bd4cac5728e2864',
                 b'xyz']

    # Process the telegrams
    print(colored("Start processing and profiling:", 'red'))
    for telegram in telegrams:
        # Profiling start
        # On Raspberry Pi 3b+ a single telegram takes about 900-1100 us (microsec)
        now1 = datetime.now(tz=zulu_time)

        try:
            # Parse the telegram as C1-type telegram
            # Could raise a TelegramParseException
            t = C1Telegram(telegram)

            # Let OmniPower process it fully, including entering in log
            # Could raise AesKeyException or CrcCheckException
            omnipower.process_telegram(t)

            # Profiling end, clock the new time and compute diff
            now2 = omnipower.measurement_log[-1].timestamp
            delta = (now2 - now1).microseconds
            print("Delay from start to timestamp {} µs".format(delta))

            # Output the SN field, for demo
            print(colored("SN-field parse demo:", 'red'))
            print(t.SN)

        except Exception as e:
            # Demo silently dropping bad telegrams
            # print(e)
            pass

    # If any items in the log, let's see them!
    if len(omnipower.measurement_log) > 0:
        # See items now stored in the log
        print(colored("Representation of entire measurement log:", 'red'))
        print(omnipower.measurement_log)

        print(colored("Representation of first object from log:", 'red'))
        print(omnipower.measurement_log[0])

        print(colored("Representation of last object from log:", 'red'))
        print(omnipower.measurement_log[-1])

        print(colored("Dump to JSON string:", 'red'))
        print(omnipower.dump_log_to_json())

        print(colored("Example of time with Zone info:", 'red'))
        print(zulu_time_str(omnipower.measurement_log[0].timestamp))

    print(colored("Demo corrupted telegram with failed CRC check and raised exception:", 'red'))
    # Correct encrypted payload portion is 0x1dfbbd7871e6ec990f60ee940532c09e505bd4cac5728e
    # Changed last hex digit to 0xf, so erroneously received 0x1dfbbd7871e6ec990f60ee940532c09e505bd4cac5728f
    # Last 4 hex digits 0x2864 are CRC16 from IM871-A and are not relevant here
    t = C1Telegram(b'27442d2c5768663230028d206e90dd03201dfbbd7871e6ec990f60ee940532c09e505bd4cac5728f2864')
    omnipower.process_telegram(t)

    print(colored("Demo bad telegram and raised exception:", 'red'))
    try:
        t = C1Telegram(b'bad')
        omnipower.process_telegram(t)
    except Exception as e:
        print(e)


    print(colored("Demo bad AES key and raised exception:", 'red'))
    omnipower.AES_key = "1234"
    t = C1Telegram(telegrams[0])
    omnipower.process_telegram(t)


if __name__ == "__main__":
    demo_0()
