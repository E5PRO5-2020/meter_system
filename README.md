# Meter System :rocket:

This repo contains the integrated metering system for Kamstrup OmniPower, including IM871-A driver, parser, objects and unit tests.

Documentation is live here: [meter-system @ readthedocs.io](https://meter-system.readthedocs.io/en/latest/)

## Install environment and libraries
Use Python 3.5.10 (best via PyEnv), setup a virtual environment and install libraries from requirements.txt (`pip install -r requirements.txt`)

## Build documentation
Compile with Sphinx using the makefile in the docs/ folder (`make html` or `make latexpdf`)

## Run tests
coverage run -m pytest
