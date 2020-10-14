""" Parse Kamstrup OmniPower wm-bus telegrams

:platform: Python 3.5.10 on Linux, OS X
:synopsis: Implements parsing functionality for C1 telegrams and log handling for data series
:author: Janus Bo Andersen <janus@janusboandersen.dk>

- This module implements parsing for the Kamstrup OmniPower meter, single-phase.
- This meter sends wm-bus C1 (compact one-way) telegrams.
- Telegrams on wm-bus are little-endian, i.e. LSB first.

In a regular measurement data telegram, the data fields are:

+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
| # | Byte# | Bytes | M-bus field | Description                                 | Expected value (little-endian)  |
+===+=======+=======+=============+=============================================+=================================+
| 0 | 0     | 1     | L           | Telegram length                             | 0x27 (39 bytes follow)          |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
| 1 | 1     | 1     | C           | Control field (type and purpose of message) | 0x44 (SND_NR)                   |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
| 2 | 2-3   | 2     | M           | Manufacturer ID (official ID code)          | 0x2D2C (KAM)                    |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
| 3 | 4-7   | 4     | A           | Address (meter serial number)               | 0x57686632 (big endian 32666857)|
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
| 9 | 13-16 | 4     | AES_CTR     | AES counter                                 | Varies, used for decryption     |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
|10 | 17-39 | 23    | Data        | Contains AES-encrypted data frame           | Encrypted data                  |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+
|11 | 40-41 | 2     | CRC16       | CRC16 check                                 |                                 |
+---+-------+-------+-------------+---------------------------------------------+---------------------------------+

The first 9 fields of the telegram can be unpacked using the little-endian format `<BBHIBBBBB`, where

- `<` marks little-endian,
- `B` is an unsigned 1 byte (char),
- `H` is an unsigned 2 byte (short),
- `I` is an unsigned 4 byte (int)

Telegram examples

+---+---+-----+---------+---+---+---+---+---+---------+-----------------------------------------------+-----+
|L  |C  |M    |A        |Ver|Med|CI |CC |ACC|AES_CTR  |Encrypted payload                              |CRC16|
+===+===+=====+=========+===+===+===+===+===+=========+===============================================+=====+
|27 |44 |2D2C |57686632 |30 |02 |8D |20 |2E |21870320 |D3A4F149B1B8F5783DF7434B8A66A55786499ABE7BAB59 |xxxx |
+---+---+-----+---------+---+---+---+---+---+---------+-----------------------------------------------+-----+
|27 |44 |2d2c |57686632 |30 |02 |8d |20 |63 |60dd0320 |c42b87f46fc048d42498b44b5e34f083e93e6af1617631 |3d9c |
+---+---+-----+---------+---+---+---+---+---+---------+-----------------------------------------------+-----+
|27 |44 |2d2c |57686632 |30 |02 |8d |20 |8e |11de0320 |188851bdc4b72dd3c2954a341be369e9089b4eb3858169 |494e |
+---+---+-----+---------+---+---+---+---+---+---------+-----------------------------------------------+-----+

The AES-CTR decryption prefix is built from some of the fields (m-bus mode 5). It's packed using the format `<HIBBBIB`.

+-----+---------+---+---+---+---------+---+
|M    |A        |Ver|Med|CC |AES_CTR  |Pad|
+=====+=========+===+===+===+=========+===+
|2D2C |57686632 |30 |02 |20 |21870320 |00 |
+-----+---------+---+---+---+---------+---+

A decrypted payload example

+------+-------+----------------+-----------+---------+---------+---------+---------+
|CRC16 |CI-TPL |Data fmt. sign. |CRC16 data |Field 1  |Field 2  |Field 3  |Field 4  |
+======+=======+================+===========+=========+=========+=========+=========+
|1170  |79     |138C            |4491       |CE000000 |00000000 |03000000 |00000000 |
+------+-------+----------------+-----------+---------+---------+---------+---------+

Measurement fields start at byte 7, and can be extracted using `<IIII` little-endian format.

The fields in the OmniPower are

+----------+---------------+----------------+--------------------+--------------------------------------+-----------+
| Field    | Kamstrup name | Data fmt (DIF) | Value type (VIF/E) | VIF/E meaning                        | DIF VIF/E |
+==========+===============+================+====================+======================================+===========+
| Field 1  | A+            | 32-bit uint    | Energy, 10^1 Wh    | Consumption from grid, accum.        | 04  04    |
+----------+---------------+----------------+--------------------+--------------------------------------+-----------+
| Field 2  | A-            | 32-bit uint    | Energy, 10^1 Wh    | Production to grid, accum.           | 04  84 3C |
+----------+---------------+----------------+--------------------+--------------------------------------+-----------+
| Field 3  | P+            | 32-bit uint    | Power,  10^0 W     | Consumption from grid, instantan.    | 04  2B    |
+----------+---------------+----------------+--------------------+--------------------------------------+-----------+
| Field 4  | P+            | 32-bit uint    | Power,  10^0 W     | Production to grid, instantan.       | 04  AB 3C |
+----------+---------------+----------------+--------------------+--------------------------------------+-----------+

"""

from binascii import hexlify, unhexlify
from struct import *
from Crypto.Cipher import AES
from Crypto.Util import Counter
from datetime import datetime
import json
# And our own implementation
from OmniPower.MeterMeasurement import MeterMeasurement, Measurement


