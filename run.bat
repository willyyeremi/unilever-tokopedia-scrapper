@echo off

docker-compose up -d
Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope Process
python -m virtualenv ./pipeline/pentaho/.venv
pipeline/pentaho/.venv/Scripts/activate
python -m pip -r ./pipeline/pentaho/requirements.txt
python kjb_maker.py
deactive