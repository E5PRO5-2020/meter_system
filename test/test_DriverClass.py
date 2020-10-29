import time
import pytest
import driver.DriverClass
from driver.DriverClass import IM871A

@pytest.fixture()
def IM871A_setup():
    USB_Port = '/dev/ttyUSB0'
    return USB_Port



def test_driver(IM871A_setup):
    # Instantiate DriverClass 
    USB_Port = IM871A_setup
    test_Driver = IM871A(USB_Port)

    # Testing ping
    assert test_Driver.ping() == True

    # Testing Linkmode. Last mode is 'c1a' to be able to test read_data()
    assert test_Driver.setup_linkmode('s1') == True
    assert test_Driver.setup_linkmode('s1m') == True
    assert test_Driver.setup_linkmode('s2') == True
    assert test_Driver.setup_linkmode('t1') == True
    assert test_Driver.setup_linkmode('t2') == True
    assert test_Driver.setup_linkmode('c2a') == True
    assert test_Driver.setup_linkmode('c2b') == True
    assert test_Driver.setup_linkmode('c1b') == True
    assert test_Driver.setup_linkmode('ha') == False
    assert test_Driver.setup_linkmode('') == False
    assert test_Driver.setup_linkmode('c1a') == True

    # Missing Line 80 - return true if FIFO is created
    #assert test_Driver.__init__(USB_Port) == True

    # Missing Line 84 - __create_pipe() print(err)

    # Missing Line 100-102 - __init_open exception

    # Missing Line 133-151 - read_data()
    # Maybe make a file the reader can read from, instead of the USB

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
    test_Driver.close()
    assert test_Driver.open() == True

    # Testing reset
    assert test_Driver.reset_module() == True

    # Testing several functions
    #assert initialize() == True
