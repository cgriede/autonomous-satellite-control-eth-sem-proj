@echo off
cd /d C:\Users\cedri\work\code\sem-proj-asc
call conda activate ASC
python backend\scripts\earth_image\calibrate_earth_background.py > data\earth_image\_calibrate.log 2>&1
python backend\scripts\earth_image\preview_earth_background.py >> data\earth_image\_calibrate.log 2>&1
echo done>> data\earth_image\_calibrate.log
