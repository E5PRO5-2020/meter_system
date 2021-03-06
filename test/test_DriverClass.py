"""
Tests for IM871-A driver.
Uses mocked tests when not on Gateway.
On Gateway, tests run using hardware peripheral.

Future dev.:

- Try spec=True to investigate if MagicMock can correctly spec the patched classes and functions.
- E.g. when patching serial.Serial, the MagicMock should appear to have all relevant methods.
- This could eliminate some need for spec'ing our own test doubles (fakes).

"""

import pytest
import os
from unittest import mock
import serial as port  # type: ignore

# Import class to be tested
from driver.DriverClass import IM871A


# Data from DriverClass testrun
# Raw USB data:  b'\xa5\x82\x03!D-,\x12P\x00d\x1b\x16\x8d ?\x02\xd9\xf3" Z\x06G\xe3hH\xe4\x0cE"V\x90~P\x1d\xe9\xfdl'
# After conversion:  a5820321442d2c125000641b168d203f02d9f322205a0647e36848e40c452256907e501de9fd6c

@pytest.fixture()
def IM871A_pipe():
    """
    Fixture that returns a path to use for the pipe
    """
    pipe_path = './'
    return pipe_path


@pytest.fixture()
def input_data():
    """
    Fixture that returns raw usb data, processed data and processed data with errors
    """
    raw_usb_data = b'\xa5\x82\x03!D-,\x12P\x00d\x1b\x16\x8d ?\x02\xd9\xf3" Z\x06G\xe3hH\xe4\x0cE"V\x90~P\x1d\xe9\xfdl'
    processed_data = b'a5820321442d2c125000641b168d203f02d9f322205a0647e36848e40c452256907e501de9fd6c'
    processed_data_bad = b'a5820321442d2c125000641b168d203f02d9f322205a0647e36848e40c452256907e501de9ffff'
    return raw_usb_data, processed_data, processed_data_bad


def is_on_gateway():
    """
    Returns true if this is the gateway
    """
    return os.uname()[1] == 'raspberrypi'


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

    def write(self, message):
        # Store the message
        self.message = message
        return True

    def close(self):
        return True

    def flush(self):
        return True


@pytest.fixture
@mock.patch("builtins.open", return_value=PipeWriter(), autospec=True)      # open fifo object
@mock.patch("driver.DriverClass.port.Serial", return_value=PatchSerial(test_vectors()[0][0]), autospec=True)
@mock.patch("driver.DriverClass.os.mkfifo")                                 # FIFO creation
@mock.patch("driver.DriverClass.im871a_port")                               # Automatic search for USB
def patched_driver(mock_obj_im871a_port, mock_obj_fifo, mock_obj_serial_conn, mock_open):
    """
    Make a driver fixture where we've patched (bypass/override) the port.Serial dependency with our own fake object.
    The port.Serial-function (serial.Serial) is used when the driver tries to establish serial connection.
    Patch os.mkfifo to prevent making FIFO (pipe) in the local OS during object construction.
    Set up that we test on one specific test vector.
    """

    # Instantiate object with a dummy device name
    program_path = '/her'
    d = IM871A(program_path, logOnDestruct=False)

    # Changed implementation, this must be called explicitly now
    d.open_pipe()

    # Ensure correct ordering
    assert type(mock_obj_serial_conn.return_value) is PatchSerial
    assert type(d.fp) is PipeWriter

    # Return patched object
    return d


@pytest.mark.skipif(is_on_gateway(), reason="Don't run mocked tests on Gateway")
def test_constructor_destructor(patched_driver):
    """
    Test construction and destruction of a driver object is OK.
    """

    d = patched_driver  # Get fixture

    # Assert existence of these objects
    # If Port is /dev/ttyReMoni, then require pipe to be named ReMoni_pipe as per spec
    assert d.Port
    assert d.pipe == '/her/IM871A_pipe'
    # Previous path method
    # d.Port.split('tty')[1] + '_pipe'

    # When object goes out of scope, destructor is called; we will force this here
    # Expect NO exceptions or errors
    # assert d.__del__() is None


@pytest.mark.skipif(is_on_gateway(), reason="Don't run mocked tests on Gateway")
def test_close(patched_driver):
    d = patched_driver  # Get fixture

    # Closing the port returns None and doesn't raise exception
    # d.close() -> d.IM871A.close() -> (by patch) patch_serial_instance.close()
    assert d.close() is None


