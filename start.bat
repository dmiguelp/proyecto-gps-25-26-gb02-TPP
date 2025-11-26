@echo off
cd .venv
cd Scripts
call activate.bat
cd ..
cd ..
python -m swagger_server
exit