# Pi Zero weather station

Get weather data from a pimoroni BME280 sensor and upload Weather Underground, Adafruit.IO and an Excel Spreadsheet

## Installation
###  Install BME280 python library
`git clone https://github.com/pimoroni/bme280-python.git`

Then follow installation instructions in README.md

### Add CRON job
`crontab -e`

Add the following line to the end of the file to run weather updates every 5 minutes:

`4-59/5 * * * * python3 /home/pi/Python_Code/Weather_Station/weather-station.py`