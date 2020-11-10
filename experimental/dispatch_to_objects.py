"""
Demo of dynamic construction of new OmniPower objects and access directly through dispatch-table object.

Recall, an OmniPower is instantiated with (some of) these arguments
name = 'Kamstrup OmniPower one-phase',
meter_id = '32666857',
manufacturer_id = '2C2D',
medium = '02',
version = '30',
aes_key = '9A25139E3244CC2E391A8EF6B915B697'

"""

from meter.OmniPower import OmniPower, C1Telegram


# Factory to create instantiated OmniPower objects
def create(meter_type, *args, **kwargs):
    # Do some checks here... Or use dispatch_table.py method, or something
    if meter_type == "omnipower":
        obj = OmniPower(*args, **kwargs)
        return obj


# Assume we want to make 3 OmniPowers with these IDs
ids = ["77777777", "88888888", "32666857"]

# Begin with empty dispatcher, and build from there
dispatch = {}
for id in ids:
    dispatch.update({id: create("omnipower", name="OP-"+id, meter_id=id)})

# Call something dynamically
telegram = C1Telegram(b'27442d2c5768663230028d206360dd0320c42b87f46fc048d42498b44b5e34f083e93e6af16176313d9c')
address = telegram.big_endian['A'].decode()     # Gets address as UTF-8 string

dispatch[address].process_telegram(telegram)    # Calls OmniPower's process function
print(dispatch[address].measurement_log[-1])    # Show what we got
