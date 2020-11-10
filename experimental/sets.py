"""
This file demos set operations to figure out marginal changes to list of monitored meters.
Lets us keep queues and data and avoid rebuilding a new object every minute.

"""

from experimental.get_mqtt_json import make_json, get_meters_to_read

# Object of currently monitored meters
monitor_list = {
    "32666857": "Old data structure",
    "32666858": "Old data structure",
    "32666859": "Old data structure",
    "76422795": "Old data structure"
}
currently_have = set(monitor_list.keys())           # What we currently monitor

recalc_command = get_meters_to_read(make_json())    # From ReCalc MQTT, get the list we should monitor now
device_ids = [device_data['deviceId'] for device_data in recalc_command]
must_have = set(device_ids)                         # What ReCalc says we must monitor

must_keep = currently_have & must_have              # Common (fællesmængde), so what we must keep
must_add = must_have - currently_have               # Add those we must have, but currently don't
must_delete = currently_have - must_keep            # Delete those we currently have, but shouldn't keep

# Perform refreshing actions
for key in must_add:
    monitor_list.update({key: "New data structure"})

for key in must_delete:
    monitor_list.pop(key)

# Output
print("MeterIds we must monitor: {}".format(must_have))
print("MeterIds we currently monitor: {}".format(currently_have))
print("MeterIds to keep: {}".format(must_keep))
print("MeterIds to add: {}".format(must_add))
print("MeterIds to delete: {}".format(must_delete))
print("Monitor List after update actions: {}".format(monitor_list))
