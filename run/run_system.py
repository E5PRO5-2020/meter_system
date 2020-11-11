"""
Contains main loop which instantiates and runs the entire system
:Authors: Steffen, Janus
:Date: 10 November 2020

Ver. 0.1: Build main loop with queue and Mqtt startup

"""

from mqtt.MqttClient import MqttClient, donothing_onpublish
from collections import deque
from time import sleep
import json
from meter.OmniPower import OmniPower, C1Telegram

# Global double-ended queue, atomic object for communication from mqtt thread
dq = deque(maxlen=1)

meter_list = {}     # Creating a dict

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

            # Step 2: Process message and update data structure
            # Split the topic and message to figure out what to do
            for i in range(0, len(full_obj)):
                # Set serial no. and convert to little-endian
                meter_id = full_obj[i]['deviceId']

                # Adding to dictionary
                # TODO: Figure out which topic to publish on from an MQTT message and include in this object
                meter_list.update({meter_id: OmniPower(name="OP-" + meter_id, meter_id=meter_id,
                                                       aes_key=full_obj[i]['encryptionKey'])})

            print(meter_list)

        # Step 3: Read all data from driver via FIFO
        # Tap the FIFO
        good_telegrams = [b'27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e',
                          b'2d442d2c5768663230028d206461dd032038931d14b405536e0250592f8b908138d58602eca676ff79e0caf0b14d0e7d']


        #TODO: Replace this with driver FIFO
        telegram = C1Telegram(good_telegrams[0])
        address = telegram.big_endian['A'].decode()  # Gets address as UTF-8 string

        # Step 4: Process received telegrams
        if address in meter_list.keys():
            meter_list[address].process_telegram(telegram)

        # Step 5: Profit?
            print(meter_list[address].measurement_log[-1])

        sleep(2)


if __name__ == '__main__':
    # When run from terminal, it powers up the system, and away we go...
    run_system()
