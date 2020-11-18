"""
Generic driver class for WM-Bus USB-dongle IM871A 
*************************************************
:Platform: Python 3.5.10 on Linux
:Synopsis: This module implements a class for communication with IM871A module.
:Authors: Steffen Breinbjerg, Thomas Serup
:Date: 21 October 2020


Version history
===============

- Ver 1.0: Set up driver.
- Ver 1.1: Implemented seperate 'open pipe' handler. Added pipe path as 2.nd argument.
- Ver 1.2: Implemented CRC-16 check.
- Ver 1.3: Logging exceptions to syslog instead of printing to console.
- Ver 1.4: No longer takes USB port as argument. Function for handling port is located in 'utils/Search_for_dongle'.  



Link Modes
===============
IM871A is able to run in different modes. Default mode is S2.


+-----------------------+----------+-------------------------------------------------------+
| Mode                  | Argument | Description                                           |
+=======================+==========+=======================================================+
| S1                    | s1       | Stationary, one way communication                     |
+-----------------------+----------+-------------------------------------------------------+
| S1-m                  | s1m      | S1 with shorter header                                |
+-----------------------+----------+-------------------------------------------------------+
| S2                    | s2       | Stationary, bidirectional communication               | 
+-----------------------+----------+-------------------------------------------------------+
| T1                    | t1       | Frequent transmit, one way communication              | 
+-----------------------+----------+-------------------------------------------------------+
| T2                    | t2       | Frequent transmit, bidirectional communication        |  
+-----------------------+----------+-------------------------------------------------------+
| C1, Telegram Format A | c1a      | Compact, one way communication. No fixed length       | 
+-----------------------+----------+-------------------------------------------------------+
| C1, Telegram Format B | c1b      | Compact, one way communication. Fixed length          | 
+-----------------------+----------+-------------------------------------------------------+
| C2, Telegram Format A | c2a      | Compact, bidirectional communication. No fixed length | 
+-----------------------+----------+-------------------------------------------------------+
| C2, Telegram Format B | c2b      | Compact, bidirectional communication. Fixed length    | 
+-----------------------+----------+-------------------------------------------------------+


"""
import serial as port   # type: ignore
import sys
import struct
import os
import subprocess
import errno
from binascii import hexlify
from struct import pack
from utils.log import get_logger
from typing import Union
from utils.Search_for_dongle import im871a_port


# Get logger instance
log = get_logger()

# Definitions imported from WMBus_HCI_Spec_V1_6.pdf
IM871A_SERIAL_SOF = 0xA5
DEVMGMT_ID = 0x01
TEMP_MEM = 0x00
DEVMGMT_MSG_PING_REQ = 0x01
DEVMGMT_MSG_PING_RSP = 0x02
DEVMGMT_MSG_SET_CONFIG_REQ = 0x03
DEVMGMT_MSG_SET_CONFIG_RSP = 0x04
DEVMGMT_MSG_RESET_REQ = 0x07
DEVMGMT_MSG_RESET_RSP = 0x08


