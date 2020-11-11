"""
Contains main loop which instantiates and runs the entire system
:Authors: Steffen, Janus
:Date: 10 November 2020

Ver. 0.1: Build main loop with queue and Mqtt startup


Test message to send to start monitoring out OmniPower:
mosquitto_pub -h <INSERT IP> -t "testtopic" -m '[{"deviceId": "32666857","manufacturerKey": "kam","encryptionKey": "9A25139E3244CC2E391A8EF6B915B697", "manufacturerDeviceKey": "OmniPower1"}]' -u <INSERT USER> -P <INSERT PWD>


"""

from mqtt.MqttClient import MqttClient, donothing_onmessage, donothing_onpublish
from collections import deque
from time import sleep
import json
from meter.OmniPower import OmniPower, C1Telegram
from select import select
from utils.log import get_logger
import os


# Global double-ended queue, atomic object for communication from mqtt thread
dq = deque(maxlen=1)

meter_list = {}     # Creating a dict

# Get logger instance
log = get_logger()

# Try to open FIFO
curr_path = os.path.dirname(os.path.abspath(__file__))
base_path = os.path.split(curr_path)[0]
fifo_path = os.path.join(base_path, "driver", "IM871A_pipe")
print(fifo_path)

try:
    fifo = open(fifo_path, 'r')
except OSError as err:
    log.exception(err)
    exit(1)

publisher = MqttClient("publishToRecalc", donothing_onmessage, donothing_onpublish, param_settings='mqtt')

def run_system():
    """
    Implements the main loop to run the entire system
    """

    # define action to take on every message from ReMoni ReCalc
    def on_message_callback(client, userdata, message):
        try:
            msg = message.payload.decode("utf-8")
            topic = message.topic
            # Put it into the queue
            dq.appendleft((topic, msg))
        except:
            pass

    # instantiate Mqtt client
    recalc = MqttClient("ListenToRecalc", on_message_callback, donothing_onpublish, param_settings='mqtt')
    recalc.subscribe("testtopic")

    # start thread, runs in background
    recalc.loop_start()

    # Main event loop
    while True:

        # Step 1: Check for message from ReMoni ReCalc
        #TODO: Prevent to objects with same serial number

        if dq:
            q_elem = dq.pop()
            full_obj = json.loads(q_elem[1])
            meter_list.clear()

            # TODO: Do we need to send a config over MQTT?
            # Step 2: Process message and update data structure
            # Split the topic and message to figure out what to do
            for i in range(0, len(full_obj)):
                # Set serial no. and convert to little-endian
                meter_id = full_obj[i]['deviceId']

                # Adding to dictionary
                # TODO: Figure out which topic to publish on from an MQTT message and include in this object
                meter_list.update({meter_id: OmniPower(name="OP-" + meter_id, meter_id=meter_id,
                                                       aes_key=full_obj[i]['encryptionKey']),
                                   'manufacturerKey': full_obj[i]['manufacturerKey'],
                                   'deviceId': full_obj[i]['deviceId'],
                                   })

            print(meter_list)

        # Step 3: Read all data from driver via FIFO
        # Tap the FIFO

        select([fifo], [], [], 10)  # polls and wait for data ready for read on fifo, 10 sec timeout

        # TODO: Don't close FIFO in driver
        msg = fifo.readline().strip()   #UTF-8 without line break
        if not msg:                     # If EOF telegram, just start again
            continue

        #print("Received telegram: {}".format(msg))

        try:
            telegram = C1Telegram(msg.encode())     # Must take bytes
            address = telegram.big_endian['A'].decode()  # Gets address as UTF-8 string
            #print("Received address {}".format(address))

            # Step 4: Process received telegrams
            #print("Monitored serial numbers {}".format(meter_list.keys()))
            if address in meter_list.keys():
                meter_list[address].process_telegram(telegram)

                # Step 5: See the log
                print(meter_list[address].measurement_log[-1])

                # v2/<gw-id>/<manufacturer-key>-<device-id>/data
                topic = "v2/" + meter_list['manufacturerKey'] + "-" + meter_list['deviceId'] + "/data"
                cloud_message = meter_list[address].measurement_log[-1].json_dump()
                #print(cloud_message)
                publisher.publish(topic, cloud_message)

        except:
            pass

        sleep(2)


if __name__ == '__main__':
    # When run from terminal, it powers up the system, and away we go...
    run_system()

    fifo.close()

# PYTHONPATH=alsjlasnglan:$PYTHONPATH python script.py