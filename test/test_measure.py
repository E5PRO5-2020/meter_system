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

def test_MeterMeasure(MeasureFix, keys):

	# Load in fixture
	m1, m2, m3, m4, meterID, testdateTime = MeasureFix
	k1, k2, k3, k4 = keys

	# Test with fixture-values
	# Instantiate MeterMeasurement object and test __init__function
	omni_power_frame = MeterMeasurement(meterID, testdateTime)
	assert omni_power_frame.meter_id==meterID
	assert omni_power_frame.timestamp==testdateTime

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
	assert test_object["A+"]== {'unit': 'kWh', 'value': 7}
	assert test_object["A-"]== {'unit': 'kWh', 'value': 8}
	assert test_object["P+"]== {'unit': 'kW', 'value': 9}
	assert test_object["P-"]== {'unit': '', 'value': ""}

	# Remaining missed lines for MeterMeasurement-class are human readable functions

def test_OmniTest():
	omnipower = OmniPower()
	telegram = '27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e'.encode()
	tlg = C1Telegram(telegram)
	assert omnipower.is_this_my(tlg) == True
	output = omnipower.extract_measurement_frame(tlg)

	assert output == "[MeterMeasurement('32666857', 2020-10-25T12:37:45)]"
	assert omnipower.measurement_log[0] == "Meter ID: 32666857" \
										   "Timestamp: 2020-10-25" \
										   " 12:37:45.691804" \
										   "A+: 2.15 kWh" \
										   "A-: 0.0 kWh" \
										   "P+: 0.003 kW" \
										   "P-: 0.0 kW"

	# Long telegrams
	text = b'2d442d2c5768663230028d206461dd032038931d14b405536e0250592f8b908138d58602eca676ff79e0caf0b14d0e7d'
	telegram = C1Telegram(text)
	payload = omnipower.decrypt(telegram)[6:]
	assert payload == "b'0404d700000004843c00000000042b0300000004ab3c00000000'"
	result = omnipower.unpack_long_telegram_data(payload)
	assert result == "(215, 0, 3, 0)"

	# Short telegram
	text = b'27442D2C5768663230028D202E21870320D3A4F149B1B8F5783DF7434B8A66A55786499ABE7BAB59ffff'
	telegram = C1Telegram(text)
	test = omnipower.process_telegram(telegram)
	assert test == b'117079138c4491ce000000000000000300000000000000aaa'
	assert 1==2
