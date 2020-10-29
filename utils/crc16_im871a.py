"""
Implementation of CRC16 for IM871-A (CCITT)
*******************************************

:synopsis: CRC16 CCITT implementation based on Steffen's C implementation.
:authors: Steffen and Janus.
:date: 29 Oct 2020.

- See IMST's WMBUS_HCL_Spec_V1.6.pdf.
- CRC computation starts from the Control Field and ends with the last octet of the Payload Field.
- IM871A uses CRC16-CCITT Polynomial G(x) = 1 + x^5 + x^12 + x^16.

"""

from binascii import hexlify
from struct import pack


def crc16_im871a(m: bytes) -> bytes:
    """
    Compute CRC16 (CCITT) for a message received serially from IM871-A.
    Full message example: a5 8203 27442d2c5768663230028d20cd12340720519df247ff65e751662a300bc4e5c67da86477f0182637 c1ab.

    Argument m must:

    - NOT contain the first field, e.g. 0xA5.
    - Start and contain the control field, e.g. 0x8203.
    - Contain full payload, e.g. 0x2744...2637
    - NOT contain the trailing 2 bytes of expected CRC16 value, e.g. 0xC1AB.

    """

    hex_radix = 16
    g = 0x8408                                      # Generator polynomial, g(x)
    crc = 0xFFFF                                    # Init value for CCITT CRC16

    for byte in range(0, len(m), 2):                # Loop over all bytes in message
        b = int(m[byte:byte + 2], hex_radix)        # Make byte value from hex digits

        for bit in range(0, 8):                     # Repeat for 8 bits in a byte
            if (b & 1) ^ (crc & 1):                 # Is there a remainder for division by the poly for this bit?
                crc = (crc >> 1) ^ g                # Get remainder from division
            else:
                crc >>= 1                           # Just advance to next bit in division
            b >>= 1                                 # Move on to next bit in this byte of the message

    crc = crc ^ 0xFFFF                              # Perform final complement
    return hexlify(pack('<H', crc))                 # Return as little-endian


if __name__ == '__main__':

    # Captured messages from IM871-A
    # First element is expected CRC16, second element is the message excluding the CRC16 (removed from end)
    # There are 8 compact messages and 1 longer message with DRH
    test_vectors = [(b'3885', b'820327442d2c5768663230028d20cb103407201d82040f26a7e808ff3449f9e9d2e4b28bd7e7c6f1c6df'),
                    (b'c1ab', b'820327442d2c5768663230028d20cd12340720519df247ff65e751662a300bc4e5c67da86477f0182637'),
                    (b'b7ac', b'820327442d2c5768663230028d206972dd032089aa2c0a75352edf4b64a7b908470ba6171c89e52aab8a'),
                    (b'e2af', b'820327442d2c5768663230028d2086f0dd0320368763cbae145d5f6c56d0afad5f369db1e22a7e6311df'),
                    (b'229e', b'820327442d2c5768663230028d2076b0dd0320c872a70560f4faef03685bcac1ac8fca34cb3ef0dbacf1'),
                    (b'02f3', b'820327442d2c5768663230028d2079b3dd032072e1bc19a9d337d17a731fcea7733abcaa002ca6e33478'),
                    (b'a0ee', b'820327442d2c5768663230028d207ed0dd032008a6f44c44320b0e636f694819e91b2a5f2fb1dc753191'),
                    (b'b64f', b'820327442d2c5768663230028d2083e1dd0320d4e65337143ba7621f5ebf580642d40fb7d66c45dd4e19'),
                    (b'f667', b'82032d442d2c5768663230028d207cc2dd0320f8325c5952304521c530f237b6ee19e4cd7d6778f660152192a4751a46')
                    ]

    for test_vector in test_vectors:
        expected_crc = test_vector[0]
        message = test_vector[1]
        assert crc16_im871a(message) == expected_crc

    print("All ok.")
