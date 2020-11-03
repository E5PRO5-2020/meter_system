import pytest
from meter.MeterMeasurement import Measurement, MeterMeasurement
from meter.OmniPower import C1Telegram, OmniPower, TelegramParseException, AesKeyException, CrcCheckException
from utils.timezone import zulu_time_str
# Includes from other files
from datetime import datetime
import json


@pytest.fixture()
def omnipower_base():
    """
    Creates an good OmniPower object with no data in log
    """

    omnipower = OmniPower(name='Kamstrup OmniPower one-phase',
                          meter_id='32666857',
                          manufacturer_id='2C2D',
                          medium='02',
                          version='30',
                          aes_key='9A25139E3244CC2E391A8EF6B915B697')
    return omnipower


@pytest.fixture()
def omnipower_setup(omnipower_base):
    """
    Sets up an omnipower test fixture with at least one telegram stored in log
    Janus, 26 Oct 2020
    """

    omnipower = omnipower_base

    # List of telegrams to include in the log
    telegrams = [b'27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e',
                 b'2d442d2c5768663230028d206c81dd03202dcd10989cd870e4439ee09a309f7114681d40570623dfae7b3c6214679786']

    # Process telegrams
    for telegram in telegrams:
        omnipower.process_telegram(C1Telegram(telegram))

    # Only return the finished fixture
    return omnipower


@pytest.fixture()
def omnipower_with_no_aes_key(omnipower_base):
    """
    Creates a good OmniPower object with empty AES key
    """

    omnipower = omnipower_base
    omnipower.AES_key = ""
    return omnipower


@pytest.fixture()
def bad_telegrams_list():
    """
    Sets up a list of bad telegrams that must cause exceptions at various places
    """

    bad_telegrams = [b'xyz', b'', ""]
    return bad_telegrams


@pytest.fixture()
def good_telegrams_list():
    """
    Sets up a list of bad telegrams that must cause exceptions at various places
    """

    good_telegrams = [b'27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e',
                      b'2d442d2c5768663230028d206461dd032038931d14b405536e0250592f8b908138d58602eca676ff79e0caf0b14d0e7d']
    return good_telegrams


@pytest.fixture()
def bad_payload_list():
    # Mangled telegram
    # Correct encrypted payload portion is 0x1dfbbd7871e6ec990f60ee940532c09e505bd4cac5728e
    # Changed last hex digit to 0xf, so erroneously received 0x1dfbbd7871e6ec990f60ee940532c09e505bd4cac5728f
    # Last 4 hex digits 0x2864 are CRC16 from IM871-A and are not relevant here

    bad_payload_tlg = C1Telegram(
        b'27442d2c5768663230028d206e90dd03201dfbbd7871e6ec990f60ee940532c09e505bd4cac5728f2864')

    return [bad_payload_tlg]


def test_OmniTest(omnipower_base):
    """
    Test the OmniPower class functionality (not yet fully implemented)
    Jakob, 27/10-2020
    """

    omnipower = omnipower_base
    telegram = '27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e'.encode()
    tlg = C1Telegram(telegram)
    assert omnipower.is_this_my(tlg) == True

    # Long telegrams
    long_telegram = b'2d442d2c5768663230028d206461dd032038931d14b405536e0250592f8b908138d58602eca676ff79e0caf0b14d0e7d'
    longC1 = C1Telegram(long_telegram)
    assert omnipower.process_telegram(longC1) == True

    # Short telegram
    short_telegram = b'27442D2C5768663230028D202E21870320D3A4F149B1B8F5783DF7434B8A66A55786499ABE7BAB59ffff'
    shortC1 = C1Telegram(short_telegram)
    assert omnipower.process_telegram(shortC1) == True

    notmy_short_telegram = b'27442D2C5768663130028D202E21870320D3A4F149B1B8F5783DF7434B8A66A55786499ABE7BAB59ffff'
    notmy_short_c1 = C1Telegram(notmy_short_telegram)
    assert omnipower.is_this_my(notmy_short_c1) == False

    omnipower.AES_key = None
    assert shortC1.decrypt_using(omnipower) == False

    # Missing line 299-302 - Raise exception for upstream handling. and propagate the existing exception

    # Missing line 330-331 - AES key exception
    # Implemented, but somehow coverage says it's missing

    # Missing line 334-335 - CRC Check fail
    # Implemented

    # Missing line 418 - AesKeyException("Bad key length")
    # Tested alongside line 330-331

    # Missing line 486 - if.not telegramdecrypted (Not implemented yet)
    #

    # Missing line 499 - Length of telegram check (Not implemented yet)

    # Missing line 522-524 - exception add_measurement

    # Missing line 542-545 - is_this_my() false

    # Missing line 565-568 - AesKeyException

    # Missing line 572 - AesKeyException

    # Missing line 580-583 - TelegramParseException

    # Missing line 587 - TelegramParseException

    # Missing line 391 - extract_measurement_frame() - if not telegram.decrypted: return false
    # Implementation is changing on this part. Do not test at the moment!

    # Missing line 431-438 - Exception handling of CRC check

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


