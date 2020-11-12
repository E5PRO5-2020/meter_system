"""
Metering system main event loop
*******************************

:Synopsis: This script is main loop which handles the system flow
:Authors: Steffen, Thomas, Janus
:Date: 11 November 2020

* **Ver. 0.1**: Build main loop with queue and Mqtt startup
* **Ver. 0.9**: Implement mqtt to get command from ReCalc, dispatcher, and mqtt to send data to ReCalc

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
    - `mosquitto_pub -h <INSERT IP> -t "v2/pi@vestjylland/sensors/set" -m '[{"deviceId": "32666857","manufacturerKey": "kam","encryptionKey": "9A25139E3244CC2E391A8EF6B915B697", "manufacturerDeviceKey": "OmniPower1"}]' -u <INSERT USER> -P <INSERT PWD>`
- Test to receive published data (fill in username and password):
    - `mosquitto_sub -h <INSERT IP> -t "#" -u <INSERT USER> -P <INSERT PWD>`

TO DO
-----

- Implement clean way to terminate program over MQTT
- Implement API compliant message
- Sort out all TODOs in the code

"""

from collections import deque
import json
import os
from select import select

from mqtt.MqttClient import MqttClient, donothing_onmessage, donothing_onpublish
from meter.OmniPower import OmniPower, C1Telegram
from utils.log import get_logger
from utils.load_settings import load_settings


def run_system():
    """
    Implements the main loop to run the entire system.
    """

    # Main event loop
    while True:

        # Step 1: Check for message from ReMoni ReCalc
        if dq:
            q_elem = dq.pop()

            # If receiving
            if q_elem[0] == 'STOP':
                end_loop()

            full_obj = json.loads(q_elem[1])
            meter_list.clear()

            # TODO: Do we need to respond with a config over MQTT?
            # Step 2: Process message and update data structure
            for i in range(0, len(full_obj)):
                # Set serial no. and convert to little-endian
                meter_id = full_obj[i]['deviceId']

                # Adding object like this to meter_list dictionary
                #    "12345678": {
                #                   "manufacturerKey": "kam",
                #                   "manufacturerDeviceKey": "somekeyfromrecalc",
                #                   "handler": OmniPower(...),
                #                   "mqttTopic": "v2/<gw-id>/<manufacturer-key>-<device-id>/data",
                #                 }

                meter_control = {
                    "manufacturerKey": full_obj[i]['manufacturerKey'],
                    "manufacturerDeviceKey": full_obj[i]['manufacturerDeviceKey'],
                    "handler": OmniPower(name="OP" + meter_id, meter_id=meter_id, aes_key=full_obj[i]['encryptionKey']),
                    "mqttTopic": "v2/" + full_obj[i]['manufacturerKey'] + "-" + full_obj[i]['deviceId'] + "/data",
                }

                # TODO: Prevent two objects with same serial number if sent by mistake?
                meter_list.update({meter_id: meter_control})

            print(meter_list)

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
                meter_list[address]["handler"].process_telegram(telegram)

                # See the log after message parsed, decrypted, etc.
                print(meter_list[address]["handler"].measurement_log[-1])

                # Step 6: Make MQTT message and send
                topic = meter_list[address]["mqttTopic"]
                data_frame = meter_list[address]["handler"].measurement_log.pop()
                cloud_message = data_frame.json_dump()
                publisher.publish(topic, cloud_message)

        except Exception as e:
            log.exception(e)


if __name__ == '__main__':
    # When run from terminal, it sets ub globals, and away we go...

    # Global double-ended queue, atomic object for communication from mqtt thread
    dq = deque(maxlen=1)

    # Dispatcher object
    meter_list = {}

    # Get logger instance
    log = get_logger()

    # Try to open FIFO
    curr_path = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.split(curr_path)[0]
    fifo_path = os.path.join(base_path, "driver", "IM871A_pipe")
    print("Connected to pipe: {}".format(fifo_path))

    try:
        fifo = open(fifo_path, 'r')
    except OSError as err:
        log.exception(err)
        exit(1)

    # On every message from ReMoni ReCalc, the message is put into atomic, threadsafe queue
    def on_command_callback(client, userdata, message):
        try:
            msg = message.payload.decode("utf-8")
            topic = message.topic
            # Put it into the queue
            dq.appendleft((topic, msg))
        except Exception as e:
            log.exception(e)

    # Set up client to get commands from ReCalc
    recalc = MqttClient("ListenToRecalc", on_command_callback, donothing_onpublish, param_settings='mqtt')

    # TODO: Figure out correct topic/gw-id to monitor
    monitor_topic = load_settings()['mqtt']['subscribe_topic']

    # TODO: Do this in one call [topic1, topic2]?
    recalc.subscribe(monitor_topic)
    recalc.subscribe('STOP')

    # start thread, runs in background
    recalc.loop_start()

    # Set up client to transmit metered data to ReCalc
    publisher = MqttClient("PublishToRecalc", donothing_onmessage, donothing_onpublish, param_settings='mqtt')

    # Function to cleanly exit loop and end threads, disconnect
    def end_loop():
        """
        Nice, clean exit.
        """

        fifo.close()
        recalc.loop_stop()
        recalc.disconnect()
        publisher.disconnect()
        exit(0)

    print("Starting main loop")
    run_system()
