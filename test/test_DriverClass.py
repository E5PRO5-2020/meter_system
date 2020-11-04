import time
import pytest
import driver.DriverClass
from driver.DriverClass import IM871A
import os


# Data from DriverClass testrun
# Raw USB data:  b'\xa5\x82\x03!D-,\x12P\x00d\x1b\x16\x8d ?\x02\xd9\xf3" Z\x06G\xe3hH\xe4\x0cE"V\x90~P\x1d\xe9\xfdl'
# After conversion:  a5820321442d2c125000641b168d203f02d9f322205a0647e36848e40c452256907e501de9fd6c

@pytest.fixture()
def IM871A_setup():
    USB_Port = '/dev/ttyUSB0'
    return USB_Port

@pytest.fixture()
def IM871A_bad_setup():
    bad_USB_Port = 'somethingrandom'
    return bad_USB_Port

@pytest.fixture()
def input_data():
    raw_usb_data = b'\xa5\x82\x03!D-,\x12P\x00d\x1b\x16\x8d ?\x02\xd9\xf3" Z\x06G\xe3hH\xe4\x0cE"V\x90~P\x1d\xe9\xfdl'
    processed_data = 'a5820321442d2c125000641b168d203f02d9f322205a0647e36848e40c452256907e501de9fd6c'
    return raw_usb_data, processed_data

def test_driver(IM871A_setup, input_data):
    if os.uname()[1] == 'raspberrypi':
        # Instantiate DriverClass
        USB_Port = IM871A_setup
        test_driver = IM871A(USB_Port)

        raw_data, processed_data = input_data

        # Testing ping
        assert test_driver.ping() == True

        # Testing Linkmode. Last mode is 'c1a' to be able to test read_data()
        assert test_driver.setup_linkmode('s1') == True
        assert test_driver.setup_linkmode('s1m') == True
        assert test_driver.setup_linkmode('s2') == True
        assert test_driver.setup_linkmode('t1') == True
        assert test_driver.setup_linkmode('t2') == True
        assert test_driver.setup_linkmode('c2a') == True
        assert test_driver.setup_linkmode('c2b') == True
        assert test_driver.setup_linkmode('c1b') == True
        assert test_driver.setup_linkmode('ha') == False
        assert test_driver.setup_linkmode('') == False
        assert test_driver.setup_linkmode('c1a') == True


        # Missing Line 80 - return true if FIFO is created
        #assert test_Driver.__init__(USB_Port) == True
        # Being reworked, not testing


        # Missing Line 84 - __create_pipe() print(err)
        # Being reworked, not testing


        # Missing Line 133-153 - read_data()
        # Maybe make a file the reader can read from, instead of the USB
        assert processed_data == raw_data.hex()


        # Missing Line 161-163 - ping() port.SerialTimeoutException

        # Missing Line 169-171 - ping() port.SerialException

        # Missing Line 179-180 - ping() No response from module. ping returns false

        # Missing Line 191-193 - reset_module() port.SerialTimeoutException (returns false)

        # Missing Line 199-201 - reset_module() port.SerialException (Returns false)

        # Missing Line 209-210 - reset_module() Module wont reset (Returns false)

        # Missing Line 227-229 - setup_linkmode() port.SerialTimeoutException (Returns false)

        # Missing Line 235-237 - setup_linkmode() port.SerialException (Returns false)

        # Missing Line 245-246 - setup_linkmode() setup failed (Returns false)

        # Missing Line 259-261 - open() port.SerialException (Returns false)

        # Testing read_data. Only returns when read from pipe.
        # ! To test this 'cat' the pipe
        # assert USBport.read_data() == True

        # Closing port to test open function
        test_driver.close()
        assert test_driver.open() == True

        # Testing reset
        assert test_driver.reset_module() == True

        # Testing several functions
        #assert initialize() == True

def test_init_open_exception(IM871A_bad_setup):
    bad_usb_port = IM871A_bad_setup
    bad_usb_port_driver = IM871A()
    assert bad_usb_port_driver.__init__(bad_usb_port_driver, bad_usb_port) == False