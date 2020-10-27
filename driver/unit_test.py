import pytest
from DriverClass import IM871A
from main import test1

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
    #assert USBport.read_data() == True

    # Closing port to test open function
    USBport.close()
    assert USBport.open() == True

    # Testing reset
    assert USBport.reset_module() == True

    # Testing several functions
    assert test1() == True
    
   

