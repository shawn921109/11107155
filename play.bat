cd %~dp0/PWS

if not exist "__pyenv__\python.xxx" (
	powershell -c Set-ExecutionPolicy unrestricted -Scope CurrentUser
	powershell -c ../bin/inst_py.ps1
)

__pyenv__\python.exe daemon.py config.json
