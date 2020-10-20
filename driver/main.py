import serial as port
import sys
import struct
import time

# Definitions import from WMBus_HCI_Spec_V1_6.pdf
IM871A_SERIAL_SOF = 0xA5
DEVMGMT_ID = 0x01
RADIOLINK_ID = 0x02
RADIOLINKTEST_ID = 0x03
HWTEST_ID = 0x04
TEMP_MEM = 0x00

DEVMGMT_MSG_PING_REQ = 0x01
DEVMGMT_MSG_PING_RSP = 0x02
DEVMGMT_MSG_SET_CONFIG_REQ = 0x03
DEVMGMT_MSG_SET_CONFIG_RSP = 0x04
DEVMGMT_MSG_GET_CONFIG_REQ = 0x05
DEVMGMT_MSG_GET_CONFIG_RSP = 0x06
DEVMGMT_MSG_RESET_REQ = 0x07
DEVMGMT_MSG_RESET_RSP = 0x08
DEVMGMT_MSG_FACTORY_RESET_REQ = 0x09
DEVMGMT_MSG_FACTORY_RESET_RSP = 0x0A
DEVMGMT_MSG_GET_OPMODE_REQ = 0x0B
DEVMGMT_MSG_GET_OPMODE_RSP = 0x0C
DEVMGMT_MSG_SET_OPMODE_REQ = 0x0D
DEVMGMT_MSG_SET_OPMODE_RSP = 0x0E
DEVMGMT_MSG_GET_DEVICEINFO_REQ = 0x0F
DEVMGMT_MSG_GET_DEVICEINFO_RSP = 0x10
DEVMGMT_MSG_GET_SYSSTATUS_REQ = 0x11
DEVMGMT_MSG_GET_SYSSTATUS_RSP = 0x12
DEVMGMT_MSG_GET_FWINFO_REQ = 0x13
DEVMGMT_MSG_GET_FWINFO_RSP = 0x14
DEVMGMT_MSG_GET_RTC_REQ = 0x19
DEVMGMT_MSG_GET_RTC_RSP = 0x1A
DEVMGMT_MSG_SET_RTC_REQ = 0x1B
DEVMGMT_MSG_SET_RTC_RSP = 0x1C
DEVMGMT_MSG_ENTER_LPM_REQ = 0x1D
DEVMGMT_MSG_ENTER_LPM_RSP = 0x1E
DEVMGMT_MSG_SET_AES_ENCKEY_REQ = 0x21
DEVMGMT_MSG_SET_AES_ENCKEY_RSP = 0x22
DEVMGMT_MSG_ENABLE_AES_ENCKEY_REQ = 0x23
DEVMGMT_MSG_ENABLE_AES_ENCKEY_RSP = 0x24
DEVMGMT_MSG_SET_AES_DECKEY_REQ = 0x25
DEVMGMT_MSG_SET_AES_DECKEY_RSP = 0x26
DEVMGMT_MSG_AES_DEC_ERROR_IND = 0x27

RADIOLINK_MSG_WMBUSMSG_REQ = 0x01
RADIOLINK_MSG_WMBUSMSG_RSP = 0x02
RADIOLINK_MSG_WMBUSMSG_IND = 0x03
RADIOLINK_MSG_DATA_REQ = 0x04
RADIOLINK_MSG_DATA_RSP = 0x05

RADIOLINKTEST_MSG_START_REQ = 0x01
RADIOLINKTEST_MSG_START_RSP = 0x02
RADIOLINKTEST_MSG_STOP_REQ = 0x03
RADIOLINKTEST_MSG_STOP_RSP = 0x04
RADIOLINKTEST_MSG_STATUS_IND = 0x07

HWTEST_MSG_RADIOTEST_REQ = 0x01
HWTEST_MSG_RADIOTEST_RSP = 0x02


def ping():
    "Ping the USB dongle"
    print(port.to_bytes([IM871A_SERIAL_SOF, DEVMGMT_ID, DEVMGMT_MSG_PING_REQ, 0x0]))
    IM871.write(port.to_bytes([IM871A_SERIAL_SOF, DEVMGMT_ID, DEVMGMT_MSG_PING_REQ, 0x0]))
    print("Ping sent")
    data_received = IM871.read(4)
    print("Ping Response received")
    data_conv = data_received.hex()
    print(data_conv[4:6])


def getdeviceid():
    msg = bytes([IM871A_SERIAL_SOF, DEVMGMT_ID, DEVMGMT_MSG_GET_DEVICEINFO_REQ, 0x0])
    print(msg)
    IM871.write(msg)
    time.sleep(1)
    data_received = IM871.read(12)
    print(data_received.hex())


