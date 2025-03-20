#!/bin/sh
ROOT=$(realpath $0) && ROOT=${ROOT%/bin/*}
DOCS=${ROOT}/docs
PID=${ROOT}/PWS.pid

python3="__pyenv__/bin/python3"
test -f "__pyenv__/python.exe" && python3="__pyenv__/python.exe"

while test "$1"; do
case "$1" in
start)
	if test -f "${ROOT}/config.json"; then
		cd ${ROOT}
		${python3} ${ROOT}/daemon.py ${ROOT}/config.json &
		for s in 1 2 3 4 5 6 7 8 9 10; do
			if test -f "${PID}"; then
				echo "Daemon running at " $(cat ${PID})
				break
			fi
			sleep 1
		done
	else
		echo "Configuration file ${ROOT}/config.json not exist"
	fi ;;
stop)
	if test -f "${PID}"; then
		echo -n "[..] Kill PID (${PID})"
		kill $(cat ${PID}) && rm ${PID}
		echo "\r[OK] Kill PID (${PID})"
	else
		echo "[OK] Not running"
	fi
	;;
status)
	if test -f "${PID}"; then
		echo "Daemon running on PID $(cat ${PID})"
	else
		echo "Daemon not running"
	fi
	;;
esac
shift
done

test "${VIRTUAL_ENV}" && deactivate
