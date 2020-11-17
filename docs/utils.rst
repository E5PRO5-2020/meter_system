.. moduleauthor:: Janus Bo Andersen

Utilities and support functions
===============================

CRC16 for wm-bus
****************
.. automodule:: utils.crc16_wmbus

CRC16 functions
--------------------
.. currentmodule:: utils.crc16_wmbus
.. autofunction:: crc16_wmbus
.. autofunction:: crc16_check

CRC check exception
--------------------
.. currentmodule:: utils.crc16_wmbus
.. autoclass:: CrcCheckException
   :members:


CRC16 for IM871-A
*****************
.. automodule:: utils.crc16_im871a

CRC16 function
--------------------
.. currentmodule:: utils.crc16_im871a
.. autofunction:: crc16_im871a_check
.. autofunction:: crc16_im871a_calc


Timezone handling
*****************
.. automodule:: utils.timezone

ZuluTime class
--------------
.. currentmodule:: utils.timezone
.. autoclass:: ZuluTime
   :members:

Print datetime object with ISO 8601 format
------------------------------------------
.. currentmodule:: utils.timezone
.. autofunction:: zulu_time_str


Logging to syslog
*****************
.. automodule:: utils.log
   :members:


Automatic search for IM871-A dongle device
******************************************
.. automodule:: utils.Search_for_dongle
   :members:
