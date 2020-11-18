"""
Just to make some simples test with the class.
"""

from mqtt.MqttClient import MqttClient
import time


def on_message_callback(client, userdata, message):
    msg = message.payload.decode("utf-8")
    print(message.topic)
    print(msg)


def on_publish_callback(client, userdata, mid):
    pass


if __name__ == '__main__':
    Client = MqttClient(name="MyID", on_message=on_message_callback, on_publish=on_publish_callback)
    Client.subscribe(topic="123321")
    # Start Thread
    Client.loop_start()
    while True:
        Client.publish(topic="Hello", payload="Random ass payload")
        time.sleep(60)
