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


def crc16_im871a(m: bytes) -> bool:
    """
    Compute CRC16 (CCITT) for a message received serially from IM871-A.
    Full message example: a5 8203 27442d2c5768663230028d20cd12340720519df247ff65e751662a300bc4e5c67da86477f0182637 c1ab.

    V1.0 Argument m must:

    - NOT contain the first field, e.g. 0xA5.
    - Start and contain the control field, e.g. 0x8203.
    - Contain full payload, e.g. 0x2744...2637
    - NOT contain the trailing 2 bytes of expected CRC16 value, e.g. 0xC1AB.

    V1.1 Update:

    - Argument must be the intire message from IM871-A
    - Function returns TRUE when the check sum matches the expected CRC16 value  

    """
    Checksum = m[-4:]                               # Store the expected CRC16 value
    data = m[2:-4]                                  # Removes SOF field and CRC16 value

    hex_radix = 16
    g = 0x8408                                      # Generator polynomial, g(x)
    crc = 0xFFFF                                    # Init value for CCITT CRC16

    for byte in range(0, len(data), 2):             # Loop over all bytes in message
        b = int(data[byte:byte + 2], hex_radix)     # Make byte value from hex digits

        for _ in range(0, 8):                       # Repeat for 8 bits in a byte
            if (b & 1) ^ (crc & 1):                 # Is there a remainder for division by the poly for this bit?
                crc = (crc >> 1) ^ g                # Get remainder from division
            else:
                crc >>= 1                           # Just advance to next bit in division
            b >>= 1                                 # Move on to next bit in this byte of the message

    crc = crc ^ 0xFFFF                              # Perform final complement
    crc16 = hexlify(pack('<H', crc))                # CRC16 as little-endian
    
    if Checksum == crc16:                           # Check if sum matches expected CRC16 value
        return True                        
    else:
        return False


def test_crc16():

    # Captured messages from IM871-A
    test_full_frames =[(b'a5820321442d2c952742761b168d206d82c40222942c7a5414f7be5ea4411ebab435fe4995ff91'),
                    (b'a5820327442d2c5768663230028d201a13e00920dddf142f84b1107cae4e84dbcb98210fc275ddc868ce8d2554'),
                    (b'a5820321442d2c952742761b168d206e83c40222c72670296e74f24339982b162de91fa1af1400'),
                    (b'a5820321442d2c622842761b168d20d550c00222055d80a5b9011be3fafdf8a7d65cd64c95ffd1'),
                    (b'a5820327442d2c5768663230028d201b20e00920b34c894aa121ef88baa3f6e4e8b1b4cebe009978e5d7c6b153'),
                    (b'a5820321442d2c952742761b168d206f90c402228d949f169fdc2fde9782cff6a0fb175aba02f0'),
                    (b'a5820324442d2c622842761b168d20d651c00222420d6c7a7e8d04496a16e01a306e1d90c99bf2b41ef3'),
                    (b'a582032d442d2c5768663230028d201c21e00920d1c1b4c7ae4e8ea21285041754ef54367a7a00d2af4d23384dc51872b5970c'),
                    (b'a5820321442d2c952742761b168d207091c4022276925e4ab3801499711e3b6da8477f7e5bbca0'),
                    (b'a5820321442d2c622842761b168d20d752c0022275f0e5b100964f3edbef976e959ca83fa00465'),
                    (b'a5820327442d2c5768663230028d201d22e00920ab4b8e693509c3c3e562d34c5d0734d5e1414c23a8d1ec8fa9')]

    for test_vector in test_full_frames:
        assert crc16_im871a(test_vector) == True
        

