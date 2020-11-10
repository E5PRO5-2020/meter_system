"""
Contains main loop which instantiates and runs the entire system

"""
from mqtt.MqttClient import MqttClient, donothing_onpublish
from collections import deque
from time import sleep

# Global double-ended queue object for communication from mqtt thread
dq = deque(maxlen=1)


def run_system():

    def on_message_callback(client, userdata, message):
        try:
            msg = message.payload.decode("utf-8")
            topic = message.topic
            dq.appendleft((topic, msg))
        except:
            pass

    # instantiate Mqtt
    recalc = MqttClient("ListenToRecalc", on_message_callback, donothing_onpublish, param_settings='mqtt')
    recalc.subscribe("testtopic")

    # start thread, runs in background
    recalc.loop_start()

    # Main event loop
    while True:

        # Step 1: Check for message from recalc
        try:
            print(dq.pop())
        except:
            pass

        # Step 2: Process message and update data structure

        # Step 3: Read all data from driver via FIFO

        # Step 4: Process received telegrams

        # Step 5: Profit?

        sleep(2)


if __name__ == '__main__':
    run_system()
