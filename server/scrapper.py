from flask import Flask, request, Response
from flask_cors import CORS
from consts import *
from bot import TelegramBot
from bs4 import BeautifulSoup
from openai import OpenAI
import requests
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from functools import lru_cache
import logging
from typing import Dict, List, Optional
from ratelimit import limits, sleep_and_retry
from threading import Thread
from flask_socketio import SocketIO
import googlemaps

logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# try:
#     gmaps = googlemaps.Client(key=GOOGLE_TOKEN)
# except Exception as error:
#     logger.error(f"failed to initialize google maps, err = {error}")
#     raise

PremiumUser = True

@app.route('/', methods=["GET", "POST"])
def hewwo():
    return str(TelegramBot == None)

@app.route('/google_token', methods=["GET", "POST"])
def get_google_token():
    return GOOGLE_TOKEN

@app.route('/openai_token', methods=["GET", "POST"])
def get_openai_token():
    return OPENAI_TOKEN


@app.route('/test_scrapper', methods=["GET", "POST"])
def get_test_scrapper():
    return [PlaceInfo(Id='ChIJtwgHgJMZ2jERCExG-EjFa6M', Name='Equate Coffee', Address='1 Tanjong Pagar Plz, #02-25, Singapore 082001', Lat=1.2748632, Long=103.8426344, Status='OPERATIONAL', Rating=4.6, RatingCount=209, PriceLevel=None, OpeningHours={'openNow': False, 'periods': [{'open': {'day': 1, 'hour': 8, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 17, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 2, 'hour': 8, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 17, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 3, 'hour': 8, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 17, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 4, 'hour': 8, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 17, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 5, 'hour': 8, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 5, 'hour': 17, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 6, 'hour': 8, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 6, 'hour': 15, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}}], 'weekdayDescriptions': ['Monday: 8:30\u202fAM\u2009–\u20095:30\u202fPM', 'Tuesday: 8:30\u202fAM\u2009–\u20095:30\u202fPM', 'Wednesday: 8:30\u202fAM\u2009–\u20095:30\u202fPM', 'Thursday: 8:30\u202fAM\u2009–\u20095:30\u202fPM', 'Friday: 8:30\u202fAM\u2009–\u20095:30\u202fPM', 'Saturday: 8:30\u202fAM\u2009–\u20093:00\u202fPM', 'Sunday: Closed'], 'nextOpenTime': '2025-03-27T00:30:00Z'}, Website='https://www.equate.sg/', GoogleLink='https://maps.google.com/?cid=11775722567883967496', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da1993800708b7:0xa36bc548f8464c08!3e0"), PlaceInfo(Id='ChIJ4wutVe4Z2jERDUp3XtrAkeE', Name='Fieldnotes, Neil Road', Address='41 Neil Rd, Singapore 088824', Lat=1.2797561, Long=103.8428418, Status='OPERATIONAL', Rating=4.7, RatingCount=605, PriceLevel=None, OpeningHours={'openNow': False, 'periods': [{'open': {'day': 0, 'hour': 11, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 0, 'hour': 20, 'minute': 45, 'date': {'year': 2025, 'month': 3, 'day': 30}}}, {'open': {'day': 1, 'hour': 11, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 20, 'minute': 45, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 2, 'hour': 11, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 20, 'minute': 45, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 3, 'hour': 11, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 20, 'minute': 45, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 4, 'hour': 11, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 20, 'minute': 45, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 5, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 5, 'hour': 22, 'minute': 45, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 6, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 6, 'hour': 22, 'minute': 45, 'date': {'year': 2025, 'month': 3, 'day': 29}}}], 'weekdayDescriptions': ['Monday: 11:30\u202fAM\u2009–\u20098:45\u202fPM', 'Tuesday: 11:30\u202fAM\u2009–\u20098:45\u202fPM', 'Wednesday: 11:30\u202fAM\u2009–\u20098:45\u202fPM', 'Thursday: 11:30\u202fAM\u2009–\u20098:45\u202fPM', 'Friday: 11:00\u202fAM\u2009–\u200910:45\u202fPM', 'Saturday: 11:00\u202fAM\u2009–\u200910:45\u202fPM', 'Sunday: 11:30\u202fAM\u2009–\u20098:45\u202fPM'], 'nextOpenTime': '2025-03-27T03:30:00Z'}, Website='http://www.fieldnotes.com.sg/', GoogleLink='https://maps.google.com/?cid=16253984574277110285', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da19ee55ad0be3:0xe191c0da5e774a0d!3e0"), PlaceInfo(Id='ChIJEZX2E0gZ2jER1zo5m4LC3fM', Name="Papi's Tacos - Tanjong Pagar", Address='33 Tg Pagar Rd, #01-01, Singapore 088456', Lat=1.279188, Long=103.844008, Status='OPERATIONAL', Rating=4.3, RatingCount=460, PriceLevel=None, OpeningHours={'openNow': False, 'periods': [{'open': {'day': 0, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 0, 'hour': 14, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 30}}}, {'open': {'day': 0, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 0, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}}, {'open': {'day': 1, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 14, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 1, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 2, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 14, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 2, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 3, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 14, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 3, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 4, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 14, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 4, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 5, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 5, 'hour': 14, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 5, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 6, 'hour': 0, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}}, {'open': {'day': 6, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 6, 'hour': 14, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 29}}}, {'open': {'day': 6, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 0, 'hour': 0, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}}], 'weekdayDescriptions': ['Monday: 12:00\u2009–\u20092:30\u202fPM, 5:00\u2009–\u200911:00\u202fPM', 'Tuesday: 12:00\u2009–\u20092:30\u202fPM, 5:00\u2009–\u200911:00\u202fPM', 'Wednesday: 12:00\u2009–\u20092:30\u202fPM, 5:00\u2009–\u200911:00\u202fPM', 'Thursday: 12:00\u2009–\u20092:30\u202fPM, 5:00\u2009–\u200911:00\u202fPM', 'Friday: 12:00\u2009–\u20092:30\u202fPM, 5:00\u202fPM\u2009–\u200912:00\u202fAM', 'Saturday: 11:00\u202fAM\u2009–\u20092:30\u202fPM, 5:00\u202fPM\u2009–\u200912:00\u202fAM', 'Sunday: 11:00\u202fAM\u2009–\u20092:30\u202fPM, 5:00\u2009–\u200911:00\u202fPM'], 'nextOpenTime': '2025-03-27T04:00:00Z'}, Website='http://www.papis-tacos.com/', GoogleLink='https://maps.google.com/?cid=17572415187275299543', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da194813f69511:0xf3ddc2829b393ad7!3e0"), PlaceInfo(Id='ChIJKeC0vJIZ2jERAsl1O-3x-00', Name='Glasshouse', Address='136 Neil Rd, #01-01, Singapore 088865', Lat=1.2783727999999999, Long=103.8408894, Status='OPERATIONAL', Rating=4.3, RatingCount=298, PriceLevel='PRICE_LEVEL_MODERATE', OpeningHours={'openNow': False, 'periods': [{'open': {'day': 0, 'hour': 8, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 0, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}}, {'open': {'day': 1, 'hour': 8, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 2, 'hour': 8, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 3, 'hour': 8, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 4, 'hour': 8, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 5, 'hour': 8, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 5, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 6, 'hour': 8, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 6, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}}], 'weekdayDescriptions': ['Monday: 8:00\u202fAM\u2009–\u20096:00\u202fPM', 'Tuesday: 8:00\u202fAM\u2009–\u20096:00\u202fPM', 'Wednesday: 8:00\u202fAM\u2009–\u20096:00\u202fPM', 'Thursday: 8:00\u202fAM\u2009–\u20096:00\u202fPM', 'Friday: 8:00\u202fAM\u2009–\u20096:00\u202fPM', 'Saturday: 8:00\u202fAM\u2009–\u20096:00\u202fPM', 'Sunday: 8:00\u202fAM\u2009–\u20096:00\u202fPM'], 'nextOpenTime': '2025-03-27T00:00:00Z'}, Website='http://theglasshousesg.com/', GoogleLink='https://maps.google.com/?cid=5619350961281943810', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da1992bcb4e029:0x4dfbf1ed3b75c902!3e0"), PlaceInfo(Id='ChIJM323rE0Z2jERWMg9G23kIBg', Name='CAFE KREAMS', Address='32 Maxwell Rd, #01-07 Maxwell Chambers, Singapore 069115', Lat=1.2775235, Long=103.84631999999999, Status='OPERATIONAL', Rating=4.4, RatingCount=1115, PriceLevel=None, OpeningHours={'openNow': False, 'periods': [{'open': {'day': 0, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 0, 'hour': 22, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}}, {'open': {'day': 1, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 22, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 2, 'hour': 9, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 3, 'hour': 9, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 4, 'hour': 9, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 5, 'hour': 9, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 5, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 6, 'hour': 9, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 6, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}}], 'weekdayDescriptions': ['Monday: 11:00\u202fAM\u2009–\u200910:00\u202fPM', 'Tuesday: 9:00\u202fAM\u2009–\u200911:00\u202fPM', 'Wednesday: 9:00\u202fAM\u2009–\u200911:00\u202fPM', 'Thursday: 9:00\u202fAM\u2009–\u200911:00\u202fPM', 'Friday: 9:00\u202fAM\u2009–\u200911:00\u202fPM', 'Saturday: 9:00\u202fAM\u2009–\u200911:00\u202fPM', 'Sunday: 11:00\u202fAM\u2009–\u200910:00\u202fPM'], 'specialDays': [{'date': {'year': 2025, 'month': 3, 'day': 31}}], 'nextOpenTime': '2025-03-27T01:00:00Z'}, Website='http://www.kreams.sg/', GoogleLink='https://maps.google.com/?cid=1738640613424613464', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da194dacb77d33:0x1820e46d1b3dc858!3e0"), PlaceInfo(Id='ChIJnS0ilrwZ2jERg66Abhmv33Y', Name='DOPA', Address='7 Tanjong Pagar Plz, #01-107, Singapore 081007', Lat=1.2773010999999999, Long=103.8428332, Status='OPERATIONAL', Rating=4.1, RatingCount=263, PriceLevel=None, OpeningHours={'openNow': False, 'periods': [{'open': {'day': 0, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 0, 'hour': 22, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}}, {'open': {'day': 1, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 22, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 2, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 22, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 3, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 22, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 4, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 22, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 5, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 5, 'hour': 22, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 6, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 6, 'hour': 22, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 29}}}], 'weekdayDescriptions': ['Monday: 12:00\u2009–\u200910:00\u202fPM', 'Tuesday: 12:00\u2009–\u200910:00\u202fPM', 'Wednesday: 12:00\u2009–\u200910:00\u202fPM', 'Thursday: 12:00\u2009–\u200910:00\u202fPM', 'Friday: 12:00\u2009–\u200910:30\u202fPM', 'Saturday: 12:00\u2009–\u200910:30\u202fPM', 'Sunday: 12:00\u2009–\u200910:00\u202fPM'], 'nextOpenTime': '2025-03-27T04:00:00Z'}, Website='http://www.dopadopacreamery.com/', GoogleLink='https://maps.google.com/?cid=8565757540044942979', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da19bc96222d9d:0x76dfaf196e80ae83!3e0"), PlaceInfo(Id='ChIJ7xlFdKwT2jERXrseJIzS6tI', Name='Citrus By The Pool', Address='3 Woodlands Street 13, Woodlands Swimming Complex, Singapore 738600', Lat=1.4344838, Long=103.77948479999999, Status='OPERATIONAL', Rating=4.9, RatingCount=21379, PriceLevel='PRICE_LEVEL_MODERATE', OpeningHours={'openNow': True, 'periods': [{'open': {'day': 0, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 1, 'hour': 5, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 1, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 2, 'hour': 5, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 2, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 3, 'hour': 5, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 3, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 23, 'minute': 59, 'truncated': True, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 4, 'hour': 0, 'minute': 0, 'truncated': True, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 5, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 4, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 5, 'hour': 5, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 5, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 6, 'hour': 5, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}}, {'open': {'day': 6, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 0, 'hour': 5, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}}], 'weekdayDescriptions': ['Monday: 11:00\u202fAM\u2009–\u20095:00\u202fAM', 'Tuesday: 11:00\u202fAM\u2009–\u20095:00\u202fAM', 'Wednesday: 11:00\u202fAM\u2009–\u20095:00\u202fAM', 'Thursday: 11:00\u202fAM\u2009–\u20095:00\u202fAM', 'Friday: 11:00\u202fAM\u2009–\u20095:00\u202fAM', 'Saturday: 11:00\u202fAM\u2009–\u20095:00\u202fAM', 'Sunday: 11:00\u202fAM\u2009–\u20095:00\u202fAM'], 'nextCloseTime': '2025-03-26T21:00:00Z'}, Website='http://www.citrusbythepool.com/', GoogleLink='https://maps.google.com/?cid=15198191391858408286', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da13ac744519ef:0xd2ead28c241ebb5e!3e0"), PlaceInfo(Id='ChIJs5IIbEdy2TERpBAR81eyBfY', Name='Bintan Indah Mall', Address='WCJR+JHG, Tanjungpinang Kota, Tanjung Pinang Kota, Tanjung Pinang City, Riau Islands, Indonesia', Lat=0.9315743, Long=104.4414432, Status='OPERATIONAL', Rating=4, RatingCount=455, PriceLevel=None, OpeningHours={'openNow': False, 'periods': [{'open': {'day': 0, 'hour': 7, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 0, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}}, {'open': {'day': 1, 'hour': 7, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 2, 'hour': 7, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 3, 'hour': 7, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 26}}, 'close': {'day': 3, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 26}}}, {'open': {'day': 4, 'hour': 7, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 5, 'hour': 7, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 5, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 6, 'hour': 7, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 6, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}}], 'weekdayDescriptions': ['Monday: 7:00\u202fAM\u2009–\u20095:00\u202fPM', 'Tuesday: 7:00\u202fAM\u2009–\u20095:00\u202fPM', 'Wednesday: 7:00\u202fAM\u2009–\u20095:00\u202fPM', 'Thursday: 7:00\u202fAM\u2009–\u20095:00\u202fPM', 'Friday: 7:00\u202fAM\u2009–\u20095:00\u202fPM', 'Saturday: 7:00\u202fAM\u2009–\u20095:00\u202fPM', 'Sunday: 7:00\u202fAM\u2009–\u20095:00\u202fPM'], 'nextOpenTime': '2025-03-27T00:00:00Z'}, Website=None, GoogleLink='https://maps.google.com/?cid=17727771599023706276', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31d972476c0892b3:0xf605b257f31110a4!3e0")]

