
# Run the tests
#python -m pytest -rs test/

# Check if FIFO is created, if not; create fifo
FILE=./IM871A_pipe
if test -f "$FILE"; then
  echo "$FILE exists."
else 
  mkfifo IM871A_pipe
fi

# "-s FILE" = true if file exists and has a size greater than zero
# Ensure recipient for pipe, and save pipe output into file
if [ -s $FILE ]
then 
	echo "Something found in file, emptying it!"
	'dd if=$FILE' 
	pytest -rs -k test_read_data_RPi
else
	echo "Nothing found in file, carrying on!"
	cat IM871A_pipe > test/pipe_data.txt &
	pytest -rs -k test_read_data_RPi
fi

# Check the coverage, -rs shows skipped tests
coverage run -m pytest -rs -k 'not test_read_data_RPi'
sleep 1s
coverage report -m --omit="${PYENV_VIRTUAL_ENV}*"

# Do type checking
echo "MyPy results for /meter/"
mypy meter
echo "MyPy result for /test/"
mypy test
echo "MyPy result for /driver/"
mypy driver

# Remove the pipe used for testing
rm ./$FILE

