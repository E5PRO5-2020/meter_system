"""
Topic: v2/<gw-id>/sensors/set
Message:
[
    {
        "deviceId": "57686632",
        "manufacturerKey": "kam",
        "encryptionKey": "9A25139E3244CC2E391A8EF6B915B697",
        "manufacturerDeviceKey": "OmniPower1"
    },
    {
        "deviceId": "76422795",
        "manufacturerKey": "kam",
        "encryptionKey": "abcd",
        "manufacturerDeviceKey": "NotOmniPower"
    }
]

"""

import json
from typing import Dict, Any


def make_json() -> str:
    """
    Simulates a possible message from ReCalc informing the Gateway
    about which meters to read.
    """

    meter1 = {
        "deviceId": "32666857",
        "manufacturerKey": "kam",
        "encryptionKey": "9A25139E3244CC2E391A8EF6B915B697",
        "manufacturerDeviceKey": "OmniPower1"
    }

    meter2 = {
        "deviceId": "76422795",
        "manufacturerKey": "kam",
        "encryptionKey": "abcd",
        "manufacturerDeviceKey": "NotOmniPower"
    }

    meter3 = {
        "deviceId": "88888888",
        "manufacturerKey": "kam",
        "encryptionKey": "abcd",
        "manufacturerDeviceKey": "AlsoNotOmniPower"
    }

    list_of_meters = [meter1, meter2, meter3]

    return json.dumps(list_of_meters)


def get_meters_to_read(json_str: str) -> Dict[Any, Any]:
    """
    Simulates reading a message and parsing it as JSON->Dict
    """

    return json.loads(json_str)


if __name__ == '__main__':

    # Encode objects as JSON string and print to terminal
    json_str = make_json()
    print(json_str)

    # Decode the JSON string, and print some data from the first meter in the list object
    full_obj = get_meters_to_read(json_str)
    print(full_obj[0]['deviceId'])

    # Get all device ids
    # Be aware that these are received big-endian from ReCalc and little-endian from wm-bus
    device_ids = [device_data['deviceId'] for device_data in full_obj]
    print(device_ids)
