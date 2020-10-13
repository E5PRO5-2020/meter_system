"""
This module implements classes for generic measurements taken from a meter
"""

import os
from collections import OrderedDict
import json
from datetime import datetime


class Measurement:
    """
    A single measurement of a physical quantity consisting of a value and a unit
    """
    def __init__(self, value, unit):

        # A numeric value (float)
        self.value = value

        # A string SI unit
        self.unit = unit

    def __repr__(self):
        return str(self.value) + " " + self.unit

    def __iter__(self):
        return self.value, self.unit


class MeterMeasurement:
    """
    A single measurement collection based on one frame from the meter
    Will contain multiple measurements of physical quantities taken at the same time
    """

    def __init__(self, meter_id, timestamp):
        """
        Make a new measurement collection
        :param meter_id: ID of the meter taking the measurement
        :param timestamp: Time when the measurement was received, must be Python datetime object
        """
        self.meter_id = meter_id
        self.timestamp = timestamp
        self.Measurements = OrderedDict()

    def add_measurement(self, name, measurement):
        """
        Store a new measurement in the collection
        :param name: Human readable field name
        :param measurement: The measurement object of type Measurement
        :return: Void
        """

        # Insert new pair into ordered dict. The name is human readable
        self.Measurements.update({name: measurement})

    def __repr__(self):
        """
        Human readable representation of a measurement collection
        :return:
        """
        # Build the header
        header = "Meter ID: " + str(self.meter_id) + os.linesep
        header = header + "Timestamp: " + str(self.timestamp) + os.linesep

        # Iterate over the measurements in the collection, making a combined string
        text = [k + ": " + str(v.value) + " " + str(v.unit) for k, v in self.Measurements.items()]
        text = os.linesep.join(text)

        # Return human readable combined string
        return header + text

    def as_dict(self):
        """
        Serializes and dumps the Measurement object as a dict object.
        Make an object similar to
        {
            "Meter ID: ": "3232323",
            "Timestamp:": "2020-10-13T17:36:53",
            "Measurements": {
                "A+": {
                    "unit": "kWh",
                    "value": 7
                },
                "A-": {
                    "unit": "kWh",
                    "value": 8
                },
                "P+": {
                    "unit": "kW",
                    "value": 9
                },
                "P-": {
                    "unit": "kW",
                    "value": 10
                }
            }
        }
        :return: dict
        """
        # Build object, and dump timestamp using ISO8601, https://en.wikipedia.org/wiki/ISO_8601
        obj = {
            'Meter ID: ': str(self.meter_id),
            'Timestamp:': datetime.strftime(self.timestamp, '%Y-%m-%dT%H:%M:%S'),
            'Measurements': {}
        }
        # Insert all the measurements
        [obj['Measurements'].update({key: {'value': val.value, 'unit': val.unit}})
         for key, val in self.Measurements.items()]

        return obj

    def json_dump(self):
        """
        Returns a JSON string
        :return:
        """
        obj = self.as_dict()
        return json.dumps(obj)



# Only run self-tests if started from terminal, not when imported
if __name__ == '__main__':
    test0()
