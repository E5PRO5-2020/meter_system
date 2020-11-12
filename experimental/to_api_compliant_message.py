"""
Converts the JSON-dump from MeterMeasurement to an API-compliant Message
Author: Jakob
"""

from meter.MeterMeasurement import MeterMeasurement
import json
from utils.timezone import zulu_time_str


def to_API(m: 'MeterMeasurement') -> str:
    """
    The format of GateWay publish data for ReCalc is as follow

    Topic: v2/<gw-id>/<manufacturer-key>-<device-id>/data
    Message:
    [
        {
            channelNumber: 1,
            aggregateType: "Raw",
            dataType: "temperature",
            value: 4.9,
            timestamp: "2020-03-20T12:00:00"
        },
        {
            channelNumber: 1,
            aggregateType: "Raw",
            dataType: "humidity",
            value: 50,
            timestamp: "2020-03-20T12:00:00"
        }
    ]

    The output from MeterMeasurement.jsondump() is:

    Topic: v2/kam-32666857/data
    Message:
    [
        {
            "Timestamp": "2020-20-20T18:39:31Z",
            "MeterID": "32666857",
            Measurements:"
                {
                    "A+":
                        {
                            "unit": "kWh",
                            "value": "4.32"
                        },
                    "A-":
                        {
                            "unit": "kWh",
                            "value": "0"
                        },
                    "P+":
                        {
                            "unit": "kW",
                            "value": "0.005"
                        },
                    "P-":
                        {
                            "unit": "kW",

    API_Dict = {
        "channelNumber": 1,
        "aggregateType": ,
        "dataType": "temperature",
        "value": 4.9,
        "timestamp": "2020-03-20T12:00:00"

    }

    print("Looking like this: \n", jsonobj)

    return json.dumps(API_Dict)     "value": "0"
                        },
                }
        }
    ]
    Author: Jakob
    """
    # Choice of keys to send from
    keys = ['A+', 'A-', 'P+', 'P-']

    # measurements is a MeterMeasurement, containing several Measurements objects inside its measurements field
    measurements = m.measurements

    # List of data points to send, to be built
    send_list = []

    # Only loop over the keys we want to send
    for key in keys:
        v = measurements[key].value

        template = {
            "channelNumber": 1,
            "aggregateType": "Raw",
            "dataType": key,
            "value": v,
            "timestamp": zulu_time_str(m.timestamp)
        }

        send_list.append(template)
    #    s = to_API(omnipower.measurement_log[-1])
    return json.dumps(send_list)