class IM871A:  
    """
    Implementation of a driver class for IM871A USB-dongle. 
    Takes 1 argument1:
    - The path to where to put the pipe, e.g. the program directory. 
    """ 

    def __init__(self, program_path):

        try:
            self.Port = im871a_port()                       # Path the USB-port used
        except Exception as e:
            log.exception(e)
            exit(1)

        self.pipe = program_path + '/IM871A_pipe'           # Pipe name and place to put it
        self.__init_open(self.Port)                         # Initially creates and opens port
        self.__create_pipe(self.Port)                       # Initially creates 'named pipe' file
        self.fp = None                                      # Pointer to pipe

    def __create_pipe(self, pipe: str) -> bool:
        """
        Creates named pipe for output when class is instantiated, if no pipe exists.
        Pipe is named after which USB-port is used.
        """
        FIFO = self.pipe
        try:
            os.mkfifo(FIFO)
            return True

        except OSError as err:
            # If error is 'File exists' don't show error
            # If error is 'File exists' don't show error
            if err.errno != errno.EEXIST:
                log.exception(err)
            return False



    def __init_open(self, Port: str) -> bool:
        """
        Initially creates and open serial communication with USB-dongle.
        Takes the port path as input.
        This function is only run once when class is instantiated. 
        If port is closed after instantiation, use open() function to reopen port.
        """       
        try:
            self.IM871 = port.Serial(port=Port, baudrate=57600, bytesize=8, parity=port.PARITY_NONE, stopbits=1, timeout=0)
            return True

        except (ValueError, port.SerialException) as err:
            log.exception(err)
            return False


    def is_open(self):
        try:
            # Will return true if object exists and is opened.
            try_val = self.IM871.isOpen()
            return try_val
        except AttributeError as err:
            log.exception(err)
            # Will return False because object doesn't exist.
            return False


    def __string_to_hex(self, argument: str) -> Union[int, bytes]:
        """
        Convert 'mode' argument into bytes. Returns '0xa' if no valid input.
        Function is used in 'setup_linkmode()'.
        """
        switcher = {
            's1' : 0x0, 
            's1m': 0x1, 
            's2' : 0x2, 
            't1' : 0x3, 
            't2' : 0x4, 
            'c1a': 0x6, 
            'c1b': 0x7, 
            'c2a': 0x8, 
            'c2b': 0x9
            }
        return switcher.get(argument, 0xa)



    def __CRC16_check(self, message: bytes) -> bool:
        """
        Argument must be the entire message from IM871-A as byte string
        Function returns TRUE if the check sum matches the expected CRC16 value
        """
        Checksum = message[-4:]                         # Store the expected CRC16 value
        data = message[2:-4]                            # Removes SOF field and CRC16 value

        hex_radix = 16
        g = 0x8408                                      # Generator polynomial, g(x)
        crc = 0xFFFF                                    # Init value for CCITT CRC16

        for byte in range(0, len(data), 2):             # Loop over all bytes in message
            b = int(data[byte:byte + 2], hex_radix)     # Make byte value from hex digits

            for _ in range(0, 8):                       # Repeat for 8 bits in a byte
                if (b & 1) ^ (crc & 1):                 # Is there a remainder for division by the poly for this bit?
                    crc = (crc >> 1) ^ g                # Get remainder from division
                else:
                    crc >>= 1                           # Just advance to next bit in division
                b >>= 1                                 # Move on to next bit in this byte of the message

        crc = crc ^ 0xFFFF                              # Perform final complement
        crc16 = hexlify(pack('<H', crc))                # CRC16 as little-endian

        if Checksum == crc16:                           # Check if sum matches expected CRC16 value
            return True
        else:
            return False



    def __pipe_data(self, data) -> bool:
        """
        Open the pipe, try to send data to pipe and close the pipe again.
        Returns a bool to verify if data is sent to pipe.
        """ 
        try:
            self.fp.write(data + os.linesep)
            try:
                self.fp.flush()
            except Exception as err:
                log.error(err)
                log.error("Broken pipe detected, goodbye!")
                #exit()
            return True

        except Exception as err:
            log.error(err)
            return False



    def open_pipe(self) -> bool:
        """ 
        Open up the pipe. Blocks until pipe is opened in the other end.
        """
        try:
            self.fp = open(self.pipe, "w")
            return True
        
        except IOError as err:
            log.exception(err)
            return False           



    def read_data(self) -> bool:
        """
        Read single dataframe from meters sending with the specified link mode.
        Function is blocking until data arrives.
        Send data into 'named pipe' (USBx_pipe).
        Removes the WM-Bus frame before sending data to pipe.
        """   
        while True:
            try:
                data = self.IM871.read(100)
            except (AttributeError, port.SerialException) as err:
                log.exception(err)
                return False
            
            if len(data) != 0:
                if self.__CRC16_check(hexlify(data)):
                    data_conv = data.hex()
                    
                    # Output to named pipe
                    if self.__pipe_data(data_conv[6::]):
                        return True
                    else:                                            
                        return False
        

    
    def ping(self) -> bool:
        """
        Ping the WM-Bus module to check if it's alive.
        """
        try:
            self.IM871.write(port.to_bytes([IM871A_SERIAL_SOF, DEVMGMT_ID, DEVMGMT_MSG_PING_REQ, 0x0]))
        except (AttributeError, port.SerialTimeoutException) as err:
            log.exception(err)
            return False

        # Looking for response message from IM871A
        for _ in range(0, 500):
            try:
                data = self.IM871.read(10)
            except port.SerialException as err:
                log.exception(err)
                return False
            data_conv = data.hex()
            # Looking for Endpoint-ID and Msg-ID in response
            if(data_conv[3:6] == "102"):
                return True

        # If no response message arrives        
        return False



    def reset_module(self) -> bool:
        """
        Reset the WM-Bus module.
        The reset will be performed after approx. 500ms.
        """ 
        try:
            self.IM871.write([IM871A_SERIAL_SOF, DEVMGMT_ID, DEVMGMT_MSG_RESET_REQ, 0x00])
        except (AttributeError, port.SerialTimeoutException) as err:
            log.exception(err)
            return False

        # Looking for response message from IM871A    
        for _ in range(0, 500):
            try:
                data = self.IM871.read(10)
            except port.SerialException as err:
                log.exception(err)
                return False
            data_conv = data.hex()
            # Looking for Endpoint-ID and Msg-ID in response
            if(data_conv[3:6] == "108"):
                return True

        # If no response message arrives
        return False



    def setup_linkmode(self, mode: str) -> bool:
        """
        Setup link mode for communication with meter. 
        Takes the link mode as argument.
        If no Link Mode is set, default is 'S2'
        """
        # Converting mode-string to byte
        Mode = self.__string_to_hex(mode)
        if(Mode == 0xa):
            return False
        try:
            self.IM871.write(port.to_bytes([IM871A_SERIAL_SOF, DEVMGMT_ID, DEVMGMT_MSG_SET_CONFIG_REQ, 0x03, TEMP_MEM, 0x2, Mode]))
        except (AttributeError, port.SerialTimeoutException) as err:
            log.exception(err)
            return False

        # Looking for responce message from IM871A     
        for _ in range(0, 500):
            try:
                data = self.IM871.read(10)
            except port.SerialException as err:
                log.exception(err)
                return False
            data_conv = data.hex()
            # Looking for Endpoint-ID and Msg-ID in response
            if(data_conv[3:6] == "104"):
                return True

        # If no responce message arrives
        return False
        


    def open(self) -> bool:
        """
        Opens the port if port has been closed.
        It opens with the path given when instantiating the class.
        Also open the pipe.
        """
        
        # Re-open port to IM871A
        try:
            self.IM871.open()
            return True
        except (AttributeError, port.SerialException) as err:
            log.exception(err)
            return False
        # Re-open pipe
        self.open_pipe()



    def close(self):
        """
        Close the connection to IM871A, and the pipe.
        """
        self.fp.close()
        self.IM871.close()



    def __del__(self):
        """
        Destructor for closing when going out of scope.
        Closes port and pipe.
        """
        log.info("IM871A-Driver stopped!")
        self.fp.close()
        self.close()