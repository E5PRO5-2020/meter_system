# Meter System :rocket:

This repo contains the integrated metering system for Kamstrup OmniPower, including IM871-A driver, parser, objects and unit tests.

Documentation is live here: [meter-system @ readthedocs.io](https://meter-system.readthedocs.io/en/latest/)

## Install environment and libraries
- Use Python 3.5.10 (best via PyEnv) and setup a virtual environment: `pyenv virtualenv 3.5.10 3.5.10-dev`
- Ensure virtual enviroment active
- Install libraries from requirements.txt: `pip install -r requirements.txt`

## Run tests
Run the start script `./starttest.sh`

## Build documentation
Compile with Sphinx using the makefile in the docs/ folder (`make html` or `make latexpdf`)
