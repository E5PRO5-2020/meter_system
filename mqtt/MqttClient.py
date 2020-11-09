"""
MQTT-class for communication between Gateway and ReCalc/Cloud at ReMoni.
*************************************************
:Platform: Python 3.5.10 on Linux
:Synopsis: This module implements a class for MQTT Client
:Authors: Steffen Breinbjerg, Janus Bo Andersen
:Date: 9 November 2020
"""

import yaml
import paho.mqtt.client as mqtt


class MqttClient:
    @staticmethod
    def __load_settings() -> dict:
        with open('secrets.yaml') as f:
            settings = yaml.load(f, Loader=yaml.FullLoader)
            # print(settings)
            return settings

    # This method is the same for all instances of the class
    @staticmethod
    def __on_connect(client, userdata, flags, rc):
        """
          on_connect callback rc argument value meaning:
          0: Connection successful
          1: Connection refused - incorrect protocol version
          2: Connection refused - invalid client identifier
          3: Connection refused - server unavailable
          4: Connection refused - bad username or password
          5: Connection refused - not authorised 6-255: Currently unused.
          """
        print("Connected with result code " + str(rc))

    # For outputting log messages to console
    @staticmethod
    def __on_log(client, userdata, level, buf):
        print("log: ", buf)

    # By default, do nothing on_message
    @staticmethod
    def __on_message_default(client, userdata, message):
        pass

    # To track QoS2 handshaking
    @staticmethod
    def __on_publish(client, userdata, mid):
        pass

    def __init__(self, name, on_message, on_publish):
        """Handles all setup and connection when object is initialized.

        :param name: Client ID
        :type name: String
        :param on_message: On message callback function
        :type on_message: Function pointer
        :param on_publish: On publish callback function
        :type on_publish: Function pointer.
        """
        settings = self.__load_settings()
        self.client = mqtt.Client(client_id=name, clean_session=True, userdata=None, transport="tcp")
        self.client.username_pw_set(settings["username"], settings["password"])
        self.client.on_connect = MqttClient.__on_connect
        self.client.on_message = on_message
        self.client.on_publish = on_publish

        # In production, let's consider disabling logging or routing to a file
        self.client.on_log = MqttClient.__on_log
        self.client.enable_logger()

        # This ensures, that there is some sort of goodbye on losing connection
        # self.client.will_set(name, will_message)

        # Connect immediately
        self.client.connect(settings["ip"], port=settings["port"])

    def loop_start(self):
        """
        Start loop in new thread. This thread will handle disconnects to MQTT broker.
        """
        return self.client.loop_start()

    def loop_stop(self):
        """
        Stops the loop thread.
        """
        return self.client.loop_stop()

    # Note: Removed qos=2 - This may be added again.
    def publish(self, topic, payload):
        """
        :param topic: Topic to publish to
        :param payload: Message payload
        """
        return self.client.publish(topic, payload)

    def subscribe(self, topic):
        """
        :param topic: Topic to subscribe to.
        :type topic: String
        """
        return self.client.subscribe(topic)

    def loop_forever(self):
        """
        Will block the program, and only handle callback functions and disconnects.
        """
        return self.client.loop_forever(retry_first_connection=False)

    def disconnect(self):
        return self.client.disconnect()
