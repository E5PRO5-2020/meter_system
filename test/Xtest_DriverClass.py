import pytest
from DriverClass import IM871A
import time


def test_driver():
    # Instantiate DriverClass 
    USBport = IM871A('/dev/ttyUSB0')

    # Testing ping
    assert USBport.ping() == True

    # Testing Linkmode. Last mode is 'c1a' to be able to test read_data()
    assert USBport.setup_linkmode('s1') == True
    assert USBport.setup_linkmode('s1m') == True
    assert USBport.setup_linkmode('s2') == True
    assert USBport.setup_linkmode('t1') == True
    assert USBport.setup_linkmode('t2') == True
    assert USBport.setup_linkmode('c2a') == True
    assert USBport.setup_linkmode('c2b') == True
    assert USBport.setup_linkmode('c1b') == True
    assert USBport.setup_linkmode('ha') == False
    assert USBport.setup_linkmode('') == False
    assert USBport.setup_linkmode('c1a') == True

    # Testing read_data. Only returns when read from pipe.
    # ! To test this 'cat' the pipe
    assert USBport.read_data() == True

    # Closing port to test open function
    USBport.close()
    assert USBport.open() == True

    # Testing reset
    assert USBport.reset_module() == True


def test1() -> bool:
    """
    Testing several functions
    """
    USB_port_0 = IM871A('/dev/ttyUSB0')
    check1 = USB_port_0.reset_module()      
    # Needs time after reset before being able to setup linkmode
    time.sleep(3)
    check2 = USB_port_0.setup_linkmode('c1a')
    
    if(check1 & check2):
        return True
    return False