@app.route('/scrapper', methods=["GET", "POST"])
# @sleep_and_retry
# @limits(calls=1, period=60) #todo - supposedly doesnt work quite well, but im not expecting massive traffic so... DEFERRED
# @lru_cache(maxsize=256)
def scrape_address() -> Response: #todo fix the response() return with jsonify and change fe to match
    '''
    scrapes html from url in query string, and retrieves all address strings from html
    '''
    # i could do this in firecrawl but it costs 19/month naurrr wayy
    url = request.args.get("url")
    logger.info("requested url = {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if not response.ok:
        logger.error(f"failed to fetch webpage, err = {response.text}")
        return Response(response.status_code, "failed to retrieve page", {})
    soup = BeautifulSoup(response.text, 'html.parser')
    response.close()
    text = "\n".join([text.strip() for text in soup.stripped_strings])
    address = generate_address(text)
    logger.info("generated information = {address}")
    print("address", address)
    result = generate_markers(address)
    print("result", result)
    return Response(200, "success", result)

def generate_address(text: str) -> Dict[str, List[str]]:
    '''
    model parses html text and returns json containing address information
    '''
    client = OpenAI(
        api_key = OPENAI_TOKEN
    )
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        store=True,
        messages=[
            { "role": "system", "content": "You are a helpful assistant." },
                {"role": "developer", "content": "Extract all names and addresses of each business listed in the following text that is scrapped from a webpage. Return only a json map object with the business name as key, and a string array of addresses of that business as the value. If there are no associated address of that business name, keep the value as an empty array. "+text}
        ]
    )
    resp = completion.choices[0].message.content
    resp = resp.replace('```', '').replace('\n', '') #todo: find a fix
    print("resp", resp)
    if resp[:4] == 'json':
        resp = resp[4:]
    try:
        address = eval(resp)
    except Exception as error:
        logger.error(f"failed to extract {resp}, err = {error}")
        raise
    return address

