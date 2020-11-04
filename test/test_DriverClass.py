"""
Tests for IM871-A driver.
Uses mocked tests when not on Gateway.
On Gateway, tests run using hardware peripheral.

"""

import pytest
import os
from unittest import mock

# Import class to be tested
from driver.DriverClass import IM871A

# Data from DriverClass testrun
# Raw USB data:  b'\xa5\x82\x03!D-,\x12P\x00d\x1b\x16\x8d ?\x02\xd9\xf3" Z\x06G\xe3hH\xe4\x0cE"V\x90~P\x1d\xe9\xfdl'
# After conversion:  a5820321442d2c125000641b168d203f02d9f322205a0647e36848e40c452256907e501de9fd6c

@pytest.fixture()
def IM871A_setup():
    USB_Port = '/dev/ttyUSB0'
    return USB_Port

@pytest.fixture()
def IM871A_bad_setup():
    bad_USB_Port = '/somethingrandom/'
    return bad_USB_Port

@pytest.fixture()
def input_data():
    raw_usb_data = b'\xa5\x82\x03!D-,\x12P\x00d\x1b\x16\x8d ?\x02\xd9\xf3" Z\x06G\xe3hH\xe4\x0cE"V\x90~P\x1d\xe9\xfdl'
    processed_data = 'a5820321442d2c125000641b168d203f02d9f322205a0647e36848e40c452256907e501de9fd6c'
    return raw_usb_data, processed_data


### Janus fun and games here ###

def test_vectors():
    """
    Build test set of raw serial data and ascii (processed) data.
    """

    # specify data as
    # (raw bytes, raw bytes as hex in ascii, message expected in pipe)
    t = [(b'\xa5\x82\x03!D-,\x12P\x00d\x1b\x16\x8d ?\x02\xd9\xf3" Z\x06G\xe3hH\xe4\x0cE"V\x90~P\x1d\xe9\xfdl',
          'a5820321442d2c125000641b168d203f02d9f322205a0647e36848e40c452256907e501de9fd6c',
          '21442d2c125000641b168d203f02d9f322205a0647e36848e40c452256907e501de9fd6c\n'), ]
    return t


class PatchSerial:
    """
    Fakes the serial.Serial object.
    Avoids attempts of write/read operations from /dev/tty devices on local machines.
    """

    def __init__(self, read_raw_return):
        self.read_raw_return = read_raw_return

    def close(self):
        return True

    def read(self, num_bytes):
        if num_bytes <= 10:
            # Reading return value from setting config
            # 0xa5 for SOF
            # 0x01 for DEVMGMT_ID
            # 0x04 for DEVMGMT_MSG_SET_CONFIG_RSP
            return b'\xa5\x01\x04'

        elif num_bytes > 10:
            # Reading a raw serial bytes message
            return self.read_raw_return

    def write(self, message_bytes):
        return True


class PipeWriter:
    """
    Fakes the builtin method used to open a pipe and write to it.
    This avoids pipes being opened on local machines.
    """

    def __init__(self):
        self.message = str()
        pass

    def write(self, message):
        # Store the message
        self.message = message
        return True

    def close(self):
        return True


@pytest.fixture
@mock.patch("driver.DriverClass.port.Serial", return_value=PatchSerial(test_vectors()[0][0]), autospec=True)
def patched_driver(mock_obj):
    """
    Make a driver fixture where we've patched out the port.Serial dependency.
    Use unittest to patch (bypass/override) the port.Serial-function (serial.Serial),
    which is used when the driver tries to establish serial connection.
    Also set up that we test on one specific test vector.
    """

    # Instantiate object
    test_port = '/dev/ttyMonster'
    test_pipe = test_port.split('tty')[1] + '_pipe'
    d = IM871A(test_port)

    # Return patched object
    return d


@pytest.mark.skipif(os.uname()[1] == 'raspberrypi', reason="Only run mocked tests when not on Gateway")
def test_constructor_destructor(patched_driver):
    """
    Test construction and destruction of a driver object is OK.
    """

    d = patched_driver              # Get fixture

    # Assert existence of these objects
    assert d.Port
    assert d.pipe == d.Port.split('tty')[1] + '_pipe'

    # When object goes out of scope, destructor is called; we will force this here
    # Expect NO exceptions or errors
    assert d.__del__() is None


@pytest.mark.skipif(os.uname()[1] == 'raspberrypi', reason="Only run mocked tests when not on Gateway")
def test_close(patched_driver):
    d = patched_driver  # Get fixture

    # Closing the port returns None and doesn't raise exception
    # d.close() -> d.IM871A.close() -> (by patch) patch_serial_instance.close()
    assert d.close() is None


@pytest.mark.skipif(os.uname()[1] == 'raspberrypi', reason="Only run mocked tests when not on Gateway")
def test_setup_linkmode(patched_driver):
    d = patched_driver  # Get fixture

    # Assert that linkmode can be set with return True
    assert d.setup_linkmode('c1a')


@pytest.mark.skipif(os.uname()[1] == 'raspberrypi', reason="Only run mocked tests when not on Gateway")
@mock.patch("builtins.open", return_value=PipeWriter(), autospec=True)
def test_read_data(mock_obj, patched_driver):
    """
    Patch out the pipe dependency to an instance of local PipeWriter-type object that we can easily read.
    """

    d = patched_driver  # Get fixture

    # Require that read_data() returns True
    assert d.read_data()

    # Require that read_data() has entered correct message into "pipe"
    assert mock_obj.return_value.message == test_vectors()[0][2]




### Jakob's tests here ###

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


#Not working
#def test_init_open_exception(IM871A_bad_setup):
#    bad_usb_port = IM871A_bad_setup
#    bad_usb_port_driver = IM871A(bad_usb_port)
#    assert bad_usb_port_driver.__init__.__init_open(bad_usb_port) == False