"""
Parse Kamstrup OmniPower wm-bus telegrams
*****************************************

:platform: Python 3.5.10 on Linux, OS X
:synopsis: Implements parsing functionality for C1 telegrams and log handling for data series
:author: Janus Bo Andersen
:date: 14 October 2020

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
| 9 | 13-16 | 4     | AES CTR     | AES counter                                 | Varies, used for decryption     |
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
- The encrypted wireless m-bus on OmniPower uses AES-128 Mode CTR.
- See EN 13757-4:2019, p. 54, as ELL (Ext. Link-Layer) with ECN = 001 => AES-CTR.
- A decryption prefix (initial counter block) is built from some of the fields.
- See table 54 on p. 55 of EN 13757-4:2019.


It can be packed using the format `<HIBBBIB`.

+-----+---------+---+---+---+---------+-----+----+
|M    |A        |Ver|Med|CC |AES CTR  |FN   |BC  |
+=====+=========+===+===+===+=========+=====+====+
|2D2C |57686632 |30 |02 |20 |21870320 |0000 |00  |
+-----+---------+---+---+---+---------+-----+----+

Prefix: M, ..., AES CTR.
Counter: FN, BC
FN: frame number (frame # sent by meter within same session number, in case of multi-frame transmissions).
BC: Block counter (encryption block number, counts up for each 16 byte block decrypted within the telegram).

Decrypted payload examples
==========================

The interpretation of the fields in the OmniPower are

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


Decrypted short telegram
________________________

+------+-------+----------------+-----------+---------+---------+---------+---------+
|CRC16 |TPL-CI |Data fmt. sign. |CRC16 data |Data 1   |Data 2   |Data 3   |Data 4   |
+======+=======+================+===========+=========+=========+=========+=========+
|1170  |79     |138C            |4491       |CE000000 |00000000 |03000000 |00000000 |
+------+-------+----------------+-----------+---------+---------+---------+---------+

Measurement data starts at byte 7, and can easily be extracted using `<IIII` little-endian format.

In this example, 206 10^1 Wh (2.06 kWh) have been consumed, and the current power draw is 3 10^0 W (0.003 kW).


Decrypted long telegram
_______________________

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
from OmniPower.MeterMeasurement import MeterMeasurement, Measurement


class C1Telegram:
    """
    Implements capture of data fields for a C1 telegram from OmniPower
    """

    def __init__(self, telegram: bytes) -> None:
        """
        Take a telegram (bytestring with hex values) and parses into fields
        """
        try:
            header = telegram[0:17 * 2]                             # Non-encrypted part, discard after parsing
            self.encrypted = telegram[17 * 2:len(telegram) - 4]     # Encrypted part of telegram, keep after parsing
            self.decrypted = bytes()                                # Empty string until decrypted
            self.CRC16 = telegram[len(telegram) - 4:]

            header_values = unpack('<BBHIBBBBBI', unhexlify(header))

            # Extract fields by field numbers
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

            # Store original hex values as big-endian inside strings for comparison with human-readable values
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
            self.prefix = pack('<HIBBBIB', self.M, self.A, self.version, self.medium, self.CC, self.AES_CTR, 0)

        except:
            print("Oops!")

    def decrypt_using(self, meter: 'OmniPower') -> bool:
        """
        Decrypts a telegram using the key from the specified meter.
        Updates the decrypted field of self.
        Requires instantiated OmniPower meter with valid AES-key.
        """

        if not meter.AES_key:
            return False

        try:
            self.decrypted = meter.decrypt(self)
            return True
        except:
            print("Oh no!")
            return False


class OmniPower:
    """
    Implementation of our OmniPower single-phase meter
    Passed values are hex encoded as string, e.g. '2C2D' for value 0x2C2D.
    """

    # Byte limit for short, data-only telegrams from OmniPower.
    # Larger telegrams also contain DIF/VIF information
    short_telegram_lim = 39

    # Short telegram format is contiguous frame of 4 32-bit uints
    short_telegram_fmt = '<IIII'

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
        Decrypt a telegram. Requires:
         - the prefix from the telegram (telegram.prefix), and
         - the encryption key from the meter.

        Decrypts the data stored telegram.encrypted
        """

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
        return hexlify(cipher.decrypt(ciphertext))

    @classmethod
    def unpack_short_telegram_data(cls, data: bytes) -> Tuple[int, ...]:
        """
        Short C1 telegrams only contain field data values, no information about DIF/VIF
        """
        # Extract the measurements into a 4-tuple
        return unpack(cls.short_telegram_fmt, unhexlify(data[7 * 2:]))

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
                print("Found DIF/VIF/VIFE field {} in data records (long) telegram".format(fmt[0]))
                return_val[i] = unpack(fmt[1], unhexlify(match.group(1).encode()))[0]

        # Finally, return a tuple that we can use to convert and log measurements
        return tuple(return_val)

    def extract_measurement_frame(self, telegram: 'C1Telegram') -> MeterMeasurement:
        """
        Requires that the telegram is already decrypted, otherwise returns empty measurement
        """

        # Create a measurement frame with static data from this meter and current time
        omnipower_meas = MeterMeasurement(self.meter_id, datetime.now())

        if not telegram.decrypted:
            return omnipower_meas

        if telegram.L <= OmniPower.short_telegram_lim:
            measurement_data = OmniPower.unpack_short_telegram_data(telegram.decrypted)
        else:
            measurement_data = OmniPower.unpack_long_telegram_data(telegram.decrypted)

        # Store in measurement objects with units
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

    def add_measurement_to_log(self, measurement: MeterMeasurement) -> None:
        """
        Pushes a new measurement to the tail end of the log
        """
        self.measurement_log.append(measurement)

    def process_telegram(self, telegram: 'C1Telegram') -> bool:
        """
        Does entire processing chain for a telegram, including adding to log
        """
        # Confirm that the telegram belongs to this meter
        if self.is_this_my(telegram):

            # decrypt the telegram, then extract measurements and store these in own log
            telegram.decrypt_using(self)
            self.add_measurement_to_log(self.extract_measurement_frame(telegram))
            return True
        else:
            return False

    def dump_log_to_json(self) -> str:
        """
        Returns a JSON object of all measurement frames in log, with an incremented number for each observation
        """
        dump = {}

        # Fill object
        [dump.update({str(i): log_i.as_dict()}) for i, log_i in enumerate(self.measurement_log)]

        # Return JSON-string
        return json.dumps(dump)
