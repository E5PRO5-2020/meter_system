"""
Parse Kamstrup OmniPower wm-bus telegrams
*****************************************

:platform: Python 3.5.10 on Linux, OS X
:synopsis: Implements parsing functionality for C1 telegrams and log handling for data series
:author: Janus Bo Andersen
:date: 28 October 2020

Version history
===============

- Ver 1.0: Set up parser and decryption. Janus.
- Ver 2.0: Implement CRC16, timezone. Janus.
- Ver 2.1: More robust exception handling, parse ELL-SN. Janus
- Ver 2.2: Utilize new MeterMeasurement.is_empty() in validation during parsing. Janus


Overview
========

- This module implements parsing for the Kamstrup OmniPower meter, single-phase.
- The meter sends wm-bus C1 (compact one-way) telegrams.
- Telegrams on wm-bus are little-endian, i.e. LSB first.
- The meter sends 1 long and 7 short telegrams, and then repeats.
- Long telegrams include data record headers (DRH) and data, that is DIF/VIF codes + data.
- Short telegrams only include data.

Telegram fields
===============

In a telegram C1 telegram, the data fields are:

+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
| # | Byte# | Bytes | M-bus field | Description                                 | Expected value (little-endian)  |
+===+=======+=======+=============+=============================================+=================================+
| 0 | 0     | 1     | L           | Telegram length                             | 0x27 (39 bytes, short frame), or|
|   |       |       |             |                                             | 0x2D (45 bytes, long frame)     |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
| 1 | 1     | 1     | C           | Control field (type and purpose of message) | 0x44 (SND_NR)                   |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
| 2 | 2-3   | 2     | M           | Manufacturer ID (official ID code)          | 0x2D2C (KAM)                    |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
| 3 | 4-7   | 4     | A           | Address (meter serial number)               | 0x57686632 (big-endian:32666857)|
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
| 4 | 8     | 1     | Ver.        | Version number of the wm-bus firmware       | 0x30                            |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
| 5 | 9     | 1     | Medium      | Type / medium of meter                      | 0x02 (Electricity)              |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
| 6 | 10    | 1     | CI          | Control Information                         | 0x8D (Extended Link Layer 2)    |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
| 7 | 11    | 1     | CC          | Communication Control                       | 0x20 (Slow response sync.)      |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
| 8 | 12    | 1     | ACC         | Access field                                | Varies                          |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
| 9 | 13-16 | 4     | AES CTR / SN| AES counter (Session number)                | Varies, see below               |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
|10 | 17-39 | 23    | Data        | Contains AES-encrypted data frame,          | Encrypted data                  |
|   | 17-45 | 29    |             | varying for short and long frames           |                                 |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
|11 |       | 2     | CRC16       | CRC16 check                                 |                                 |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+

The fields 0-9 of the telegram can be unpacked using the little-endian format `<BBHIBBBBB`, where

- `<` marks little-endian,
- `B` is an unsigned 1 byte (char),
- `H` is an unsigned 2 byte (short),
- `I` is an unsigned 4 byte (int)

AES counter / Session number
============================

The AES_CTR / Extended Link Layer SN field (ELL-SN) is is structured as per EN 13757-4, p. 54.

The example shows ELL-SN value of 0x01870320 (little-endian) -> 0x20038701 (big-endian). Bit readout:

+---------+-----------+-----------+-----------+-----------+
|Byte:    | 3         | 2         | 1         | 0         |
+=========+===========+===========+===========+===========+
|Hex:     | 0x20      | 0x03      | 0x87      | 0x01      |
+---------+-----------+-----------+-----------+-----------+
|Binary:  | 0010 0000 | 0000 0011 | 1000 0111 | 0000 0001 |
+---------+-----------+-----------+-----------+-----------+

Should give the following slicing and interpretation:

+---------+-------+---------------------------------+---------+
|Bits:    | 31-29 | 28-04                           | 03-00   |
+=========+=======+=================================+=========+
|Field:   | ENC   | Time                            | Session |
+---------+-------+---------------------------------+---------+
|Example: | 001   | 0 0000 0000 0011 1000 0111 0000 | 0001    |
+---------+-------+---------------------------------+---------+
|Hex:     | 0x1   | 0x3870 (14448)                  | 0x1     |
+---------+-------+---------------------------------+---------+

- ENC (Encryption): 0 -> No encryption, 1 -> AES-CTR mode, higher -> reserved.
- Time: Minute counter since 01/01/2013 (?), or since meter started, requires RTC set on meter. \
  So time measurement was taken about 10 days after the meter was started.
- Session: Incremented by meter for each transmission, unless using partial/fractured frames.

Parsing. The whole ELL-SN field is read out and masks are used to extract fields.


Telegram examples
=================
Encrypted short telegrams:

+---+---+------+----------+---+---+---+---+---+----------+----------------------------------------------------+------+
|L  |C  |M     |A         |Ver|Med|CI |CC |ACC|AES CTR   |Encrypted payload                                   |CRC 16|
+===+===+======+==========+===+===+===+===+===+==========+====================================================+======+
|27 |44 |2D 2C |5768 6632 |30 |02 |8D |20 |2E |2187 0320 |D3A4F149 B1B8F578 3DF7434B 8A66A557 86499ABE 7BAB59 |xxxx  |
+---+---+------+----------+---+---+---+---+---+----------+----------------------------------------------------+------+
|27 |44 |2d 2c |5768 6632 |30 |02 |8d |20 |63 |60dd 0320 |c42b87f4 6fc048d4 2498b44b 5e34f083 e93e6af1 617631 |3d9c  |
+---+---+------+----------+---+---+---+---+---+----------+----------------------------------------------------+------+
|27 |44 |2d 2c |5768 6632 |30 |02 |8d |20 |8e |11de 0320 |188851bd c4b72dd3 c2954a34 1be369e9 089b4eb3 858169 |494e  |
+---+---+------+----------+---+---+---+---+---+----------+----------------------------------------------------+------+

Encrypted long telegrams:

+---+---+------+----------+---+---+---+---+---+----------+------------------------------------------------------------------+------+
|L  |C  |M     |A         |Ver|Med|CI |CC |ACC|AES CTR   |Encrypted payload                                                 |CRC 16|
+===+===+======+==========+===+===+===+===+===+==========+==================================================================+======+
|2D |44 |2D 2C |5768 6632 |30 |02 |8D |20 |64 |61DD 0320 |38931d14 b405536e 0250592f 8b908138 d58602ec a676ff79 e0caf0b1 4d |0e7d  |
+---+---+------+----------+---+---+---+---+---+----------+------------------------------------------------------------------+------+


Decryption
==========
- The wireless m-bus on OmniPower uses AES-128 Mode CTR (if enabled, otherwise no encryption).
- See EN 13757-4:2019, p. 54, as ELL (Ext. Link-Layer) with ENC = 0x1 => AES-CTR.
- A decryption prefix (initial counter block) is built from some of the fields.
- See table 54 on p. 55 of EN 13757-4:2019.


It can be packed using the format `<HIBBBIB`.

+-----+---------+---+---+---+---------+-----+----+
|M    |A        |Ver|Med|CC |AES_CTR  |FN   |BC  |
+=====+=========+===+===+===+=========+=====+====+
|2D2C |57686632 |30 |02 |20 |21870320 |0000 |00  |
+-----+---------+---+---+---+---------+-----+----+

- AES Prefix (initialization vector): Fields M, ..., AES_CTR, FN.
- FN: frame number (frame # sent by meter within same session number, in case of multi-frame transmissions).
- AES Counter: BC
- BC: Block counter (encryption block number, counts up for each 16 byte block decrypted within the telegram).


Decrypted payload examples
==========================

The interpretation of the fields in the OmniPower is

+----------+---------------+----------------+--------------------+--------------------------------------+-----------+
| Field    | Kamstrup name | Data fmt (DIF) | Value type (VIF/E) | VIF/E meaning                        | DIF VIF/E |
+==========+===============+================+====================+======================================+===========+
| Data 1   | A+            | 32-bit uint    | Energy, 10^1 Wh    | Consumption from grid, accum.        | 04  04    |
+----------+---------------+----------------+--------------------+--------------------------------------+-----------+
| Data 2   | A-            | 32-bit uint    | Energy, 10^1 Wh    | Production to grid, accum.           | 04  84 3C |
+----------+---------------+----------------+--------------------+--------------------------------------+-----------+
| Data 3   | P+            | 32-bit uint    | Power,  10^0 W     | Consumption from grid, instantan.    | 04  2B    |
+----------+---------------+----------------+--------------------+--------------------------------------+-----------+
| Data 4   | P-            | 32-bit uint    | Power,  10^0 W     | Production to grid, instantan.       | 04  AB 3C |
+----------+---------------+----------------+--------------------+--------------------------------------+-----------+

Transport layer control information fields (TPL-CI), ref. EN 13757-7:2018, p. 17, introduce Application Layer (APL) as:

- 0x78 with full frames (Response from device, full M-Bus frame)
- 0x79 with compact frames (Response from device, M-Bus compact frame)

Data integrity check (CRC16)
____________________________
The first 2 bytes (16 bits) of a payload is always the CRC16 value of the sent message.
This value must be checked versus CRC16 calculated on the received payload.


Decrypted short telegram payload
________________________________

+------+-------+----------------+-----------+---------+---------+---------+---------+
|CRC16 |TPL-CI |Data fmt. sign. |CRC16 data |Data 1   |Data 2   |Data 3   |Data 4   |
+======+=======+================+===========+=========+=========+=========+=========+
|1170  |79     |138C            |4491       |CE000000 |00000000 |03000000 |00000000 |
+------+-------+----------------+-----------+---------+---------+---------+---------+

Measurement data starts at byte 7, and can easily be extracted using `<IIII` little-endian format.

In this example, 206 10^1 Wh (2.06 kWh) have been consumed, and the current power draw is 3 10^0 W (0.003 kW).


Decrypted long telegram payload
_______________________________

In this kind of telegram, the DRHs are included.

+------+-------+----------+---------+---------------+---------+----------+---------+----------+---------+
|CRC16 |TPL-CI |DIF/VIF 1 |Data 1   |DIF/VIF/VIFE 2 |Data 2   |DIF/VIF 3 |Data 3   |DIF/VIF 4 |Data 4   |
+======+=======+==========+=========+===============+=========+==========+=========+==========+=========+
|9831  |78     |04 04     |D7000000 |04 84 3C       |00000000 |04 2B     |03000000 |04 AB 3C  |00000000 |
+------+-------+----------+---------+---------------+---------+----------+---------+----------+---------+

Extraction is slightly more complex, requiring either a longer parsing pattern or perhaps a regex.

In this example, 215 10^1 Wh (2.15 kWh) have been consumed, and the current power draw is 3 10^0 W (0.003 kW).

"""

