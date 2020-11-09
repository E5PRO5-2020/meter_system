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


def set_json():
    meter1 = {
        "deviceId": "32666857",
        "manufacturerKey": "kam",
        "encryptionKey": "9A25139E3244CC2E391A8EF6B915B697",
        "manufacturerDeviceKey": "OmniPower1"
    }

    meter2 = {
        "deviceId": "76422795",
        "manufacturerKey": "kam",
        "encryptionKey": "DEADBEEF",
        "manufacturerDeviceKey": "NotOmniPower"
    }

    list_of_meters = [meter1, meter2]

    return json.dumps(list_of_meters)


def get_json(json_str):
    return json.loads(json_str)


if __name__ == '__main__':

    # Encode objects as JSON string and print to terminal
    json_str = set_json()
    print(json_str)

    # Decode the JSON string, and print some data from the first of the object
    full_obj = get_json(json_str)
    print(full_obj[1]['deviceId'])
    