def generate_markers(addressStruct: Dict[str, List[str]]) -> List[PlaceInfo]:
    '''
    takes address map and queries, for each address, its location information as defined by PlaceInfo
    '''
    address_info = []
    for name, addresses in addressStruct.items():
        if len(addresses) == 0:
            addresses.append('')
        for address in addresses:
            info = map_info(name + " " + address)
            if not info:
                continue
            address_info.append(info)
    return address_info

def map_info(address: str) -> Optional[PlaceInfo]:
    fields = ','.join(PlaceSearchFieldsNew_Free + PlaceSearchFieldsNew_Basic + (PlaceSearchFieldsNew_Premium if PremiumUser else []))
    detail_params = {
        "textQuery": address
    }
    detail_headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_TOKEN,
        "X-Goog-FieldMask":fields 
    }
    try:
        detail_response = requests.post(
            PlaceSearchDomainNew, 
            params=detail_params,
            headers=detail_headers
        )
    except Exception as error:
        logger.error(f"google info fetch failed, param={detail_params}, err = {error}")
        return None
    detail_data = detail_response.json().get("places", "")
    if not detail_response.ok or not detail_data:
        logger.error(f"google info fetch failed, param={detail_params}, err = {detail_response.text}")
        return None
    detail = detail_data[0]
    return PlaceInfo(
        Id=detail.get("id", ""),
        Name=detail.get("displayName", {}).get("text", ""),
        Address=detail.get("formattedAddress", ""),
        Lat=detail.get("location", {}).get("latitude", ""),
        Long=detail.get("location", {}).get("longitude", ""),
        Status=detail.get("businessStatus", ""),
        Rating=detail.get("rating", None),
        RatingCount=detail.get("userRatingCount",  None),
        PriceLevel=detail.get("priceLevel",  None),
        OpeningHours=detail.get("currentOpeningHours",  None),
        Website=detail.get("websiteUri",  None),
        GoogleLink=detail.get("googleMapsLinks",  {}).get("placeUri", None),
        DirectionLink=detail.get("googleMapsLinks",  {}).get("directionsUri", None)
    )

