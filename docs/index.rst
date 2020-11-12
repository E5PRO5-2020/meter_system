.. Kamstrup OmniPower wm-bus metering documentation master file, created by
   sphinx-quickstart on Wed Oct 14 10:19:52 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Kamstrup OmniPower wm-bus metering
==================================

This documentation covers the system to read the
Kamstrup OmniPower 1-phase meter over wm-bus.
The implementation uses an iM871-A transceiver to read wm-bus messages.
Processed measurements are sent upstream using MQTT.

.. toctree::
   :caption: Table of contents
   :maxdepth: 2

   run_system

   DriverClass
   omnipower
   metermeasurement
   mqtt

   util_crc16wmbus
   util_crc16im871a
   util_timezone
   log
   Search_for_dongle
   
   test


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
