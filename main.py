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

    omni_power_meas = MeterMeasurement("3232323", datetime.now())
    m1 = Measurement(7, "kWh")
    omni_power_meas.add_measurement("A+", m1)

    m2 = Measurement(8, "kWh")
    omni_power_meas.add_measurement("A-", m2)

    m3 = Measurement(9, "kW")
    omni_power_meas.add_measurement("P+", m3)

    m4 = Measurement(10, "kW")
    omni_power_meas.add_measurement("P-", m4)
    print(omni_power_meas)

    # Demo of dumping object to JSON object that can be saved in a file
    jsdump = omni_power_meas.json_dump()

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
    print(omnipower.measurement_log)


def test2():
    """
    Self test to test automatic processing of multiple streamed telegrams
    :return:
    """

    # Make new omnipower meter with default values (our meter)
    omnipower = OmniPower()

    # Receive a bunch of telegrams from Steffen's and Thomas's list
    telegrams = ['27442d2c5768663230028d206360dd0320c42b87f46fc048d42498b44b5e34f083e93e6af16176313d9c',
                 '27442d2c5768663230028d206562dd03200ac3aea1e613dd9af1a75c68cdedd5fdd2617c1e71a9d0b3b1',
                 '27442d2c5768663230028d206663dd0320183edb492079b22095afcd9c7721b64c7cbffb1b892e9c832d',
                 '27442d2c5768663230028d2078b2dd0320677e926ba3cb04597a0ac9f513afc5c48936f442d3584cc090',
                 '27442d2c5768663230028d208940da03201e39769c3a1158e6368d765a076fbe7755bb401a34dbceca57',
                 '27442d2c5768663230028d208a41da0320736984fdd8de6f6e8a3902874130f2f69ad15a84ceb49e7238',
                 '27442d2c5768663230028d208b42da032083e4987384543125fcb8aea6714d7554c71a4387afd260a91d',
                 '27442d2c5768663230028d208d10de0320eb9f476e9e4d8e82b16d9b9bc46dbf514276f576afba7baa30',
                 '27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e']

    # Process the telegrams
    for telegram in telegrams:
        # Parse the telegram as C1-type telegram
        tlg = C1Telegram(telegram.encode())

        # Let OmniPower process it fully, including entering in log
        omnipower.process_telegram(tlg)

    # Check what we have in the log now
    # print(omnipower.measurement_log)

    return omnipower


# Only run self-tests if started from terminal, not when imported
if __name__ == '__main__':
    # Run demo 0
    test0()

    # Run demo 1
    test1()

    # Run demo 2
    omnipower_meter = test2()

    # Output the log
    # print(omnipower.measurement_log)

    # Try to dump all data to a JSON string. This emulates saving to a file
    logobj = omnipower_meter.dump_log_to_json()

    # Try to parse the JSON (like reading from the file) and check the A+ measurement for the last object
    print(json.loads(logobj)['8'])
