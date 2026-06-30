@echo off
cd /d "%~dp0"
uv run --with pyserial --with python-osc heatpett_server.py
pause
