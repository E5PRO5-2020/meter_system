import pytest
from OmniPower.MeterMeasurement import Measurement, MeterMeasurement
from OmniPower.OmniPower import C1Telegram, OmniPower
from binascii import hexlify
from datetime import datetime
import json

# Setup fixture for Measurement class
@pytest.fixture()
def MeasureFix():
	m1 = Measurement(7, "kWh")
	m2 = Measurement(8, "kWh")
	m3 = Measurement(9, "kW")
	m4 = Measurement(10, "kW")
	m5 = Measurement(10000, "MWh")
	m6 = Measurement("abcd", "123")
	meterID = "3232323"
	testTime = (2020, 10, 15, 15, 12, 30, 262939)
	return m1, m2, m3, m4, m5, m6, meterID, testTime

@pytest.fixture()
def keys():
	k1 = "A+"
	k2 = "A-"
	k3 = "P+"
	k4 = "P-"
	return k1, k2, k3, k4


def test_measure(MeasureFix):
	# Load in fixture
	m1, m2, m3, m4, m5, m6, meterID, testTime = MeasureFix
	# Test with fixture-values
	assert Measurement.__repr__(m1)=="7 kWh"
	assert Measurement.__repr__(m2)=="8 kWh"
	assert Measurement.__repr__(m3)=="9 kW"
	assert Measurement.__repr__(m4)=="10 kW"
	assert Measurement.__repr__(m5)=="10000 MWh"
	assert Measurement.__repr__(m6)=="abcd 123"

	assert Measurement.__iter__(m1)== (m1.value, m1.unit)
	assert Measurement.__iter__(m2)== (m2.value, m2.unit)
	assert Measurement.__iter__(m3)== (m3.value, m3.unit)
	assert Measurement.__iter__(m4)== (m4.value, m4.unit)
	assert Measurement.__iter__(m5)== (m5.value, m5.unit)
	assert Measurement.__iter__(m6)== (m6.value, m6.unit)





def test_MeterMeasure(MeasureFix, keys):
	# Load in fixture
	m1, m2, m3, m4, m5, m6, meterID, testTime = MeasureFix
	k1, k2, k3, k4 = keys
	# Test with fixture-values
	# Instantiate MeterMeasurement object and add values
	omni_power_frame = MeterMeasurement(meterID, testTime)
	omni_power_frame.add_measurement(k1, m1)
	omni_power_frame.add_measurement(k2, m2)
	omni_power_frame.add_measurement(k3, m3)
	omni_power_frame.add_measurement(k4, m4)
	# Testing add_measurement
	assert omni_power_frame.Measurements[k1].value == m1.value
	assert omni_power_frame.Measurements[k1].unit == m1.unit

	assert omni_power_frame.Measurements[k2].value == m2.value
	assert omni_power_frame.Measurements[k2].unit == m2.unit

	assert omni_power_frame.Measurements[k3].value == m3.value
	assert omni_power_frame.Measurements[k3].unit == m3.unit

	assert omni_power_frame.Measurements[k4].value == m4.value
	assert omni_power_frame.Measurements[k4].unit == m4.unit

	assert omni_power_frame.timestamp == testTime
#Setup test for OmniPower class
#@pytest.fixture()
#def OmniFix():
#	telegram =  '27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e'.encode()
#	return telegram

#def OmniTest(OmniFix):
#	telegram = OmniFix


