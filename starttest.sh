# Run the tests
#python -m pytest -rs test/

# Check if FIFO is created, if not; create fifo
FILE=./IM871A_pipe
if test -f "$FILE"; then
  echo "$FILE exists."
else 
  mkfifo IM871A_pipe
fi

# Ensure recipient for pipe, and save pipe output into file
cat IM871A_pipe > test/pipe_data.txt &

# Setup pipe reader

# Check the coverage, -rs shows skipped tests
coverage run -m pytest -rs
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
