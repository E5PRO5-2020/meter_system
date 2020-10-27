import pytest
from meter.MeterMeasurement import Measurement, MeterMeasurement
from meter.OmniPower import C1Telegram, OmniPower
from utils.timezone import zulu_time_str

# Includes from other files
from datetime import datetime
import json
from binascii import hexlify, unhexlify
from struct import *
from Crypto.Cipher import AES
from Crypto.Util import Counter
import json
import re
from typing import List, Tuple


# Setup fixture for Measurement class
@pytest.fixture()
def MeasureFix():
    m1 = Measurement(7, "kWh")
    m2 = Measurement(8, "kWh")
    m3 = Measurement(9, "kW")
    m4 = Measurement("", "")

    MeterID = "3232323"
    test_datetime = datetime(2020, 10, 15, 15, 12, 30, 262939)
    return m1, m2, m3, m4, MeterID, test_datetime


# Setup fixture for keys
@pytest.fixture()
def keys():
    k1 = "A+"
    k2 = "A-"
    k3 = "P+"
    k4 = "P-"
    return k1, k2, k3, k4

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
	telegrams = [b'27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e']
	#b'2d442d2c5768663230028d206c81dd03202dcd10989cd870e4439ee09a309f7114681d40570623dfae7b3c6214679786'
	# Process telegrams
	for telegram in telegrams:
		omnipower.process_telegram(C1Telegram(telegram))

	# Only return the finished fixture
	return omnipower

def test_MeterMeasure(MeasureFix, keys):
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

    # Testing as.dict() (make dynamic at some point)
    test_object = omni_power_frame.as_dict()["Measurements"]
    assert test_object["A+"] == {'unit': 'kWh', 'value': 7}
    assert test_object["A-"] == {'unit': 'kWh', 'value': 8}
    assert test_object["P+"] == {'unit': 'kW', 'value': 9}
    assert test_object["P-"] == {'unit': '', 'value': ""}

    # Testing json_dump() (make dynamic at some point)
    jsdump = omni_power_frame.json_dump()
    my_obj = json.loads(jsdump)
    assert my_obj == {'Timestamp:': '2020-10-15T15:12:30Z',
                      'Meter ID: ': '3232323',
                      'Measurements':
                          {'A+': {'unit': 'kWh', 'value': 7},
                           'A-': {'unit': 'kWh', 'value': 8},
                           'P+': {'unit': 'kW', 'value': 9},
                           'P-': {'unit': '', 'value': ''}}}

# Remaining missed lines for MeterMeasurement-class are human readable functions

def test_json_single_measurement(omnipower_setup):
	"""
	Test that a single MeterMeasurement dumped to JSON can be recovered correctly
	Janus, 26 Oct 2020
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