from binascii import hexlify, unhexlify
from struct import *
from Crypto.Cipher import AES
from Crypto.Util import Counter
from datetime import datetime
import json
import re
from typing import List, Tuple

# And our own implementation
from meter.MeterMeasurement import MeterMeasurement, Measurement
from utils.timezone import ZuluTime
from utils.crc16_wmbus import crc16_wmbus, crc16_check, CrcCheckException

# Set timezone
zulu_time = ZuluTime()


class C1Telegram:
    """
    Implements capture of data fields for a C1 telegram from OmniPower
    """

    # Define slices for C1 telegram
    # These byte positions are multiplied by *2 to get hex digit count
    header_slice = slice(0, 17*2)       # Byte 0-16 (inclusive)
    ell_sn_slice = slice(13*2, 17*2)    # Bytes 13-16 (inclusive)
    payload_start_byte = 17
    im871a_crc_bytes = 2

    def __init__(self, telegram: bytes) -> None:
        """
        Take a telegram (bytestring with hex values) and parses into fields
        """
        try:
            # Pull out non-encrypted header. Will discard this variable after parsing it
            header = telegram[self.header_slice]

            # Encrypted part of telegram, keep after parsing
            self.encrypted = telegram[self.payload_start_byte * 2 : len(telegram) - self.im871a_crc_bytes * 2]

            # The payload message is set as an empty bytestring until decrypted
            self.decrypted = bytes()

            # The CRC16 from the IM871-A dongle, always at the end
            self.im871_crc = telegram[len(telegram) - self.im871a_crc_bytes * 2 : ]

            # Unpack header values into a tuple
            header_values = unpack('<BBHIBBBBBI', unhexlify(header))

            # Extract fields by field numbers, see first table in documentation
            self.L = header_values[0]
            self.C = header_values[1]
            self.M = header_values[2]
            self.A = header_values[3]
            self.version = header_values[4]
            self.medium = header_values[5]
            self.CI = header_values[6]
            self.CC = header_values[7]
            self.ACC = header_values[8]
            self.AES_CTR = header_values[9]

            # The ELL-SN (AES_CTR) field is a composite 4-byte session number (SN) field.
            # Including encryption method, minute counter and session number
            ell_sn = self.parse_ell_sn(telegram[self.ell_sn_slice])
            self.SN = {
                "ENC": ell_sn[0],
                "Time": ell_sn[1],
                "Session": ell_sn[2],
            }

            # Store original hex values as big-endian inside strings
            # for comparison with human-readable values
            self.big_endian = {
                'L': hexlify(pack('>B', self.L)),
                'C': hexlify(pack('>B', self.C)),
                'M': hexlify(pack('>H', self.M)),
                'A': hexlify(pack('>I', self.A)),
                'version': hexlify(pack('>B', self.version)),
                'medium': hexlify(pack('>B', self.medium)),
                'CI': hexlify(pack('>B', self.CI)).upper(),
                'CC': hexlify(pack('>B', self.CC)).upper(),
                'ACC': hexlify(pack('>B', self.ACC)),
                'AES_CTR': hexlify(pack('>I', self.AES_CTR)),
            }

            # Compute decryption prefix
            # See recipe in documentation, currently FN=0
            self.prefix = pack('<HIBBBIB', self.M, self.A, self.version, self.medium, self.CC, self.AES_CTR, 0)

        except Exception as e:
            # TODO: Specify error type caught and handle
            # Raise exception for upstream handling. and propagate the existing exception
            raise TelegramParseException("Failed to parse.") from e

    @staticmethod
    def parse_ell_sn(sn_field: bytes) -> Tuple[int, ...]:

        # Get 32 bit from little-endian format
        ell_sn = unpack('<I', unhexlify(sn_field))[0]

        # Get bits using masks
        enc = (ell_sn & (0xe << 28)) >> 29       # Get bits 31-29
        time = (ell_sn & (0x1ffffff << 4)) >> 4  # Get bits 28-04
        session = ell_sn & 0xf                   # Get bits 03-00

        return enc, time, session

    def decrypt_using(self, meter: 'OmniPower') -> bool:
        """
        Decrypts a telegram and inserts it into telegram (self)
        Uses a meter object and its key to perform decryption.
        Requires instantiated OmniPower meter with valid AES-key.
        """

        try:
            # Store decrypted value in field decrypted
            self.decrypted = meter.decrypt(self)
            return True
        except AesKeyException as e:
            # Missing key or malformed
            print(e)
            return False
        except CrcCheckException as e:
            # Bad message received, CRC check fail
            print(e)
            return False
        except:
            # TODO: Blanket broad exception - bad idea, test and fix!
            return False