def test_c1telegram_must_raise_exception(bad_telegrams_list):
    """
    Test that C1 Telegram initialized with bad bytestream raises exception
    """

    bad_data = bad_telegrams_list

    for test_val in bad_data:
        with pytest.raises(TelegramParseException, match="Failed to parse") as exc_info:
            obj = C1Telegram(test_val)


def test_decrypt_must_raise_aes_key_error(omnipower_with_no_aes_key, good_telegrams_list):
    """
    To be
    """

    # Fixtures
    omnipower = omnipower_with_no_aes_key
    good_data = good_telegrams_list

    # Set a bad key
    omnipower.AES_key = b'badkey'

    # Make C1 telegrams with known good data
    c1_tlgs = [C1Telegram(t) for t in good_data]

    # Expect that AesKeyException is raised
    with pytest.raises(AesKeyException):
        omnipower.decrypt(c1_tlgs[0])



def test_decrypt_must_raise_crc_check_error(omnipower_base, bad_payload_list):
    """
    To be
    """

    omnipower = omnipower_base

    # Get a C1Telegram with mangled payload
    bad_payload = bad_payload_list[0]

    # Expect that CrcCheckException is raised
    with pytest.raises(CrcCheckException):
        omnipower.decrypt(bad_payload)


def test_decrypt_using_must_return_false_for_bad_input(omnipower_with_no_aes_key, good_telegrams_list):
    """
    ERROR PART 2 DOES NOT WORK CORRECTLY
    Test strategy:
    1. Good telegram + bad AES key -> AesKeyException
    2. Bad payload + good AES key -> CrcCheckException
    """

    # Fixtures
    omnipower_nokey = omnipower_with_no_aes_key
    good_data = good_telegrams_list

    ####
    # Test part 1.
    # Set a bad key
    omnipower_nokey.AES_key = b'badkey'

    # Make C1 telegrams with known good data
    c1_tlgs = [C1Telegram(t) for t in good_data]

    # Must return False due to caught AesKeyException
    for t in c1_tlgs:
        assert t.decrypt_using(omnipower_nokey) == False


def test_decrypt_using_must_return_false_for_bad_input(omnipower_base, bad_payload_list):

    ####
    # Test part 2
    # Get object with good key
    omnipower_goodkey = omnipower_base

    # Get a C1Telegram with mangled payload
    bad_payload = bad_payload_list[0]

    # Function must return False due to caught CrcKeyException
    assert bad_payload.decrypt_using(omnipower_goodkey) == False

def test_extract_measurement_frame_fail(omnipower_base, good_telegrams_list):
    """
    Aloha
    """
    omnipower = omnipower_base
    c1_tlgs = [C1Telegram(t) for t in good_telegrams_list]

    # Expect that TelegramParseException is raised
    #with pytest.raises(TelegramParseException):
    #    omnipower.extract_measurement_frame(c1_tlgs[0])
    # Janus hjælp mig! eller skriv noget bedre kode!
    assert omnipower.extract_measurement_frame(c1_tlgs[0]).measurements == ''
