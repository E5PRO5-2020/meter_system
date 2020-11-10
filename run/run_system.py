"""
Contains main loop which instantiates and runs the entire system
:Authors: Steffen, Janus
:Date: 10 November 2020

Ver. 0.1: Build main loop with queue and Mqtt startup

"""

from mqtt.MqttClient import MqttClient, donothing_onpublish
from collections import deque
from time import sleep

# Global double-ended queue, atomic object for communication from mqtt thread
dq = deque(maxlen=1)


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
        if dq:
            print(dq.pop())

        # Step 2: Process message and update data structure
        # Split the topic and message to figure out what to do

        # Step 3: Read all data from driver via FIFO
        # Tap the FIFO

        # Step 4: Process received telegrams

        # Step 5: Profit?

        sleep(2)


if __name__ == '__main__':
    # When run from terminal, it powers up the system, and away we go...
    run_system()
