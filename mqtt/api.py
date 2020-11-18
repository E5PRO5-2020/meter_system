"""

:Synopsis: Implements functionality to send and receive correctly formatted messages as spec'ed by ReMoni API.
:Authors: Jakob, Steffen, Janus
:Last update: 18 Nov. 2020.

"""

import json
from meter.MeterMeasurement import MeterMeasurement, Measurement
from utils.timezone import zulu_time_str
from typing import List, Any


def build_api_message_from_log_obj(m: 'MeterMeasurement') -> List[Any]:
    """
    Due to bug in ReCalc, this currently only returns a list of Python dicts.
    In the future, should return the same dumped to JSON.
    """

    # Choice of keys to send from
    keys = ['A+', 'A-', 'P+', 'P-']

    # measurements is a MeterMeasurement, containing several Measurements objects inside its measurements field
    measurements = m.measurements

    # Check if unit is in kilo-watts, and change it to watts if true
    if m.measurements['P+'].unit == "kW":
        m.measurements['P+'].value = m.measurements['P+'].value * 1000
        m.measurements['P+'].unit = "W"

    if m.measurements['P-'].unit == "kW":
        m.measurements['P-'].value = m.measurements['P-'].value * 1000
        m.measurements['P-'].unit = "W"


    # List of data points to send, to be built
    send_list = []

    # Only loop over the keys we want to send
    for i, key in enumerate(keys):
        v = measurements[key].value
        if key in ['A+', 'A-']:
            temptype = "accumulated-power"
        else:
            temptype = "power"

        template = {
            "channelNumber": i+1,
            "aggregateType": "Raw",
            "dataType": temptype,
            "value": v,
            "timestamp": zulu_time_str(m.timestamp)
        }
        send_list.append(template)

    return send_list


def config_json() -> str:
    """
    Returns a JSON-formatted string to config OmniPower in ReCalc API.

    """

    config_msg = {
        "Channels": [
            {
                "ChannelNumber": 1,
                "DataType": "accumulated-power",
                "ChannelName": "A+ / Active positive energy"
            },
            {
                "ChannelNumber": 2,
                "DataType": "accumulated-power",
                "ChannelName": "A- / Active negative energy"
            },
            {
                "ChannelNumber": 3,
                "DataType": "power",
                "ChannelName": "P+ / Active positive power"
            },
            {
                "ChannelNumber": 4,
                "DataType": "power",
                "ChannelName": "P- / Active negative power"
            }
        ]
    }

    return json.dumps(config_msg)