@pytest.mark.skipif(is_on_gateway(), reason="Don't run mocked tests on Gateway")
def test_setup_linkmode(patched_driver):
    d = patched_driver  # Get fixture

    # Assert that linkmode can be set with return True
    assert d.setup_linkmode('c1a')


#@pytest.mark.skip
@pytest.mark.skipif(is_on_gateway(), reason="Don't run mocked tests on Gateway")
def test_read_data(patched_driver):
    """
    Already Patch out the pipe dependency to an instance of local PipeWriter-type object that we can easily read.
    """

    d = patched_driver  # Get fixture

    # Require that read_data() returns True
    assert d.read_data()

    # Require that read_data() has entered correct message into "pipe"
    assert d.fp.message == test_vectors()[0][2]


# Can object be instantiated
@pytest.mark.skipif(not is_on_gateway(), reason="Only run this test on Gateway")
def test_object_instatiated_true_RPi(IM871A_pipe):
    """
    Testing if an object of the type IM871A can be instantiated
    """
    path_pipe = IM871A_pipe
    test_driver = IM871A(path_pipe)
    assert test_driver.is_open()


@pytest.mark.skipif(not is_on_gateway(), reason="Only run this test on Gateway")
def test_read_data_RPi(IM871A_pipe, input_data):
    """
    Testing if it's possible to read from the pipe
    """
    path_pipe = IM871A_pipe
    test_driver = IM871A(path_pipe)
    test_driver.setup_linkmode('c1a')

    # Open pipe
    test_driver.open_pipe()

    assert test_driver.read_data()

    # Ensure that data was received at the other end of the pipe
    p = os.path.abspath('test/pipe_data.txt')
    fp = open(p, 'r')
    val_read_from_serial = fp.readline()
    assert val_read_from_serial


@pytest.mark.skipif(not is_on_gateway(), reason="Only run this test on Gateway")
def test_CRC_check_succes_RPi(IM871A_pipe, input_data):
    """
    Tests if a succesfull CRC-check returns true
    """
    path_pipe = IM871A_pipe
    test_driver_CRC = IM871A(path_pipe, logOnDestruct=False)
    raw_data, processed_data, processed_data_bad = input_data

    # This is a way to test a private method inside the IM871A object
    assert test_driver_CRC._IM871A__CRC16_check(processed_data)


@pytest.mark.skipif(not is_on_gateway(), reason="Only run this test on Gateway")
def test_CRC_check_fails_RPi(IM871A_pipe, input_data):
    """
    Tests if a unsuccesfull CRC-check returns false
    """
    path_pipe = IM871A_pipe
    test_driver_CRC = IM871A(path_pipe, logOnDestruct=False)
    raw_data, processed_data, processed_data_bad = input_data

    # This is a way to test a private method inside the IM871A object
    assert test_driver_CRC._IM871A__CRC16_check(processed_data_bad) is False


@pytest.mark.skipif(not is_on_gateway(), reason="Only run this test on Gateway")
def test_usb_essentials_RPi(IM871A_pipe):
    """
    Testing if it is possible to open the pipe and reset the USB-module
    """
    # Closing port to test open function
    path_pipe = IM871A_pipe
    test_driver = IM871A(path_pipe, logOnDestruct=False)

    assert test_driver.is_open() is True
    # Testing reset
    assert test_driver.reset_module() is True


@pytest.mark.skipif(not is_on_gateway(), reason="Only run this test on Gateway")
def test_linkmodes_RPi(IM871A_pipe):
    """
    Testing all the linkmodes possible with IM871A
    """
    # Instantiate DriverClass
    path_pipe = IM871A_pipe
    test_driver = IM871A(path_pipe, logOnDestruct=False)
    # Testing ping
    assert test_driver.ping() is True

    # Testing Linkmode. Last mode is 'c1a' to be able to test read_data()
    assert test_driver.setup_linkmode('s1') is True
    assert test_driver.setup_linkmode('s1m') is True
    assert test_driver.setup_linkmode('s2') is True
    assert test_driver.setup_linkmode('t1') is True
    assert test_driver.setup_linkmode('t2') is True
    assert test_driver.setup_linkmode('c2a') is True
    assert test_driver.setup_linkmode('c2b') is True
    assert test_driver.setup_linkmode('c1b') is True
    assert test_driver.setup_linkmode('ha') is False
    assert test_driver.setup_linkmode('') is False
    assert test_driver.setup_linkmode('c1a') is True
