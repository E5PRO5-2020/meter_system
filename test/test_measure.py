
import pytest
from meter.MeterMeasurement import Measurement, MeterMeasurement
from meter.OmniPower import C1Telegram, OmniPower
from binascii import hexlify
from datetime import datetime
import json

# Setup fixture for Measurement class
@pytest.fixture()
def MeasureFix():
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
	k1 = "A+"
	k2 = "A-"
	k3 = "P+"
	k4 = "P-"
	return k1, k2, k3, k4

# Test for MeterMeasurement.Measure
def test_measure(MeasureFix):
	# Load in fixture
	m1, m2, m3, m4, meterID, testdatetime = MeasureFix
	# Test with fixture-values
	# assert Measurement.__repr__(m1)=="7 kWh"
	# assert Measurement.__repr__(m2)=="8 kWh"
	# assert Measurement.__repr__(m3)=="9 kW"
	# assert Measurement.__repr__(m4)==" "

	# print("dinmor")
	# assert Measurement.__iter__(m1)== (m1.value, m1.unit)
	# assert Measurement.__iter__(m2)== (m2.value, m2.unit)
	# assert Measurement.__iter__(m3)== (m3.value, m3.unit)
	# assert Measurement.__iter__(m4)== (m4.value, m4.unit)

def test_MeterMeasure(MeasureFix, keys):

	# Currently the def __repr__(self):-function is not tested in MeterMeasurement.py

	# Load in fixture
	m1, m2, m3, m4, meterID, testdateTime = MeasureFix
	k1, k2, k3, k4 = keys
	# Test with fixture-values
	# Instantiate MeterMeasurement object and add values
	omni_power_frame = MeterMeasurement(meterID, testdateTime)
	omni_power_frame.add_measurement(k1, m1)
	omni_power_frame.add_measurement(k2, m2)
	omni_power_frame.add_measurement(k3, m3)
	omni_power_frame.add_measurement(k4, m4)
	# Testing add_measurement
	assert omni_power_frame.measurements[k1].value == m1.value
	assert omni_power_frame.measurements[k1].unit == m1.unit

	assert omni_power_frame.measurements[k2].value == m2.value
	assert omni_power_frame.measurements[k2].unit == m2.unit

	assert omni_power_frame.measurements[k3].value == m3.value
	assert omni_power_frame.measurements[k3].unit == m3.unit

	assert omni_power_frame.measurements[k4].value == m4.value
	assert omni_power_frame.measurements[k4].unit == m4.unit

	assert omni_power_frame.timestamp == testdateTime


	# Test for bestemte properties!
	assert MeterMeasurement.as_dict(omni_power_frame)=="{'Timestamp:': '2020-10-20T12:46:35', " \
												"'Measurements': {" \
												"'P-': {'unit': ' ', 'value':  }, " \
												"'A+': {'unit': 'kWh', 'value': 2.15}, " \
												"'P+': {'unit': 'kW', 'value': 0.003}, " \
												"'A-': {'unit': 'kWh', 'value': 0.0}}, " \
												"'Meter ID: ': '32666857'}"

	assert MeterMeasurement.json_dump(omni_power_frame)=="{'Timestamp:': '2020-10-20T12:46:35', " \
												"'Measurements': {" \
												"'P-': {'unit': ' ', 'value':  }, " \
												"'A+': {'unit': 'kWh', 'value': 2.15}, " \
												"'P+': {'unit': 'kW', 'value': 0.003}, " \
												"'A-': {'unit': 'kWh', 'value': 0.0}}, " \
												"'Meter ID: ': '32666857'}"

#Setup test for OmniPower class
#@pytest.fixture()
#def OmniFix():
#	telegram =  '27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e'.encode()
#	return telegram

#def OmniTest(OmniFix):
#	telegram = OmniFix
	
	
