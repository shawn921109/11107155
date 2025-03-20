$ROOT = Split-Path (Get-Variable MyInvocation).value.MyCommand.Path

cd ${ROOT}/..
if (-Not (Test-Path "__pyenv__/python.exe" -PathType Leaf)) {
	.\install.ps1
}
__pyenv__\python.exe daemon.py config.json
