"""
Metering system main event loop
*******************************

:Synopsis: This script is main loop which handles the system flow
:Authors: Steffen, Thomas, Janus
:Latest update: 17 November 2020
:Version: 0.92
:Version history:
* **Ver. 0.1**: Build main loop with queue and Mqtt startup.
* **Ver. 0.9**: Implement mqtt to get command from ReCalc, dispatcher, and mqtt to send data to ReCalc.
* **Ver. 0.91**: Implement (1) gw-id from settings into topics, (2) mqtt pub rc check (log on err), (3) Use DEBUG instead of print.
* **Ver. 0.92**: Move functions out of __main__ section to document them.

Starting and stopping the system
--------------------------------

- Full system is started using shell script `start_stop_system.sh`.
    - Start: `./start_stop_system.sh start`
    - Stop: `./start_stop_system.sh stop`
- Driver will be running as daemon and will create a FIFO as driver/IM871A_pipe.
- This script will visibly run in terminal (debug).

Stopping the system over MQTT
-----------------------------

- Send message with `topic: STOP` to end program. Example:
    - `mosquitto_pub -h <INSERT IP> -p 1883 -t STOP -m 'anything' -u <INSERT USER> -P <INSERT PWD>`


Data flows
----------

* Config flow: ReCalc command (mqtt) -> Update Dispatcher
* Data flow: Driver -> (FIFO) -> C1-parser -> Dispatcher -> Handler (OmniPower) -> Mqtt publish data
* Error logging flow: On errors -> Logger -> SysLog

Testing
-------

- Test message to start monitoring our OmniPower (fill in username and password):
    - `mosquitto_pub -h <INSERT IP> -t "v2/706462169/sensors/set" -m '[{"deviceId": "32666857","manufacturerKey": "kam","encryptionKey": "9A25139E3244CC2E391A8EF6B915B697", "manufacturerDeviceKey": "OmniPower1"}]' -u <INSERT USER> -P <INSERT PWD>`
- Test to receive published data (fill in username and password):
    - `mosquitto_sub -h <INSERT IP> -t "#" -u <INSERT USER> -P <INSERT PWD>`

TO DO
-----

- Implement API compliant message
- Sort out all TODOs in the code
- Consider refactoring several steps into functions

"""

from collections import deque
import json
import os
from select import select

from mqtt.MqttClient import MqttClient, donothing_onmessage, donothing_onpublish, publish_rc_str, publish_rc_bool
from meter.OmniPower import OmniPower, C1Telegram
from utils.log import get_logger
from utils.load_settings import load_settings
import mqtt.api as api


def run_system():
    """
    Implements the main loop to run the entire system.
    """

    # Main event loop
    DEBUG("Listening on MQTT.")
    while True:

        # Step 1: Check for message from ReMoni ReCalc
        if dq:
            q_elem = dq.pop()

            # If receiving command to stop
            if q_elem[0] == 'STOP':
                end_loop()

            # ReCalc sends list with objects, each object represents a sensor to monitor
            obj_list = json.loads(q_elem[1])
            meter_list.clear()

            # Step 2: Process message objects and update data structure
            for obj in obj_list:
                # Set serial no. and convert to little-endian
                meter_id = obj['DeviceId']

                # Adding object like this to meter_list dictionary
                #    "12345678": {
                #                   "ManufacturerKey": "kam",
                #                   "ManufacturerDeviceKey": "somekeyfromrecalc",
                #                   "handler": OmniPower(...),
                #                   "mqttTopic": "v2/<gw-id>/<manufacturer-key>-<device-id>/data",
                #                 }

                meter_control = {
                    "ManufacturerKey": obj['ManufacturerKey'],
                    "ManufacturerDeviceKey": obj['ManufacturerDeviceKey'],
                    "handler": OmniPower(name="OP" + meter_id, meter_id=meter_id, aes_key=obj['EncryptionKey']),
                    "mqttTopic": "v2/" + str(gw_id) + "/" + obj['ManufacturerKey'] + "-" + obj['DeviceId'] + "/data",
                }

                # TODO: Prevent two objects with same serial number if sent by mistake?
                meter_list.update({meter_id: meter_control})

                # Make config topic
                # v2/<gw-id>/<manufacturer-key>-<device-id>/config
                config_topic = "v2/" + str(gw_id) + "/" + obj['ManufacturerKey'] + "-" + obj['DeviceId'] + "/config"

                # Send config message
                # TODO: Fix PyCharm unresolved reference due to tuple
                config_msg = api.config_json()
                rc = publisher.publish(config_topic, config_msg)
                rc.wait_for_publish()

                DEBUG("Sent config message: " + str((config_msg, config_topic)))

            DEBUG("Monitored meters:")
            DEBUG(str(meter_list))

        # Step 3: Read telegram data from driver via FIFO
        # Wait for data to read on fifo, break every 10 sec to check MQTT
        # If this times out, we will just read an empty FIFO and restart loop.
        select([fifo], [], [], 10)

        msg = fifo.readline().strip()   # UTF-8 without line break
        if not msg:                     # If EOF telegram, just start loop again
            continue

        # Step 4: Process received telegram
        try:
            telegram = C1Telegram(msg.encode())             # Must take bytes, not UTF-8
            address = telegram.big_endian['A'].decode()     # Gets address into UTF-8 string

            # Step 5: Let a registered meter handle the telegram
            if address in meter_list.keys():
                DEBUG("Received data on monitored meter.")
                meter_list[address]["handler"].process_telegram(telegram)

                # See the log after message parsed, decrypted, etc.
                DEBUG(meter_list[address]["handler"].measurement_log[-1])

                # Step 6: Make MQTT message and send
                topic = meter_list[address]["mqttTopic"]
                data_frame = meter_list[address]["handler"].measurement_log.pop()
                data_msg_list = api.build_api_message_from_log_obj(data_frame)

                # Loop over all measurements to be sent
                for data_msg in data_msg_list:
                    rc = publisher.publish(topic, json.dumps(data_msg))
                    DEBUG(json.dumps(data_msg))
                    rc.wait_for_publish()

                DEBUG("Sent MQTT message with rc" + str(rc) + ": " + publish_rc_str(rc) + ".")
                if not publish_rc_bool(rc):
                    # Save message somewhere
                    log.info("Failed to send MQTT message")

        except Exception as e:
            log.exception(e)


