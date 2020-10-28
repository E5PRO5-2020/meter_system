# Run the tests
python -m pytest test/

# Check the coverage
coverage run -m pytest
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
