[中文](https://github.com/DoctorReid/StarRailAutoProxy/tree/main/.github/README.md) | English

# Honkai Star Rail - Auto Proxy
Image recognition-based automated game script

## User Guide
This script only supports resolutions in the ```16:9``` aspect ratio. It should theoretically work on resolutions of ```1920x1080``` and higher, as well as on low graphics settings. If the game resolution is lower than the display resolution, please use windowed mode. The script has a lower chance of errors with better graphics quality.

Currently, only English version is on beta test. During the script's execution, ensure that the game window is fully visible on the screen. In some systems, running the script may require ```administrator``` privileges. 

For more details, please refer to the __[wiki](https://github.com/DoctorReid/StarRailAutoProxy/wiki/Home_en)__, or method with conda&powershell see [install](#install).

To download the script, visit the [Release page](https://github.com/DoctorReid/StarRailAutoProxy/releases). If you like this project, consider giving me a ```Star``` ~

If you have any questions, you can raise an issue or join the QQ group ```743525216``` for inquiries.~~__(Although I may have slow response times during work hours and when coding after work)__~~

## source code related

### install

#### conda&powershell

```powershell
git clone git@github.com:DoctorReid/StarRailOneDragon.git
cd StarRailOneDragon
conda create --prefix="./.env" python=3.11
conda activate ./.env
pip install -r requirements.txt
# dministrator permissions required
conda activate ./.env    #if ./.env not activate
$env:PYTHONPATH="src"
python src/gui/app.py
```

## English localization
This script may not work properly in English mode because of insufficient test. 

Needs help for localization and test, contact with me if you want to contribute. 

Thanks in advance!

# Disclaimer
    ""This software is open source, free of charge and for learning and exchange purposes only." 
    "The developer team has the final right to interpret this project. 
    "All problems arising from the use of this software are not related to this project and the developer team.
    "If you encounter a merchant using this software to practice on your behalf and charging for it, it may be the cost of equipment and time, etc. 
    "The problems and consequences arising from this software have nothing to do with it.""
