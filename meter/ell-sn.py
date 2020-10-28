"""
This file and function is a a development demo only, will be removed before release.
Janus, Oct 2020
"""
from struct import unpack
from binascii import unhexlify
from typing import Tuple


def parse_ell_sn(sn_field: bytes) -> Tuple[int, ...]:

    # Get 32 bit from little-endian format
    ell_sn = unpack('<I', unhexlify(sn_field))[0]

    # Get bits using masks
    enc = (ell_sn & (0xe << 28)) >> 29          # Get bits 31-29
    time = (ell_sn & (0x1ffffff << 4)) >> 4     # Get bits 28-04
    session = ell_sn & 0xf                      # Get bits 03-00

    return enc, time, session


if __name__ == '__main__':
    print(parse_ell_sn(b'01870320'))
