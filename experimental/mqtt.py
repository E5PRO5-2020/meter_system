"""
Experimental MQTT Client
Connect to Raspberry from outside

"""

import time
import yaml
import paho.mqtt.client as mqtt


def load_auth_info() -> dict:
    with open('secrets.yaml') as f:
        settings = yaml.load(f, Loader=yaml.FullLoader)
        # print(settings)
        return settings


class MqttClient():

    # Get setting from local secrets file
    settings = load_auth_info()

    # These should be gotten from the environment or, ideally, from the Django settings file
    broker_address = settings["ip"]
    broker_port = settings["port"]
    username = settings["username"]
    password = settings["password"]

    # This method is the same for all instances of the class
    @staticmethod
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

    # For outputting log messages to console
    @staticmethod
    def on_log(client, userdata, level, buf):
        print("log: ", buf)

    # By default, do nothing on_message
    @staticmethod
    def on_message_default(client, userdata, message):
        pass

    # To track QoS2 handshaking
    @staticmethod
    def on_publish(client, userdata, mid):
        pass

    #Initialize the client, straight on create
    def __init__(self, name, on_message, on_publish, will_message="Logging off"):
        """ __init__ Handles all setup and connection when object is initialized.
        @:param: name is the name of the client, as will be shown on the server (required)
        @:param: on_message is the callback used when this client receives a message (required)
        @:param: will_message is the "Last Will" message sent when the client loses the connection (optional)
        """
        self.client = mqtt.Client(client_id=name, clean_session=True, userdata=None, transport="tcp")
        self.client.username_pw_set(MqttClient.username, MqttClient.password)
        self.client.on_connect = MqttClient.on_connect
        self.client.on_message = on_message
        self.client.on_publish = on_publish

        # In production, let's consider disabling logging or routing to a file
        self.client.on_log = MqttClient.on_log
        self.client.enable_logger()

        # This ensures, that there is some sort of goodbye on losing connection
        self.client.will_set(name, will_message)

        # Connect immediately
        self.client.connect(MqttClient.broker_address, port=MqttClient.broker_port)

    def loop_start(self):
        return self.client.loop_start()

    def loop_stop(self):
        return self.client.loop_stop()

    def publish(self, topic, payload):
        return self.client.publish(topic, payload, qos=2)

    def subscribe(self, topic):
        return self.client.subscribe(topic)

    def loop(self):
        return self.client.loop_forever(retry_first_connection=False)

    def run_thread(self):
        return self.client.loop_start()

    def run_once(self):
        return self.client.loop()

    def disconnect(self):
        return self.client.disconnect()


if __name__ == '__main__':

    #global i_am_global
    i_am_global = False

    def on_message_callback(client, userdata, message):
        msg = message.payload.decode("utf-8")
        topic = message.topic
        topic_parts = topic.split('/') #consider matching using regex instead
        print(topic)
        print(topic_parts)
        print(msg)
        global i_am_global
        i_am_global= not i_am_global

    def on_publish_callback(client, userdata, mid):
        pass

    # Pass the callback to the client
    subscriber = MqttClient("ConnectedFromRemote", on_message_callback, on_publish_callback)

    # Only subscribe to relevant inbound messages
    subscriber.subscribe("#")

    print("Starting a loop")
    subscriber.run_thread()

    while True:
        print("Thread is running!")
        print("Current state of global variable {}.".format(i_am_global))
        time.sleep(10.0)
