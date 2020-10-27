"""
Generic class for measurements and measurement frames
*****************************************************

:platform: Python 3.5.10 on Linux, OS X
:synopsis: This module implements classes for generic measurements taken from a meter.
:authors: Janus Bo Andersen, Jakob Aaboe Vestergaard
:date: 13 October 2020
"""

import os
from collections import OrderedDict
import json
from datetime import datetime
from typing import Any, Dict

from utils.timezone import zulu_time_str


class Measurement:
    """Single physical measurement.
    A single measurement of a physical quantity pair, consisting of a value and a unit.
    """
    def __init__(self, value: float, unit: str):

        # A numeric value (float)
        self.value = value

        # A string SI unit
        self.unit = unit

    def __str__(self) -> str:
        return str(self.value) + " " + self.unit

    def __repr__(self) -> str:
        return 'Measurement({}, {})'.format(self.value, self.unit)


class MeterMeasurement:
    """
    A single measurement collection based on one frame from the meter.
    Will contain multiple measurements of physical quantities taken at the same time.
    """

    def __init__(self, meter_id: str, timestamp: datetime):
        """
        Make a new measurement collection.
        Takes meter ID of the meter taking the measurement.
        Add the time when the measurement was received as a datetime obj.
        """

        self.meter_id = meter_id
        self.timestamp = timestamp
        self.measurements = OrderedDict()   # type: OrderedDict[str, Any]

    def add_measurement(self, name: str, measurement: Measurement) -> None:
        """
        Store a new measurement in the collection.
        """

        # Insert new pair into ordered dict. The name is human readable
        self.measurements.update({name: measurement})

    def __str__(self) -> str:
        """
        Human readable representation of a measurement collection.
        """
        # Build the header
        header = "Meter ID: " + str(self.meter_id) + os.linesep
        header = header + "Timestamp: " + zulu_time_str(self.timestamp) + os.linesep

        # Iterate over the measurements in the collection, making a combined string
        text = [k + ": " + str(v.value) + " " + str(v.unit) for k, v in self.measurements.items()]
        text_join = os.linesep.join(text)

        # Return human readable combined string
        return header + text_join

    def __repr__(self) -> str:
        return "MeterMeasurement('{}', {})".format(self.meter_id, zulu_time_str(self.timestamp))

    def as_dict(self) -> dict:
        """
        Serializes and outputs the Measurement frame as a structured dict.
        """

        # Build object, and dump timestamp using ISO8601, https://en.wikipedia.org/wiki/ISO_8601
        obj = dict({
            'MeterID': str(self.meter_id),
            'Timestamp': zulu_time_str(self.timestamp),
        })  # type: Dict[str, Any]

        # Build a temporary dict where we insert all the measurements
        tmp = dict()    # type: Dict[str, Any]

        for key, val in self.measurements.items():
            tmp.update({key: {'value': val.value, 'unit': val.unit}})

        # Insert the temporary dictionary with all measurements into the original object
        obj.update({'Measurements': tmp})

        return obj

    def json_dump(self) -> str:
        """Returns a JSON formatted string of all data in frame.
        """
        obj = self.as_dict()
        return json.dumps(obj)