def on_command_callback(client, userdata, message):
    """
    On every message from ReMoni ReCalc, the message is put into an atomic, threadsafe queue.
    Atomic deque, dq, is from global scope from __main__ section.
    """

    try:
        msg = message.payload.decode("utf-8")
        topic = message.topic
        DEBUG("Topic: " + topic + ". Message: " + msg)
        # Put received message into the queue as tuple
        dq.appendleft((topic, msg))
    except Exception as e:
        log.exception(e)


def end_loop():
    """
    Function to cleanly exit loop and end threads, disconnect.
    From __main__ section: FIFO queue, fifo; Mqtt subscriber, recalc; Mqtt publisher.
    """

    fifo.close()
    recalc.loop_stop()

    # TODO: Consider implementing disconnects in destructors (must be tested)
    recalc.disconnect()
    publisher.disconnect()
    DEBUG("Stopping main loop.")
    exit(0)


def DEBUG(message: str):
    """
    Prints out if global DEBUG_ON set to True.
    """

    if DEBUG_ON:
        print(message)


if __name__ == '__main__':
    # When run from terminal, it sets up globals, and away we go...

    # Debug printouts
    DEBUG_ON = True

    # Global double-ended queue, atomic object for communication from mqtt thread
    dq = deque(maxlen=1)

    # Dispatcher object, empty dict (hashmap)
    meter_list = {}

    # Make logger instance
    log = get_logger()

    # Try to open FIFO, first build an absolute path to the FIFO
    curr_path = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.split(curr_path)[0]
    fifo_path = os.path.join(base_path, "driver", "IM871A_pipe")

    try:
        DEBUG("Trying to open FIFO, waiting for communication partner.")
        fifo = open(fifo_path, 'r')
        DEBUG("Connected to pipe: {}".format(fifo_path))
    except OSError as err:
        log.exception(err)
        exit(1)

    # Set up client to get commands from ReCalc
    profile = 'recalc'
    #"ListenTo_" + profile
    recalc = MqttClient("Verner", on_command_callback, donothing_onpublish, param_settings=profile)

    # Gets topics to monitor and ID for this gateqay
    settings_yaml = load_settings()[profile]
    monitor_topic = settings_yaml['subscribe_topic']
    DEBUG("Monitor topic: " + monitor_topic)
    gw_id = settings_yaml['gateway_id']

    # TODO: Do this in one call [(topic1,0), (topic2,0)]?
    recalc.subscribe(monitor_topic, 0)
    #recalc.subscribe('STOP')

    # start thread, runs in background
    recalc.loop_start()

    # Set up client to transmit metered data to ReCalc
    publisher = MqttClient("PublishToRecalc", donothing_onmessage, donothing_onpublish, param_settings='recalc')

    DEBUG("Starting main loop:")
    run_system()
