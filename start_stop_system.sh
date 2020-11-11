# Script to start/stop Omnipower/WMBUS reading system 


# Test for input argument
if [ $# != 1 ]
then 
	echo "Only accept one arguement"
else
	if [ $1 == "start" ]
	then
		echo "Starting system"
		# Start driver as daemon
		PYTHONPATH=$PYTHONPATH:pwd python driver/Start_Driver.py
		# Start main event loop in this terminal
		PYTHONPATH=$PYTHONPATH:pwd python run/run_system.py
	elif [ $1 == "stop" ]
	then
		echo "Stopping system"
		# Get Driver PID
		# (Maybe) Make signal handler in daemon
		pids=$(pgrep -f driver/Start_Driver.py)
		kill $pids
		echo "Stopped daemon with pid: $pids"
		# Make MQTT or other implementation to stop run_system.py
		#Example: (Not implemented in run_system.py)
		#mosquitto_pub -h localhost -p 1883 -t StopTheVerner -m "#Backtowritemorecode' " -u <username> -P <password>	
	else
		echo "Wrong input argument"
	fi
fi
	
