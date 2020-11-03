"""
Tests for the functionality of MeterMeasurement implementation.

"""

# Includes from standard library
import pytest
from datetime import datetime
import json

# Include our objects to be tested
from meter.MeterMeasurement import Measurement, MeterMeasurement
from meter.OmniPower import C1Telegram, OmniPower
from utils.timezone import zulu_time_str, ZuluTime


@pytest.fixture
def initialized_measurement_frame():
    """
    Sets up a measurement frame with ID and fixed Zulu timestamp, but no data.
    """
    zulu_time = ZuluTime()
    return MeterMeasurement("32666857", datetime(year=2020,
                                                 month=9,
                                                 day=1,
                                                 hour=12,
                                                 minute=30,
                                                 second=0,
                                                 microsecond=0,
                                                 tzinfo=zulu_time))


# Setup fixture for Measurement class
@pytest.fixture()
def MeasureFix():
    """
    Setup-fixture for Measurement-class
    """
    m1 = Measurement(7, "kWh")
    m2 = Measurement(8, "kWh")
    m3 = Measurement(9, "kW")
    m4 = Measurement("", "")

    meterID = "3232323"
    testdatetime = datetime(2020, 10, 15, 15, 12, 30, 262939)
    return m1, m2, m3, m4, meterID, testdatetime


# Setup fixture for keys
@pytest.fixture()
def keys():
    """
    Setup-fixture for keys
    """
    k1 = "A+"
    k2 = "A-"
    k3 = "P+"
    k4 = "P-"
    return k1, k2, k3, k4


@pytest.fixture()
def omnipower_setup():
    """
    Sets up an omnipower test fixture with at least one telegram stored in log.
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


def test_MeterMeasure(MeasureFix, keys):
    """
	Test the MeterMeasurement class functionality
	Jakob, 27/10-2020
	"""
    # Load in fixture
    m1, m2, m3, m4, meterID, testdateTime = MeasureFix
    k1, k2, k3, k4 = keys

    # Test with fixture-values
    # Instantiate MeterMeasurement object and test __init__function
    omni_power_frame = MeterMeasurement(meterID, testdateTime)
    assert omni_power_frame.meter_id == meterID
    assert omni_power_frame.timestamp == testdateTime

    # Adding measurements and asserting result
    omni_power_frame.add_measurement(k1, m1)
    omni_power_frame.add_measurement(k2, m2)
    omni_power_frame.add_measurement(k3, m3)
    omni_power_frame.add_measurement(k4, m4)
    assert omni_power_frame.measurements[k1].value == m1.value
    assert omni_power_frame.measurements[k1].unit == m1.unit
    assert omni_power_frame.measurements[k2].value == m2.value
    assert omni_power_frame.measurements[k2].unit == m2.unit
    assert omni_power_frame.measurements[k3].value == m3.value
    assert omni_power_frame.measurements[k3].unit == m3.unit
    assert omni_power_frame.measurements[k4].value == m4.value
    assert omni_power_frame.measurements[k4].unit == m4.unit
    assert omni_power_frame.timestamp == testdateTime

    # Testing as.dict()
    test_object = omni_power_frame.as_dict()["Measurements"]
    assert test_object["A+"] == {'unit': 'kWh', 'value': 7}
    assert test_object["A-"] == {'unit': 'kWh', 'value': 8}
    assert test_object["P+"] == {'unit': 'kW', 'value': 9}
    assert test_object["P-"] == {'unit': '', 'value': ""}


# Remaining missed lines for MeterMeasurement-class are human readable functions

def test_json_single_measurement(omnipower_setup):
    """
	Test that a single MeterMeasurement dumped to JSON can be recovered correctly.
	"""

    # Set up fixture
    omnipower = omnipower_setup

    # Attempt to dump a single MeterMeasurement to JSON
    # The MeterMeasurement to dump, just use first object in log
    ref_obj = omnipower.measurement_log[0]

    # The resulting JSON-formatted string
    test_json_str = ref_obj.json_dump()

    # Recover an object from JSON, this will be a full dict, no guaranteed ordering
    json_recovered_dict = json.loads(test_json_str)

    # First, confirm that saved metadata is similar
    assert json_recovered_dict['MeterID'] == ref_obj.meter_id
    assert json_recovered_dict['Timestamp'] == zulu_time_str(ref_obj.timestamp)

    # Loop over measurements in the recovered object to compare all
    for measurement_name, measurement_obj in json_recovered_dict['Measurements'].items():
        assert measurement_obj['value'] == ref_obj.measurements[measurement_name].value
        assert measurement_obj['unit'] == ref_obj.measurements[measurement_name].unit


def test_meter_measurement_returns_empty(initialized_measurement_frame):
    """
    A MeterMeasurement with no data added must return True on is_empty() method.
    """

    frame = initialized_measurement_frame
    assert frame.is_empty()
