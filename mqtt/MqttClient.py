"""
MQTT-class for communication between Gateway and ReCalc/Cloud at ReMoni
***********************************************************************

:Platform: Python 3.5.10 on Linux
:Synopsis: This module implements a class for MQTT Client
:Authors: Steffen Breinbjerg, Janus Bo Andersen
:Latest update: 18 November 2020
:Version: 1.2

* **Ver. 1.0**: Setup MQTT class with loaded settings.
* **Ver. 1.1**: Implement support functions for return codes and better printout for on_connect.
* **Ver. 1.2**: Implemented TLS and better handling of reason codes.

"""

import paho.mqtt.client as mqtt
from utils.load_settings import load_settings
from typing import Tuple
import ssl


class MqttClient:
    """
    This class wraps a Paho MQTT client and sets it up using a profile from settings/secrets.yaml.
    On instantiation, all setup steps run up to and including connect.

    """

    # This method is the same for all instances of the class
    @staticmethod
    def on_connect(client: 'mqtt.Client', userdata, flags, rc):
        """
        on_connect callback rc argument value meaning:

        * 0: Connection successful
        * 1: Connection refused - incorrect protocol version
        * 2: Connection refused - invalid client identifier
        * 3: Connection refused - server unavailable
        * 4: Connection refused - bad username or password
        * 5: Connection refused - not authorised 6-255: Currently unused.

        """
        # TODO: Implement logging potentially
        print("Connected " + client._client_id.decode() + " with result code " + str(rc) + ": " + connection_rc_str(rc))

    # For outputting log messages to console
    @staticmethod
    def __on_log(client, userdata, level, buf):
        # TODO: Implement logging if needed
        pass
        # print("log: ", buf)

    # By default, do nothing on_message
    @staticmethod
    def __on_message_default(client, userdata, message):
        pass

    # To track QoS2 handshaking
    @staticmethod
    def __on_publish(client, userdata, mid):
        pass

    @staticmethod
    def on_disconnect(client, userdata, flads, rc=0):
        pass

    @staticmethod
    def on_subscribe(client, obj, mid, granted_qos):
        pass

    def __init__(self, name, on_message, on_publish, param_settings='mqtt_local'):
        """Handles all setup and connection when object is initialized.

        :param str name: Client ID (must be unique)
        :param function_ptr on_message: On message callback function
        :param function_ptr on_publish: On publish callback function
        :param str param_settings: Profile from secrets.yaml to use
        """

        settings = load_settings()[param_settings]
        self.client = mqtt.Client(client_id=name, transport=settings["transport"])
        self.client.username_pw_set(settings["username"], str(settings["password"]))
        if settings["tls"]:
            self.client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
                                tls_version=ssl.PROTOCOL_TLS)
        self.client.on_connect = MqttClient.on_connect
        self.client.on_message = on_message
        self.client.on_disconnect = MqttClient.on_disconnect
        self.client.on_subscribe = MqttClient.on_subscribe
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
        :param str topic: Topic to publish to
        :param str payload: Message payload
        :returns: (result, mid)
        :rtype: tuple

            - result: 0 on success, 4 if no connection
            - mid is message id for tracked message

        """

        return self.client.publish(topic, payload)

    def subscribe(self, topic, qos):
        """
        :param str topic: Topic to subscribe to.
        :param int qos: Quality of service level (0, 1, 2).
        :returns: (result, mid)
        :rtype: tuple

            - result: 0 on success, 4 if no connection
            - mid is message id for tracked message
        """
        return self.client.subscribe(topic, qos)

    def loop_forever(self):
        """
        Will block the program, and only handle callback functions and disconnects.
        """
        return self.client.loop_forever(retry_first_connection=False)

    def disconnect(self):
        """
        Gracefully disconnects from server.
        """
        return self.client.disconnect()


def donothing_onmessage(client, userdata, message):
    pass


def donothing_onpublish(client, userdata, mid):
    pass


def publish_rc_str(rc: Tuple) -> str:
    """
    Returns text description of return codes for publishing a message.
    Based on return code spec. from Paho MQTT.
    Alternatively, use mqtt.error_string().
    """
    rc_str = {
        mqtt.MQTT_ERR_SUCCESS: "Successful",
        mqtt.MQTT_ERR_NO_CONN: "No connection"
    }

    try:
        reason = rc_str[rc[0]]
    except KeyError as e:
        reason = "unknown"

    return reason


def publish_rc_bool(rc: Tuple) -> bool:
    """
    Returns True if message was sent correctly, otherwise False.
    Based on return code spec. from Paho MQTT.
    The rc tuple is (reason_code, message_id).
    Alternatively, use mqtt.error_string().
    """

    return rc[0] == mqtt.MQTT_ERR_SUCCESS


def connection_rc_str(rc: Tuple) -> str:
    """
    Returns text description of return codes for a connection attempt to server.
    Based on return code spec. from Paho MQTT.
    Alternatively, use mqtt.connack_string().
    """
    rc_str = {
        mqtt.CONNACK_ACCEPTED: "Connection successful",
        mqtt.CONNACK_REFUSED_PROTOCOL_VERSION: "Connection refused - incorrect protocol version",
        mqtt.CONNACK_REFUSED_IDENTIFIER_REJECTED: "Connection refused - invalid client identifier",
        mqtt.CONNACK_REFUSED_SERVER_UNAVAILABLE: "Connection refused - server unavailable",
        mqtt.CONNACK_REFUSED_BAD_USERNAME_PASSWORD: "Connection refused - bad username or password",
        mqtt.CONNACK_REFUSED_NOT_AUTHORIZED: "Connection refused - not authorised"
    }

    return rc_str[rc]
