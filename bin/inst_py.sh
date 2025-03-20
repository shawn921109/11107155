#!/bin/sh

if ! test -f __pyenv__/bin/activate; then
	echo "Install python virtual environment"
	python3 -m venv __pyenv__
	if test -f "./requirements.txt"; then
		. __pyenv__/bin/activate
		python3 -m pip install -r ./requirements.txt
		deactivate
	fi
fi
