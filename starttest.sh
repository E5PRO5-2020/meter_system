# Run the tests
#python -m pytest -rs test/

# Setup pipe reader

# Check the coverage, -rs shows skipped tests
coverage run -m pytest -rs
sleep 0.2s
coverage report -m --omit="${PYENV_VIRTUAL_ENV}*"

# Do type checking
echo "MyPy results for /meter/"
mypy meter
echo "MyPy result for /test/"
mypy test

#Uncomment to test driver folder
#echo "MyPy result for /driver/"
#mypy driver
