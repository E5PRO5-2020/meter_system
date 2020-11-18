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

# Check the coverage, -rs shows skipped tests
coverage run -m pytest -rs

# Remove the pipe used for testing
rm ./$FILE