class C1Telegram:
    """
    Implements capture of data fields for a C1 telegram from OmniPower
    """

    def __init__(self, tlg):
        """
        Take a telegram (string with hex values) and parses into fields
        :param tlg: C1 type telegram
        """
        try:
            header = tlg[0:17 * 2]                      # Non-encrypted part of telegram, discard after parsing
            self.encrypted = tlg[17 * 2:len(tlg)-4]     # Encrypted part of telegram, keep after parsing
            self.decrypted = ''                         # Empty string until decrypted
            self.CRC16 = tlg[len(tlg)-4:]

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
            self.be = {
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

    def decrypt_using(self, meter: object) -> None:
        """
        Decrypts a telegram using the key from the specified meter.
        Updates the decrypted field of self.
        :param meter: Instantiated OmniPower meter with valid AES-key
        :return: void
        """
        try:
            self.decrypted = meter.decrypt(self)
        except:
            print("Oh no!")


class OmniPower:
    """
    Implementation of our OmniPower single-phase meter
    Passed values are hex encoded as string, e.g. '2C2D' for value 0x2C2D.
    """

    def __init__(self,
                 name='Kamstrup OmniPower one-phase',
                 meter_id='32666857',
                 manufacturer_id='2C2D',
                 medium='02',
                 version='30',
                 aes_key='9A25139E3244CC2E391A8EF6B915B697'):

        self.name = name                        # Meter nickname
        self.meter_id = meter_id                # serial number of the meter
        self.manufacturer_id = manufacturer_id  # Kamstrup manufacturer ID
        self.medium = medium                    # Medium/type of meter, e.g 0x02 is electricity
        self.version = version                  # Firmware version for the wm-bus interface
        self.AES_key = aes_key                  # 128-bit AES encryption key
        self.measurement_log = []               # Start with an empty log

    def is_this_my(self, t: type(C1Telegram)) -> None:
        """
        Check whether a given telegram is from this meter by comparing meter setting to telegram
         - Meter ID == A
         - Manufacturer ID == M
         - Version == Version
         - Medium == Medium

        Comparison is done on lowercase strings and big-endian values, e.g. 2c2d == 2c2d
        :param t: C1Telegram type telegram
        :return:
        """

        if (t.be['A'] == self.meter_id.lower().encode()) and \
                (t.be['M'] == self.manufacturer_id.lower().encode()) and \
                (t.be['version'] == self.version.lower().encode()) and \
                (t.be['medium'] == self.medium.lower().encode()):
            return True
        else:
            return False

    def decrypt(self, t: type(C1Telegram)) -> str:
        """
        Decrypt a telegram, requires the prefix from the telegram (t.prefix) and the encryption key from the meter.
        Decrypts the data inside t.encrypted
        :param t: C1 type telegram
        :return:
        """

        # Get relevant variables
        key = self.AES_key          # UTF-8 formatted
        ciphertext = t.encrypted    # ASCII string
        prefix = t.prefix           # bytestring

        # Make binary representations
        key = unhexlify(key)
        ciphertext = unhexlify(ciphertext)

        # Create cryptographic objects to decrypt using AES-CTR method
        counter = Counter.new(nbits=16, prefix=prefix, initial_value=0x0000)
        cipher = AES.new(key, AES.MODE_CTR, counter=counter)

        # Perform decryption
        return hexlify(cipher.decrypt(ciphertext))

    def extract_measurement_frame(self, t):
        """
        Requires an already decrypted telegram
        :return:
        """

        # Extract the measurements into a 4-tuple
        measurement_data = unpack('<IIII', unhexlify(t.decrypted[7 * 2:]))

        # Store in measurement objects with units
        m1 = Measurement(measurement_data[0] * 10 / 1000, "kWh")  # A+ measurement
        m2 = Measurement(measurement_data[1] * 10 / 1000, "kWh")  # A- measurement
        m3 = Measurement(measurement_data[2] / 1000, "kW")  # P+ measurement
        m4 = Measurement(measurement_data[3] / 1000, "kW")  # P- measurement

        # Create a measurement frame with static data from this meter and current time
        omnipower_meas = MeterMeasurement(self.meter_id, datetime.now())

        # Add the measurements in the measurement frame
        omnipower_meas.add_measurement("A+", m1)
        omnipower_meas.add_measurement("A-", m2)
        omnipower_meas.add_measurement("P+", m3)
        omnipower_meas.add_measurement("P-", m4)

        return omnipower_meas

    def add_measurement_to_log(self, measurement):
        """
        Pushes a new measurement to the tail end of the log
        :param measurement: A MeterMeasurement frame
        :return: void
        """
        self.measurement_log.append(measurement)

    def process_telegram(self, t):
        """
        Does entire processing chain for a telegram, including adding to log
        :param t:
        :return: True if success, otherwise False
        """

        # Confirm that the telegram belongs to this meter
        if self.is_this_my(t):

            # decrypt the telegram, then extract measurements and store these in own log
            t.decrypt_using(self)
            self.add_measurement_to_log(self.extract_measurement_frame(t))
            return True
        else:
            return False

    def dump_log_to_json(self):
        """
        Returns a JSON object of all measurement frames in log, with an incremented number for each observation
        :return: JSON-encoded string (UTF-8)
        """
        dump = {}

        # Fill object
        [dump.update({str(i): log_i.as_dict()}) for i, log_i in enumerate(self.measurement_log)]

        # Return JSON-string
        return json.dumps(dump)