class OmniPower:
    """
    Implementation of our OmniPower single-phase meter
    Passed values are hex encoded as string, e.g. '2C2D' for value 0x2C2D.
    """

    # Required AES key digits (128 bit -> 16 bytes -> 32 hex digits)
    # Anything else must be a malformed key
    aes_req_key_digits = 2*16

    # Byte limit for short, data-only telegrams from OmniPower.
    # Larger telegrams also contain DIF/VIF information
    short_telegram_lim = 39

    # TPL-CI field value for different C1 frame formats
    tpl_ci_field = slice(4, 6)
    tpl_ci_compact = b'79'      # This kind is data-only
    tpl_ci_drh = b'78'          # This kind has DIF/VIF information too

    # Short telegram format is contiguous frame of 4 32-bit uints
    # The data begins at byte 7 of the payload
    short_telegram_fmt = '<IIII'
    short_telegram_data_slice = slice(7*2, None)

    # Long telegram format contains DIF/VIF/VIF followed by values.
    # The DIF 04 specifies a 32-bit uint, so the little-endian format '<I' is used.
    long_telegram_fmt = (('0404', '<I'),
                         ('04843C', '<I'),
                         ('042B', '<I'),
                         ('04AB3C', '<I'))

    def __init__(self,
                 name: str = 'Kamstrup OmniPower one-phase',
                 meter_id: str = '32666857',
                 manufacturer_id: str = '2C2D',
                 medium: str = '02',
                 version: str = '30',
                 aes_key: str = '9A25139E3244CC2E391A8EF6B915B697'):

        self.name = name                        # Meter nickname
        self.meter_id = meter_id                # serial number of the meter
        self.manufacturer_id = manufacturer_id  # Kamstrup manufacturer ID
        self.medium = medium                    # Medium/type of meter, e.g 0x02 is electricity
        self.version = version                  # Firmware version for the wm-bus interface
        self.AES_key = aes_key                  # 128-bit AES encryption key
        self.measurement_log = []               # type: List['MeterMeasurement']

    def is_this_my(self, telegram: 'C1Telegram') -> bool:
        """
        Check whether a given telegram is from this meter by comparing meter setting to telegram
        """

        # Comparison is done on lowercase strings and big-endian values, e.g. 2c2d == 2c2d
        if (telegram.big_endian['A'] == self.meter_id.lower().encode()) and \
                (telegram.big_endian['M'] == self.manufacturer_id.lower().encode()) and \
                (telegram.big_endian['version'] == self.version.lower().encode()) and \
                (telegram.big_endian['medium'] == self.medium.lower().encode()):
            return True
        else:
            return False

    def decrypt(self, telegram: 'C1Telegram') -> bytes:
        """
        Decrypt a telegram. Returns decrypted bytes.
        Raises CrcCheckException if CRCs do not match after decryption.

        Requires:

         - the prefix from the telegram (telegram.prefix), and
         - the encryption key stored in the meter object.

        Decrypts the data stored in field telegram.encrypted

        """

        # Check that 16 byte (128 bit) key has 32 hex digits
        if len(self.AES_key) != self.aes_req_key_digits:
            raise AesKeyException("Bad key length, {}".format(len(self.AES_key)))

        # Get relevant variables
        key_in = self.AES_key               # UTF-8 formatted
        ciphertext = telegram.encrypted     # ASCII string
        prefix = telegram.prefix            # bytestring

        # Make binary representations
        key = unhexlify(key_in)             # type: bytes
        ciphertext = unhexlify(ciphertext)

        # Create cryptographic objects to decrypt using AES-CTR method
        counter = Counter.new(nbits=16, prefix=prefix, initial_value=0x0000)
        cipher = AES.new(key, AES.MODE_CTR, counter=counter)

        # Perform decryption
        decryption = hexlify(cipher.decrypt(ciphertext))

        # Will raise exception if CRC check failed, to be caught upstream
        crc16_check(decryption)

        return decryption

    @classmethod
    def unpack_short_telegram_data(cls, data: bytes) -> Tuple[int, ...]:
        """
        Short C1 telegrams only contain field data values, no information about DIF/VIF
        """
        # Extract the measurements into a 4-tuple
        return unpack(cls.short_telegram_fmt, unhexlify(data[cls.short_telegram_data_slice]))

    @classmethod
    def unpack_long_telegram_data(cls, data: bytes) -> Tuple[int, ...]:
        """
        Long C1 telegrams contain DIF/VIF information and field data values
        """
        # Make return value vector with exactly as many zeros as there are expected fields.
        # So if one field is not found, a zero is returned in its place
        return_val = [0] * len(cls.long_telegram_fmt)

        for i, fmt in enumerate(cls.long_telegram_fmt):

            # Build Regex, which searches for the code and groups the 8 subsequent characters
            pattern = fmt[0].lower() + "(.{8})"

            # Search for the pattern in the data, which we first format to an UTF-8 string with decode
            match = re.search(pattern, data.decode())

            if match:
                # Unpack the found specific 8 characters (4 bytes = 32 bits)
                # match.group(1) contains these 8 characters
                # unpack returns a 1-tuple, from which we grab the single integer element with [0]
                # print("Found DIF/VIF/VIFE field {} in data records (long) telegram".format(fmt[0]))
                return_val[i] = unpack(fmt[1], unhexlify(match.group(1).encode()))[0]

        # Finally, return a tuple that we can use to convert and log measurements
        return tuple(return_val)

    def extract_measurement_frame(self, telegram: 'C1Telegram') -> MeterMeasurement:
        """
        Requires that the telegram is already decrypted, otherwise returns empty measurement frame.
        """

        # Create a measurement frame with static data from this meter and current time
        omnipower_meas = MeterMeasurement(self.meter_id, datetime.now(tz=zulu_time))

        if not telegram.decrypted:
            # TODO: Do better error handling here, instead of just dumping empty objects
            return omnipower_meas

        # Look at TPL-CI field and determine long (frame with DRH) / short (Compact frame) type
        #print("TPL-CI: {}".format(telegram.decrypted[4:6]))
        #if telegram.L <= OmniPower.short_telegram_lim:

        tpl_ci = telegram.decrypted[self.tpl_ci_field]
        if tpl_ci == self.tpl_ci_compact:
            measurement_data = OmniPower.unpack_short_telegram_data(telegram.decrypted)
        elif tpl_ci == self.tpl_ci_drh:
            measurement_data = OmniPower.unpack_long_telegram_data(telegram.decrypted)
        else:
            # TODO: Better error handling... What to do if neither 0x78 nor 0x79?
            return omnipower_meas

        # Convert and store in measurement objects with units
        m1 = Measurement(measurement_data[0] * 10 / 1000, "kWh")  # A+ measurement
        m2 = Measurement(measurement_data[1] * 10 / 1000, "kWh")  # A- measurement
        m3 = Measurement(measurement_data[2] / 1000, "kW")  # P+ measurement
        m4 = Measurement(measurement_data[3] / 1000, "kW")  # P- measurement

        # Add the measurements in the measurement frame
        omnipower_meas.add_measurement("A+", m1)
        omnipower_meas.add_measurement("A-", m2)
        omnipower_meas.add_measurement("P+", m3)
        omnipower_meas.add_measurement("P-", m4)

        return omnipower_meas

    def add_measurement_to_log(self, measurement: MeterMeasurement) -> bool:
        """
        Pushes a new measurement to the tail end of the log
        """
        try:
            self.measurement_log.append(measurement)
            return True
        except:
            # TODO: Specify potential exceptions / errors
            return False

    def process_telegram(self, telegram: 'C1Telegram') -> bool:
        """
        Does entire processing chain for a telegram, including adding to log.
        Returns True if processing is OK and added to log OK.
        Otherwise False.
        """
        # Confirm that the telegram belongs to this meter, then
        # try to decrypt the telegram
        if self.is_this_my(telegram) and telegram.decrypt_using(self):

            # extract measurements
            measurement_frame = self.extract_measurement_frame(telegram)

            # Confirm not empty
            if not measurement_frame.is_empty():

                # then add measurement frame to log and return True if okay
                return self.add_measurement_to_log(measurement_frame)

            else:
                # Is empty. No data was added, so nothing to be logged
                return False
        else:
            # This is not my telegram or telegram failed to decrypt
            return False

    def dump_log_to_json(self) -> str:
        """
        Returns a JSON string of all measurement frames in log, with an incremented number for each observation.
        """
        dump = {}

        # Fill object
        [dump.update({str(i): log_i.as_dict()}) for i, log_i in enumerate(self.measurement_log)]

        # Return JSON-string
        return json.dumps(dump)


class AesKeyException(Exception):
    """
    Use this to raise an exception when an AES key is missing or wrong length.
    """
    def __init__(self, exception_message: str):
        self.exception_message = exception_message

        # Invoke constructor for base class
        super().__init__(self.exception_message)

    def __str__(self):
        # String representation of exception if printed
        return "AES key missing from meter object or malformed: {}.".format(self.exception_message)


class TelegramParseException(Exception):
    """
    Use this to raise an exception if a bytestream telegram fails to parse into C1 format.
    """
    def __init__(self, exception_message: str):
        self.exception_message = exception_message

        # Invoke constructor for base class
        super().__init__(self.exception_message)

    def __str__(self):
        # String representation of exception if printed
        return "Byte object could not be parsed as a C1 telegram: {}.".format(self.exception_message)
