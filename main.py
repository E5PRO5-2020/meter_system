"""
This main module is only for demo'ing the implemented classes and testing their function.
"""
from binascii import hexlify
from datetime import datetime
import json

# Use our implemented classes
from OmniPower.MeterMeasurement import Measurement, MeterMeasurement
from OmniPower.OmniPower import C1Telegram, OmniPower


def test0():
    """
    Test the implementation of the Measurement and MeterMeasurement types
    """

    # Just some generic data to see how these classes work
    omni_power_frame = MeterMeasurement("3232323", datetime.now())

    m1 = Measurement(7, "kWh")
    print(str(m1))

    omni_power_frame.add_measurement("A+", m1)
    print([omni_power_frame])

    m2 = Measurement(8, "kWh")
    omni_power_frame.add_measurement("A-", m2)

    m3 = Measurement(9, "kW")
    omni_power_frame.add_measurement("P+", m3)

    m4 = Measurement(10, "kW")
    omni_power_frame.add_measurement("P-", m4)

    print(omni_power_frame)

    # Demo of dumping object to JSON object that can be saved in a file
    jsdump = omni_power_frame.json_dump()

    # Demo of loading object
    my_obj = json.loads(jsdump)
    print(my_obj['Measurements'])


def test1():
    """
    Self-test to demo stepwise functions for OmniPower and C1Telegram
    :return:
    """

    # Make new omnipower meter with default values (our meter)
    omnipower = OmniPower()

    # Receive new telegram as byte-encoded, this one is the latest from Steffen's and Thomas's list
    telegram = '27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e'.encode()

    # Parse telegram as C1-type telegram
    tlg = C1Telegram(telegram)

    # Confirm that the telegram belongs to this meter
    check = omnipower.is_this_my(tlg)
    print("This telegram comes from {}? {}".format(omnipower.name, check))

    # See the encrypted part of the telegram
    print("Encrypted message: {}".format(tlg.encrypted))

    # See the decryption prefix
    print("Encryption prefix: {}".format(hexlify(tlg.prefix)))

    # Decrypt the data, there are two ways
    # -> First way, via the meter. This only returns the decoded message
    plaintext = omnipower.decrypt(tlg)
    print("Decrypted message via Meter: {}".format(plaintext))

    # -> Second way, via the telegram, this saves the value inside the telegram
    tlg.decrypt_using(omnipower)
    print("Decrypted message via Telegram: {}".format(tlg.decrypted))

    # Get a set of measurements
    meas = omnipower.extract_measurement_frame(tlg)
    print(meas)

    # Add the measurement frame to the meter log
    omnipower.add_measurement_to_log(meas)

    # See what's in the log
    print("Measurement log for {}:".format(omnipower.name))
    print("Printing full log overview")
    print(omnipower.measurement_log)
    print("Printing first element")
    print(omnipower.measurement_log[0])


def test2():
    """
    Self test to test automatic processing of multiple streamed telegrams
    :return:
    """

    # Make new omnipower meter with default values (our meter)
    omnipower = OmniPower()

    # Receive a bunch of telegrams from Steffen's and Thomas's list (UTF-8 strings)
    telegrams = ['27442d2c5768663230028d206360dd0320c42b87f46fc048d42498b44b5e34f083e93e6af16176313d9c',
                 '27442d2c5768663230028d206562dd03200ac3aea1e613dd9af1a75c68cdedd5fdd2617c1e71a9d0b3b1',
                 '27442d2c5768663230028d206663dd0320183edb492079b22095afcd9c7721b64c7cbffb1b892e9c832d',
                 '27442d2c5768663230028d2078b2dd0320677e926ba3cb04597a0ac9f513afc5c48936f442d3584cc090',
                 '27442d2c5768663230028d208940da03201e39769c3a1158e6368d765a076fbe7755bb401a34dbceca57',
                 '27442d2c5768663230028d208a41da0320736984fdd8de6f6e8a3902874130f2f69ad15a84ceb49e7238',
                 '27442d2c5768663230028d208b42da032083e4987384543125fcb8aea6714d7554c71a4387afd260a91d',
                 '27442d2c5768663230028d208d10de0320eb9f476e9e4d8e82b16d9b9bc46dbf514276f576afba7baa30',
                 '27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e']

    # Encode them all as ascii strings (might not be needed with IM871A interface)
    telegrams = [t.encode() for t in telegrams]

    # Process the telegrams
    for telegram in telegrams:
        # Parse the telegram as C1-type telegram
        tlg = C1Telegram(telegram)

        # Let OmniPower process it fully, including entering in log
        omnipower.process_telegram(tlg)

    # Check what we have in the log now
    # print(omnipower.measurement_log)

    # Return the meter including all the measurements
    return omnipower


