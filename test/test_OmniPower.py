import pytest
from meter.MeterMeasurement import Measurement, MeterMeasurement
from meter.OmniPower import C1Telegram, OmniPower

# Includes from other files
from datetime import datetime
import json


def test_OmniTest():
    omnipower = OmniPower()
    telegram = '27442d2c5768663230028d208e11de0320188851bdc4b72dd3c2954a341be369e9089b4eb3858169494e'.encode()
    tlg = C1Telegram(telegram)
    assert omnipower.is_this_my(tlg) == True

    # Long telegrams
    long_telegram = b'2d442d2c5768663230028d206461dd032038931d14b405536e0250592f8b908138d58602eca676ff79e0caf0b14d0e7d'
    telegram = C1Telegram(long_telegram)
    payload = omnipower.decrypt(telegram)[6:]
    assert payload == b'0404d700000004843c00000000042b0300000004ab3c00000000'
    result = omnipower.unpack_long_telegram_data(payload)
    assert result == (215, 0, 3, 0)

    # Short telegram
    short_telegram = b'27442D2C5768663230028D202E21870320D3A4F149B1B8F5783DF7434B8A66A55786499ABE7BAB59ffff'
    telegram = C1Telegram(short_telegram)
    process_telegram_test = omnipower.process_telegram(telegram)
    assert process_telegram_test == True

    # Missing line 241
    # if not meter.AES_key:
    #	return False

    # Missing line 247-253
    # Exception handling ( Do we want to test this? )

    # Testing is_this_my()-method
    tg1 = '27442d2c5768663230028d206360dd0320c42b87f46fc048d42498b44b5e34f083e93e6af16176313d9c'
    tg2 = '27442d2c5768663230028d206562dd03200ac3aea1e613dd9af1a75c68cdedd5fdd2617c1e71a9d0b3b1'
# Currently not working - Investigating
# omnipower.is_this_my(tg1) == True

# Missing Line 304 - Exception handling of decrypt()

# Missing line 391 - extract_measurement_frame() - if not telegram.decrypted: return false

# Missing line 396 - unpack_long_telegram(telegram.decrypted)
# tg1_decrypted = omnipower.process_telegram(tg1)
# omnipower.extract_measurement_frame(tg1_decrypted)