def getdeviceinfo():
    IM871.write(port.to_bytes([IM871A_SERIAL_SOF, DEVMGMT_ID, DEVMGMT_MSG_GET_CONFIG_REQ, 0x00]))
    print("Config requested")
    time.sleep(2)
    data_received = IM871.read(IM871.in_waiting)
    print(data_received.hex())


def resetmodule():
    msg = bytes([IM871A_SERIAL_SOF, DEVMGMT_ID, DEVMGMT_MSG_RESET_REQ, 0x00])
    IM871.write(msg)
    data_receive = IM871.read(4)
    print(data_receive)


def system_status():
    IM871.write(port.to_bytes([IM871A_SERIAL_SOF, DEVMGMT_ID, DEVMGMT_MSG_GET_SYSSTATUS_REQ, 0x00]))
    print("Status requested")
    time.sleep(2)
    data_received = IM871.read(42)
    print(data_received.hex())


def setup_linkmode():
    # 0x2 = RADIO MODE REQUESTED
    # 0x6 = C1 Format
    IM871.write(port.to_bytes([IM871A_SERIAL_SOF, DEVMGMT_ID, DEVMGMT_MSG_SET_CONFIG_REQ, 0x03, TEMP_MEM, 0x2, 0x6]))
    print("Request linkmode")
    time.sleep(1)
    data_received = IM871.read(4)
    print(data_received.hex())
    IM871.write(port.to_bytes([IM871A_SERIAL_SOF, DEVMGMT_ID, DEVMGMT_MSG_SET_CONFIG_REQ, 0x03, TEMP_MEM, 0x80, 0xb]))
    print("request radio channel T-mode")
    time.sleep(1)
    data_received = IM871.read(4)
    print(data_received.hex())


def enable_enckey():
    # change configuration only temporary
    # enable AES
    IM871.write(port.to_bytes([IM871A_SERIAL_SOF, DEVMGMT_ID, DEVMGMT_MSG_ENABLE_AES_ENCKEY_REQ, 0x02, 0x00, 0x01]))
    print("Enable AES")
    time.sleep(2)
    data_received = IM871.read(5)
    print(data_received.hex())


def set_enckey():
    # change configuration only temporary
    # 1-16 payload: KEY
    IM871.write(port.to_bytes([IM871A_SERIAL_SOF, DEVMGMT_ID, DEVMGMT_MSG_SET_AES_ENCKEY_REQ, 0x11, 0x00, 0x01,
                               0x9A, 0x25, 0x13, 0x9E, 0x32, 0x44, 0xCC, 0x2E, 0x39, 0x1A, 0x8E, 0xF6, 0xB9, 0x15, 0xB6,
                               0x97]))
    print("set AES")
    time.sleep(2)
    data_received = IM871.read(5)
    print(data_received.hex())


def set_deckey():
    IM871.write(
        port.to_bytes([IM871A_SERIAL_SOF, DEVMGMT_ID, DEVMGMT_MSG_SET_AES_DECKEY_REQ, 0x19, 0x1, 0x2C, 0x2D, 0x32, 0x66,
                       0x68, 0x57, 0x30, 0x02, 0x9A, 0x25, 0x13, 0x9E, 0x32, 0x44, 0xCC, 0x2E, 0x39, 0x1A, 0x8E,
                       0xF6, 0xB9, 0x15, 0xB6,
                       0x97]))
    print("Set deckey")
    time.sleep(2)
    data_received = IM871.read(5)
    print(data_received.hex())


def read_data():
    while True:
        data = IM871.read(100)
        datasci = data.hex()
        if datasci[14:22] == '57686632':
            datasci = datasci[6::]
            with open("data_read.txt", "a+") as f:
                f.write(datasci+"\n")
            print(datasci)
    # Look for AES Error indication (3.1.10.4 Manual)
    # if datasci[4:6] == '0x27':
    #   print(datasci)


# def data_handling(data):
#   for


if __name__ == '__main__':
    IM871 = port.Serial(port='/dev/ttyUSB0', baudrate=57600, bytesize=8, parity=port.PARITY_NONE, stopbits=1,
                        timeout=0.3)
    if IM871.isOpen():
        print("Connected to Serial port ttyUSB0")
        # getdeviceid()
        # ping()
        # resetmodule()
        # getdeviceinfo()
        # system_status()
        # setup_linkmode()
        # enable_enckey()
        # set_enckey()
        # set_deckey()
        read_data()
        IM871.close()
    else:
        sys.exit("Failed to open the USB port")