def test3():
    """
    This tests the ability to handle long telegrams
    """

    text = b'2d442d2c5768663230028d206461dd032038931d14b405536e0250592f8b908138d58602eca676ff79e0caf0b14d0e7d'
    omnipower = OmniPower()
    telegram = C1Telegram(text)
    payload = omnipower.decrypt(telegram)[6:]
    print(payload)
    result = omnipower.unpack_long_telegram_data(payload)
    print(result)


def test4():
    # Make new omnipower meter with default values (our meter)
    omnipower = OmniPower()

    # Receive a bunch of mixed telegrams from Steffen's and Thomas's list (UTF-8 strings)
    telegrams = [b'27442D2C5768663230028D202E21870320D3A4F149B1B8F5783DF7434B8A66A55786499ABE7BAB59ffff',
                 b'27442d2c5768663230028d206360dd0320c42b87f46fc048d42498b44b5e34f083e93e6af16176313d9c',
                 b'2d442d2c5768663230028d206461dd032038931d14b405536e0250592f8b908138d58602eca676ff79e0caf0b14d0e7d',
                 b'27442d2c5768663230028d206562dd03200ac3aea1e613dd9af1a75c68cdedd5fdd2617c1e71a9d0b3b1',
                 b'2d442d2c5768663230028d206c81dd03202dcd10989cd870e4439ee09a309f7114681d40570623dfae7b3c6214679786',
                 b'27442d2c5768663230028d206e90dd03201dfbbd7871e6ec990f60ee940532c09e505bd4cac5728e2864']

    # Process the telegrams
    for telegram in telegrams:
        # Parse the telegram as C1-type telegram
        tlg = C1Telegram(telegram)

        # Let OmniPower process it fully, including entering in log
        omnipower.process_telegram(tlg)
        # print(tlg.decrypted)

    print(omnipower.dump_log_to_json())
    # print(omnipower.measurement_log[2])
    #print(omnipower.measurement_log[2])


# Only run self-tests if started from terminal, not when imported
if __name__ == '__main__':
    # mypy can be used to test types, i.e. run a type-checker like static type
    # checking in C / C++ / Java. Errors are not necessarily a problem, but
    # shows where we could have issues.

    # Run demo 0
    # test0()

    # Run demo 1
    # test1()

    # Run demo 2
    # omnipower_meter = test2()

    # Run demo 3
    # test3()

    # Run demo 4
    # Test ability to handle multiple mixed telegrams
    test4()

    # Output from the log
    # print("What is the A+ measurement?")
    #print(omnipower_meter.measurement_log[1].Measurements['A+'])

    # Try to dump all data to a JSON string. This emulates saving to a file
    # logobj = omnipower_meter.dump_log_to_json()

    # Try to parse the JSON (like reading from the file) and check the A+ measurement for the last object
    # print(json.loads(logobj)['8'])

    # omni_power_frame = MeterMeasurement('777', datetime.now())
    # m1 = Measurement(7, 'kWh')
    # omni_power_frame.add_measurement("A+", m1)
    # print(omni_power_frame.Measurements['A+'].value == m1.value)





