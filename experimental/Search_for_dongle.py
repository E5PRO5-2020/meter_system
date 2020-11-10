"""
Experimental:
Search for IMST IM871a WMbus dongle.
Looking at udev rules in Linux:
Default OS placed in /lib/udev/rules.d - These cannot be changed. If user want to create custom udev rules
this should be placed in /etc/udev/rules.d

Rules placed in /etc have priority over /lib.

Specific for serial communication rules OS uses 60-serial.rules
where one line define location and name for the link to tty PORT used for specific device.

ENV{.ID_PORT}=="?*", SYMLINK+="serial/by-id/$env{ID_BUS}-$env{ID_SERIAL}
    -if$env{ID_USB_INTERFACE_NUM}-port$env{.ID_PORT}"

Looking at the line its clear that the link is placed in /dev/serial/by-id. Furthermore the name of the link
is given by the ID_BUS, ID_SERIAL ,ID_USB_INTERFACE_NUM, ID_PORT.
At the moment it's believed but not confirmed that ID_USB_INTERFACE_NUM and ID_PORT is subject to change
if different port is assigned.

This method first confirms the directory /dev/serial/by-id exist, afterwards looks for iM871a in any link name.
If any the method will return the absolute path. If Several links contains "iM871a" the method will return path
to first encountered link.

"""

import os
import serial as port


def im871a_port() -> str:
    directory = "/dev/serial/by-id"
    if os.path.exists("/dev/serial/by-id"):
        for cur_path, directories, files in os.walk(directory):
            if "iM871A" in files[0]:
                return os.path.join(directory, cur_path, files[0])
            else:
                raise Exception("No IM871A-Link found in /dev/serial/by-id")
    else:
        raise Exception("No serial devices are found.")


if __name__ == '__main__':
    try:
        path = im871a_port()
    except Exception as err:
        print(err)
    # Stolen lines from the IM871a-driver to test the returned path.
    try:
        IM871 = port.Serial(port=path, baudrate=57600, bytesize=8, parity=port.PARITY_NONE, stopbits=1, timeout=0)

    except (ValueError, port.SerialException) as err:
        print(err)

    while True:
        try:
            data = IM871.read(100)
            if len(data) != 0:
                data = data.hex()
                print(data)
        except (AttributeError, port.SerialException) as err:
            print(err)
