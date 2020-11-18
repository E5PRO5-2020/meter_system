"""
Experimental MQTT Client
Connect to Raspberry from outside

"""

from mqtt.MqttClient import MqttClient, donothing_onpublish, donothing_onmessage
from collections import deque
import json
from time import sleep

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

    list_of_meters = [meter1, meter2]

    return json.dumps(list_of_meters)


if __name__ == '__main__':

    global q
    q = deque(maxlen=5)

    def on_message_callback(client, userdata, message):
        msg = message.payload.decode("utf-8")
        topic = message.topic
        q.appendleft((topic, msg))

    def on_publish_callback(client, userdata, mid):
        pass

    # Pass the callback to the client
    publisher = MqttClient("PublisherFromRemote",
                           donothing_onmessage,
                           donothing_onpublish,
                           param_settings='mqtt')

    # Pass the callback to the client
    subscriber = MqttClient("SubscriberFromRemote",
                           on_message_callback,
                           donothing_onpublish,
                           param_settings='mqtt')

    # Only subscribe to relevant inbound messages
    subscriber.subscribe("testtopic")

    #print("Starting a loop")
    subscriber.loop_start()

    while True:
        try:
            print(q.pop())
        except:
            print("no message")
        sleep(1)
