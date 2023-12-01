#!/usr/bin/env python
import os

from dotenv import load_dotenv
import time
import datetime
import requests
from datetime import date
from openpyxl import load_workbook
from Adafruit_IO import Client, Feed, Dashboard, RequestError

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus
from bme280 import BME280

load_dotenv()


def hpa_to_inches(pressure_in_hpa):
    pressure_in_inches_of_m = pressure_in_hpa * 0.02953
    return pressure_in_inches_of_m


def degc_to_degf(temperature_in_c):
    temperature_in_f = (temperature_in_c * (9 / 5.0)) + 32
    return temperature_in_f


def send_to_weather_underground(temperature, pressure, humidity):
    # create a string to hold the first part of the URL
    WU_URL = os.getenv("WU_URL")
    WU_STATION_ID = os.getenv("WU_STATION_ID")
    WU_STATION_PWD = os.getenv("WU_STATION_PWD")

    temp_str = "{0:.2f}".format(degc_to_degf(temperature))
    humidity_str = "{0:.2f}".format(humidity)
    pressure_str = "{0:.2f}".format(hpa_to_inches(pressure))
    payload = {
        'action': 'updateraw',
        'dateutc': 'now',
        'ID': WU_STATION_ID,
        'PASSWORD': WU_STATION_PWD,
        'realtime': 1,
        'rtfreq': 2.5,
        'tempf': temp_str,
        'humidity': humidity_str,
        'baromin': pressure_str
    }

    try:
        r = requests.get(WU_URL, params=payload)
    except Exception:
        print("Error sending weather update to wunderground.")

    if (r.status_code != 200):
        print("Error sending to Weather Underground: Received " + str(r.status_code) + " " + str(r.text))


ADAFRUIT_IO_KEY = os.getenv("ADAFRUIT_IO_KEY")
ADAFRUIT_IO_USERNAME = os.getenv("ADAFRUIT_IO_USERNAME")
aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

ADAFRUIT_IO_FEED_NAME = os.getenv("ADAFRUIT_IO_FEED_NAME")
# Create new feeds
# print(ADAFRUIT_IO_FEED_NAME + """
# ========================
# """)

try:
    aio.create_feed(Feed(name="Temperature"))
    aio.create_feed(Feed(name="Humidity"))
    aio.create_feed(Feed(name="Pressure"))
    print("Adafruit feeds created")
except RequestError:
    # print("Feeds already exist")
    pass

temperature_feed = aio.feeds('temperature')
humidity_feed = aio.feeds('humidity')
pressure_feed = aio.feeds('pressure')

# Create new dashboard
try:
    dashboard = aio.create_dashboard(Dashboard(name="Home Weather Station"))
    print("Adafruit dashboard created")
except RequestError:
    # print("Dashboard already exists")
    pass

dashboard = aio.dashboards('home-weather-station')

# print("https://io.adafruit.com/{0}/dashboards/{1}".format(ADAFRUIT_IO_USERNAME, dashboard.key))

# Initialise the BME280
bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)

# Reject the first value, it's often junk
temperature = bme280.get_temperature()
pressure = bme280.get_pressure()
humidity = bme280.get_humidity()
time.sleep(1)

now = datetime.datetime.now()

try:
    temperature = round(bme280.get_temperature(), 1)
    pressure = round(bme280.get_pressure(), 1)
    humidity = round(bme280.get_humidity(), 1)

    print('[' + now.strftime('%d/%m/%y %H:%M') + '] ' + '{:05.1f}*C {:05.1f}hPa {:05.1f}%'.format(temperature, pressure,
                                                                                                  humidity))
except Exception as e:
    print(e)

# Send to adafruit.io
try:
    aio.send_data(temperature_feed.key, temperature)
    aio.send_data(pressure_feed.key, pressure)
    aio.send_data(humidity_feed.key, humidity)
    # print('Data sent to adafruit.io')
except Exception as e:
    print(e)

# Send to Weather Underground
try:
    send_to_weather_underground(temperature, pressure, humidity)
except Exception as e:
    print(e)

# Add to Spreadsheet
try:
    # Load the workbook and select the sheet
    wb = load_workbook('/home/pi/Python_Code/Weather_Station/weather.xlsx')
    sheet = wb['Sheet1']

    # Append data to the spreadsheet
    row = (now.strftime('%d/%m/%y'), now.strftime('%H:%M'), temperature, pressure, humidity)
    sheet.append(row)

    # Save the workbook
    wb.save('/home/pi/Python_Code/Weather_Station/weather.xlsx')
except Exception as e:
    print(e)

finally:
    wb.save('/home/pi/Python_Code/Weather_Station/weather.xlsx')
    # print("Goodbye!")


