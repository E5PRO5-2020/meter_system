"""
CRC16 for wm-bus
****************

:synopsis: CRC16 calculator for EN 13757
:author: Janus Bo Andersen
:date: October 2020

Overview:
---------

- This function performs the CRC16 algorithm.
- The result can be used to confirm data integrity of received payload in a wm-bus message.
- Wm-bus follows the CRC16 standard outlined in EN 13757.

A `CrcCheckException` class is also implemented, which is used to raise exceptions
if a CRC check fails.

The IM871-A transceiver removes the outer CRC16 (last two bytes of a message)
and replaces it with its own, which follows another standard, CRC16-CCITT.
So the outer CRC16 can not be checked with the function in this module.

CRC16 EN 13757:
---------------

- CRC16 uses a generator polynomial, g(x), described in EN 13757-4.
- See p. 42 for data-link layer CRC, and an example with a C1 telegram on p. 84.
- See p. 58 for transport layer CRC polynomial.

g(x) = x^16 + x^13 + x^12 + x^11 + x^10 + x^8 + x^6 + x^5 + x^2 + 1

In binary (excluding x^16 as it is shifted out anyway), this g(x) is represented as

+-------------+-----------------+-----------+
| Byte 1      | Byte 2          | Hex value |
+=============+=================+===========+
|0011 1101    |0110 0101        | 0x3D65    |
+-------------+-----------------+-----------+
|MSbit = x^15 | LSbit = x^0 = 1 |           |
+-------------+-----------------+-----------+

See EN 13757-4, table 43, p. 50 for expected structure of ELL for a CI=0x8D telegram.
PayloadCRC is included in the encrypted part of telegram.

Algorithm rules:
----------------

- Treats data most-significant bit first
- Final CRC shall be complemented
- Multi-byte data is transmitted LSB first
- CRC is transmitted MSB first

Math background:
----------------

- CRC uses a finite field F=[0, 1], so we do subtraction using XOR.
- CRC is the final remainder from repeated long division of message by polynomial,\
when no further division is possible.
- The output CRC is complemented by XOR with 0xFFFF.

Algorithm implementation comments:
----------------------------------
The implemented algorithm uses Python's ability for 'infinite' width of integers.
That is slightly inefficient, and can't be ported to C code on an embedded device.
But it is significantly easier to debug and understand than byte-wise algorithms or lookup tables.

"""

from binascii import hexlify
from struct import pack


def crc16_wmbus(message: bytes) -> bytes:
    """
    Takes a bytes object with a message (ascii encoded hex values).
    Returns the CRC16 value for the message encoded in a bytes object.

    Example: f(b'79138C4491CE000000000000000300000000000000') -> b'1170'.

    """

    crc_bits = 16
    hex_radix = 16

    g = 0x3d65                                  # Generator polynomial, g(x)
    m = int(message, hex_radix) << crc_bits     # Message, m(x), shifted to make space for 16-bit CRC
    crc = m                                     # Start with m(x)<<16 (initial crc=remainder is 0x0000)

    m_bitlen = len(bin(m)[2:])                  # Hacky method to get number of bits req. to represent m(x)
    g_bitlen = crc_bits                         # Poly is 16 bits

    # Loop over each bit, from highest to lowest
    # Continue while remainder is larger than polynomial (i.e. still divisions to perform)
    for n in range(m_bitlen - 1, g_bitlen - 1, -1):
        # Step 1 Check if most significant bit is 1
        if crc & (1 << n):
            # If yes, perform division and subtract to get remainder (XOR)
            g_shift = g << (n - g_bitlen)     # Shift polynomial
            crc = (crc ^ g_shift) % 2**n      # mod 2^n is to emulate << 1 (but Py doesn't shift out to the left)
        else:
            # If not, move on to next
            pass

        # Repeat

    # Perform final complement
    crc = crc ^ 0xFFFF

    # Return as little-endian 16-bit to match how CRC16's are stored in telegrams
    crc_hex = hexlify(pack('<H', crc))

    return crc_hex


def crc16_check(payload: bytes) -> bool:
    """
    Takes a payload and splits into CRC16-field and message.
    Computes CRC16 on the message and compares to CRC16-field.
    Return True if match.
    Raises CrcCheckException if no match.
    """

    crc16_recv = payload[0:4]
    crc16_calc = crc16_wmbus(payload[4:])

    # Perform comparison on lowercase, just in case something is UPPER'ed
    # Raise an exception if CRC check fails
    if crc16_recv.lower() == crc16_calc.lower():
        return True
    else:
        raise CrcCheckException(crc16_recv, crc16_calc, "CRC check fail. No match.")


class CrcCheckException(Exception):
    """
    Use this to raise an exception when a CRC16 check
    has failed.
    """
    def __init__(self, crc_recv: bytes, crc_calc: bytes, exception_message: str):
        self.crc_recv = crc_recv
        self.crc_calc = crc_calc
        self.exception_message = exception_message

        # Invoke constructor for base class
        super().__init__(self.exception_message)

    def __str__(self):
        # String representation of exception if printed
        return "CRC received ({}) does not match CRC calculated ({}).".format(self.crc_recv.decode(), self.crc_calc.decode())


if __name__ == '__main__':

    # Self-test if run as main from command line

    # Example from p. 84
    expected_crc = b'c57a'   # Reverse order of example
    data = b'1444AE0C7856341201078C2027780B13436587'
    assert crc16_wmbus(data) == expected_crc

    # From actual telegram, payload CRC
    expected_crc = b'bb52'
    data = b'79138C7976CE000000000000000400000000000000'
    assert crc16_wmbus(data) == expected_crc

    # Another example from captured real OmniPower telegram
    expected_crc = b'1170'
    data = b'79138C4491CE000000000000000300000000000000'
    assert crc16_wmbus(data) == expected_crc

    # Telegram with data record headers
    expected_crc = b'0fe6'
    data = b'780404CE00000004843C00000000042B0300000004AB3C00000000'
    assert crc16_wmbus(data) == expected_crc
