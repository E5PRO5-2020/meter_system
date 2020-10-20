coverage run -m pytest
sleep 0.2s
coverage report --omit="${PYENV_VIRTUAL_ENV}*"

