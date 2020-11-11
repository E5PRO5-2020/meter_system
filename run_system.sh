
# Start driver as daemon
PYTHONPATH=$PYTHONPATH:pwd python driver/Start_Driver.py

# Start main event loop in this terminal
PYTHONPATH=$PYTHONPATH:pwd python run/run_system.py