# def default_map_info(address: str) -> Optional[PlaceInfo]:
#     detail_response = gmaps.find_place(
#             address,
#             "textquery",
#             fields=PlaceSearchField_LEGACY,
#             # language=self.language,
#         )
#     if detail_response["status"] != "OK":
#         logger.error(f"google info fetch failed, param={address}, err = {detail_response}")
#         return None
#     return PlaceInfo()

@app.route('/telegram-webhook', methods=['POST'])
def webhook():
    # Verify secret token
    # if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != TELEGRAM_BOT_TOKEN:
    #     return 'Unauthorized', 401
    
    # # Process update
    # update = Update.de_json(request.get_json(), TelegramBot)
    # chat_id = update.message.chat.id
    # msg_id = update.message.message_id
    # text = update.message.text.encode('utf-8').decode()

    # print("got text message :", text)
    # TelegramBot.sendMessage(chat_id=chat_id, text="test", reply_to_message_id=msg_id)
    
    return 'OK', 200

# @app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
# async def webhook():
#     """Handle Telegram webhook requests"""
#     try:
#         # Get the update from Telegram
#         update_json = request.get_json(force=True)
#         logger.info(f"Received update: {update_json}")
        
#         # Process the update
#         if TelegramBot is None:
#             logger.error("TelegramBot is not initialized")
#             return Response(status=500)
#         update = Update.de_json(update_json, TelegramBot.bot)
#         # todo: persist or queue updates asynchronously
#         # Store and broadcast the message if it exists
#         if update.message:
#             if update.message.text:
#                 chat_id = str(update.message.chat_id)
#                 message_data = {
#                     'chat_id': chat_id,
#                     'text': update.message.text,
#                     'sender': update.message.from_user.username or "Unknown",
#                     'timestamp': update.message.date.isoformat()
#                 }
                
#                 # Store the latest message
#                 latest_messages[chat_id] = message_data
                
#                 # Broadcast to all connected clients
#                 socketio.emit('new_telegram_message', message_data)
#             elif update.message.location:
#                 # Handle location updates
#                 chat_id = str(update.message.chat_id)
#                 location_data = {
#                     'chat_id': chat_id,
#                     'latitude': update.message.location.latitude,
#                     'longitude': update.message.location.longitude,
#                     'sender': update.message.from_user.username or "Unknown",
#                     'timestamp': update.message.date.isoformat()
#                 }
#                 # Store the latest message
#                 latest_messages[chat_id] = location_data
                
#                 # Broascast to all connected clients
#                 socketio.emit('new_telegram_message', location_data)
#         # Process the update using asyncio
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         loop.run_until_complete(TelegramBot.process_update(update))
#         # await TelegramBot.process_update(update)
#         return Response(status=200)
#     except Exception as e:
#         logger.error(f"Error processing webhook: {e}")
#         return Response(status=500)
