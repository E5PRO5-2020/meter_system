import pytest
from meter.MeterMeasurement import Measurement, MeterMeasurement
from meter.OmniPower import C1Telegram, OmniPower
from utils.timezone import zulu_time_str
# Includes from other files
from datetime import datetime
import json


@pytest.fixture()
def omnipower_setup():
    """
	Sets up an omnipower test fixture with at least one telegram stored in log
	Janus, 26 Oct 2020
	"""

    # Maybe not a good idea to do default initialization here,
    # as we are likely to remove deafult values in the future
    omnipower = OmniPower()

    # List of telegrams to include in the log
    telegrams = [b'27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e',
                 b'2d442d2c5768663230028d206c81dd03202dcd10989cd870e4439ee09a309f7114681d40570623dfae7b3c6214679786']

    # Process telegrams
    for telegram in telegrams:
        omnipower.process_telegram(C1Telegram(telegram))

    # Only return the finished fixture
    return omnipower


def test_OmniTest():
    """
	Test the OmniPower class functionality (not yet fully implemented)
	Jakob, 27/10-2020
	"""
    omnipower = OmniPower()
    telegram = '27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e'.encode()
    tlg = C1Telegram(telegram)
    assert omnipower.is_this_my(tlg) == True

    # Long telegrams
    long_telegram = b'2d442d2c5768663230028d206461dd032038931d14b405536e0250592f8b908138d58602eca676ff79e0caf0b14d0e7d'
    longC1 = C1Telegram(long_telegram)
    payload = omnipower.decrypt(longC1)[6:]
    assert payload == b'0404d700000004843c00000000042b0300000004ab3c00000000'
    result = omnipower.unpack_long_telegram_data(payload)
    assert result == (215, 0, 3, 0)

    # Short telegram
    short_telegram = b'27442D2C5768663230028D202E21870320D3A4F149B1B8F5783DF7434B8A66A55786499ABE7BAB59ffff'
    shortC1 = C1Telegram(short_telegram)
    assert omnipower.process_telegram(shortC1) == True

    # Missing line 241
    # if not meter.AES_key:
    #	return False

    # Missing line 247-253
    # Exception handling ( Do we want to test this? )

    # Missing Line 304 - Exception handling of decrypt()

    # Missing line 391 - extract_measurement_frame() - if not telegram.decrypted: return false

    # Missing line 396 - unpack_long_telegram(telegram.decrypted)
    assert omnipower.process_telegram(shortC1) == True

    # omnipower.extract_measurement_frame(shortC1)


def test_json_full_log(omnipower_setup):
    """
	Test that a full log of MeterMeasurement objects dumped to JSON can all be recovered correctly
	Janus, 26 Oct 2020
	"""

    # Set up fixture
    omnipower = omnipower_setup

    # Attempt to dump a list of MeterMeasurement objects to JSON
    ref_obj = omnipower.measurement_log

    # The resulting JSON-formatted string
    test_json_str = omnipower.dump_log_to_json()

    # Recover an object from JSON, this will be a full dict, no guaranteed ordering
    json_recovered_dict = json.loads(test_json_str)

    # loop over entire measurement log, n = 0,..., N-1, log_item = MeterMeasurement(...)
    # to ensure all items are included
    for n, log_item in enumerate(ref_obj):

        # Confirm metadata identical for nth object
        assert json_recovered_dict[str(n)]['MeterID'] == log_item.meter_id
        assert json_recovered_dict[str(n)]['Timestamp'] == zulu_time_str(log_item.timestamp)

        # Confirm measurements identical for nth object
        # Looks up e.g. item labelled '0' in the JSON dump anc compares to 0th item from actual log
        # Then proceeds to loop over each measurement, e.g. "A+", "A-", etc...
        for measurement_name, measurement_obj in json_recovered_dict[str(n)]['Measurements'].items():
            assert measurement_obj['value'] == ref_obj[n].measurements[measurement_name].value
            assert measurement_obj['unit'] == ref_obj[n].measurements[measurement_name].unit
