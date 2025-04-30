from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from consts import *
from bot import TelegramBot
from bs4 import BeautifulSoup
from openai import OpenAI
import requests
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from functools import lru_cache
import sys
import logging
from typing import Dict, List, Tuple, Any, Optional
from ratelimit import limits, sleep_and_retry
from threading import Thread
from flask_socketio import SocketIO
import itertools
import hashlib
import redis
import json
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import easyocr
import pytesseract
import numpy as np
from PIL import Image
import io
import cv2

# Set up logging
logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler(sys.stdout)
console_format = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s | %(module)s:%(lineno)d'
    )
console_handler.setFormatter(console_format)
if logger.hasHandlers():
        logger.handlers.clear()
logger.addHandler(console_handler)

# Set up Redis
# redis_client = redis.Redis(host='localhost', port=6379, db=0)
# redis_process = subprocess.Popen(['redis-server'], 
#                                 stdout=subprocess.PIPE,
#                                 stderr=subprocess.PIPE)
                                
# Set up Flask
app = Flask(__name__)
app.config['REDIS_URL'] = 'redis://localhost:6379/0'
app.redis = redis.Redis.from_url(app.config['REDIS_URL'])


CORS(app, resources={
    r"/*": {
        "origins": ["*"],# ["http://localhost:5173/","https://aumi-gamma.vercel.app"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "ngrok-skip-browser-warning"]
    }
})

@app.route('/', methods=["GET", "POST"])
def hewwo():
    return str(TelegramBot == None)

@app.route('/google_token', methods=["GET", "POST"])
def get_google_token():
    return generate_response({"token": GOOGLE_TOKEN}, 200)

# @app.route('/openai_token', methods=["GET", "POST"])
# def get_openai_token():
#     response = jsonify({"token": OPENAI_TOKEN})
#     response.headers.add("Access-Control-Allow-Origin", "*")
#     response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
#     response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
#     return response

@app.route('/test_scrapper_error', methods=["GET", "POST"])
def get_test_scrapper_error():
    return generate_response({"error": "test err"}, 500) 

@app.route('/test_scrapper', methods=["GET", "POST"])
def get_test_scrapper():
    return generate_response([PlaceInfo(Id='ChIJtwgHgJMZ2jERCExG-EjFa6M', Name='Equate Coffee', Address='1 Tanjong Pagar Plz, #02-25, Singapore 082001', Lat=1.2748632, Long=103.8426344, Status='OPERATIONAL', Rating=4.6, RatingCount=209, PriceLevel=None, OpeningHours={'openNow': False, 'periods': [{'open': {'day': 1, 'hour': 8, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 17, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 2, 'hour': 8, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 17, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 3, 'hour': 8, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 17, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 4, 'hour': 8, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 17, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 5, 'hour': 8, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 5, 'hour': 17, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 6, 'hour': 8, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 6, 'hour': 15, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}}], 'weekdayDescriptions': ['Monday: 8:30\u202fAM\u2009–\u20095:30\u202fPM', 'Tuesday: 8:30\u202fAM\u2009–\u20095:30\u202fPM', 'Wednesday: 8:30\u202fAM\u2009–\u20095:30\u202fPM', 'Thursday: 8:30\u202fAM\u2009–\u20095:30\u202fPM', 'Friday: 8:30\u202fAM\u2009–\u20095:30\u202fPM', 'Saturday: 8:30\u202fAM\u2009–\u20093:00\u202fPM', 'Sunday: Closed'], 'nextOpenTime': '2025-03-27T00:30:00Z'}, Website='https://www.equate.sg/', GoogleLink='https://maps.google.com/?cid=11775722567883967496', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da1993800708b7:0xa36bc548f8464c08!3e0"), PlaceInfo(Id='ChIJ4wutVe4Z2jERDUp3XtrAkeE', Name='Fieldnotes, Neil Road', Address='41 Neil Rd, Singapore 088824', Lat=1.2797561, Long=103.8428418, Status='OPERATIONAL', Rating=4.7, RatingCount=605, PriceLevel=None, OpeningHours={'openNow': False, 'periods': [{'open': {'day': 0, 'hour': 11, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 0, 'hour': 20, 'minute': 45, 'date': {'year': 2025, 'month': 3, 'day': 30}}}, {'open': {'day': 1, 'hour': 11, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 20, 'minute': 45, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 2, 'hour': 11, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 20, 'minute': 45, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 3, 'hour': 11, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 20, 'minute': 45, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 4, 'hour': 11, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 20, 'minute': 45, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 5, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 5, 'hour': 22, 'minute': 45, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 6, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 6, 'hour': 22, 'minute': 45, 'date': {'year': 2025, 'month': 3, 'day': 29}}}], 'weekdayDescriptions': ['Monday: 11:30\u202fAM\u2009–\u20098:45\u202fPM', 'Tuesday: 11:30\u202fAM\u2009–\u20098:45\u202fPM', 'Wednesday: 11:30\u202fAM\u2009–\u20098:45\u202fPM', 'Thursday: 11:30\u202fAM\u2009–\u20098:45\u202fPM', 'Friday: 11:00\u202fAM\u2009–\u200910:45\u202fPM', 'Saturday: 11:00\u202fAM\u2009–\u200910:45\u202fPM', 'Sunday: 11:30\u202fAM\u2009–\u20098:45\u202fPM'], 'nextOpenTime': '2025-03-27T03:30:00Z'}, Website='http://www.fieldnotes.com.sg/', GoogleLink='https://maps.google.com/?cid=16253984574277110285', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da19ee55ad0be3:0xe191c0da5e774a0d!3e0"), PlaceInfo(Id='ChIJEZX2E0gZ2jER1zo5m4LC3fM', Name="Papi's Tacos - Tanjong Pagar", Address='33 Tg Pagar Rd, #01-01, Singapore 088456', Lat=1.279188, Long=103.844008, Status='OPERATIONAL', Rating=4.3, RatingCount=460, PriceLevel=None, OpeningHours={'openNow': False, 'periods': [{'open': {'day': 0, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 0, 'hour': 14, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 30}}}, {'open': {'day': 0, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 0, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}}, {'open': {'day': 1, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 14, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 1, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 2, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 14, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 2, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 3, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 14, 'minute': 30, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 3, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 4, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 14, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 4, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 5, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 5, 'hour': 14, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 5, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 6, 'hour': 0, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}}, {'open': {'day': 6, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 6, 'hour': 14, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 29}}}, {'open': {'day': 6, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 0, 'hour': 0, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}}], 'weekdayDescriptions': ['Monday: 12:00\u2009–\u20092:30\u202fPM, 5:00\u2009–\u200911:00\u202fPM', 'Tuesday: 12:00\u2009–\u20092:30\u202fPM, 5:00\u2009–\u200911:00\u202fPM', 'Wednesday: 12:00\u2009–\u20092:30\u202fPM, 5:00\u2009–\u200911:00\u202fPM', 'Thursday: 12:00\u2009–\u20092:30\u202fPM, 5:00\u2009–\u200911:00\u202fPM', 'Friday: 12:00\u2009–\u20092:30\u202fPM, 5:00\u202fPM\u2009–\u200912:00\u202fAM', 'Saturday: 11:00\u202fAM\u2009–\u20092:30\u202fPM, 5:00\u202fPM\u2009–\u200912:00\u202fAM', 'Sunday: 11:00\u202fAM\u2009–\u20092:30\u202fPM, 5:00\u2009–\u200911:00\u202fPM'], 'nextOpenTime': '2025-03-27T04:00:00Z'}, Website='http://www.papis-tacos.com/', GoogleLink='https://maps.google.com/?cid=17572415187275299543', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da194813f69511:0xf3ddc2829b393ad7!3e0"), PlaceInfo(Id='ChIJKeC0vJIZ2jERAsl1O-3x-00', Name='Glasshouse', Address='136 Neil Rd, #01-01, Singapore 088865', Lat=1.2783727999999999, Long=103.8408894, Status='OPERATIONAL', Rating=4.3, RatingCount=298, PriceLevel='PRICE_LEVEL_MODERATE', OpeningHours={'openNow': False, 'periods': [{'open': {'day': 0, 'hour': 8, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 0, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}}, {'open': {'day': 1, 'hour': 8, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 2, 'hour': 8, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 3, 'hour': 8, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 4, 'hour': 8, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 5, 'hour': 8, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 5, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 6, 'hour': 8, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 6, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}}], 'weekdayDescriptions': ['Monday: 8:00\u202fAM\u2009–\u20096:00\u202fPM', 'Tuesday: 8:00\u202fAM\u2009–\u20096:00\u202fPM', 'Wednesday: 8:00\u202fAM\u2009–\u20096:00\u202fPM', 'Thursday: 8:00\u202fAM\u2009–\u20096:00\u202fPM', 'Friday: 8:00\u202fAM\u2009–\u20096:00\u202fPM', 'Saturday: 8:00\u202fAM\u2009–\u20096:00\u202fPM', 'Sunday: 8:00\u202fAM\u2009–\u20096:00\u202fPM'], 'nextOpenTime': '2025-03-27T00:00:00Z'}, Website='http://theglasshousesg.com/', GoogleLink='https://maps.google.com/?cid=5619350961281943810', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da1992bcb4e029:0x4dfbf1ed3b75c902!3e0"), PlaceInfo(Id='ChIJM323rE0Z2jERWMg9G23kIBg', Name='CAFE KREAMS', Address='32 Maxwell Rd, #01-07 Maxwell Chambers, Singapore 069115', Lat=1.2775235, Long=103.84631999999999, Status='OPERATIONAL', Rating=4.4, RatingCount=1115, PriceLevel=None, OpeningHours={'openNow': False, 'periods': [{'open': {'day': 0, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 0, 'hour': 22, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}}, {'open': {'day': 1, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 22, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 2, 'hour': 9, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 3, 'hour': 9, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 4, 'hour': 9, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 5, 'hour': 9, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 5, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 6, 'hour': 9, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 6, 'hour': 23, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}}], 'weekdayDescriptions': ['Monday: 11:00\u202fAM\u2009–\u200910:00\u202fPM', 'Tuesday: 9:00\u202fAM\u2009–\u200911:00\u202fPM', 'Wednesday: 9:00\u202fAM\u2009–\u200911:00\u202fPM', 'Thursday: 9:00\u202fAM\u2009–\u200911:00\u202fPM', 'Friday: 9:00\u202fAM\u2009–\u200911:00\u202fPM', 'Saturday: 9:00\u202fAM\u2009–\u200911:00\u202fPM', 'Sunday: 11:00\u202fAM\u2009–\u200910:00\u202fPM'], 'specialDays': [{'date': {'year': 2025, 'month': 3, 'day': 31}}], 'nextOpenTime': '2025-03-27T01:00:00Z'}, Website='http://www.kreams.sg/', GoogleLink='https://maps.google.com/?cid=1738640613424613464', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da194dacb77d33:0x1820e46d1b3dc858!3e0"), PlaceInfo(Id='ChIJnS0ilrwZ2jERg66Abhmv33Y', Name='DOPA', Address='7 Tanjong Pagar Plz, #01-107, Singapore 081007', Lat=1.2773010999999999, Long=103.8428332, Status='OPERATIONAL', Rating=4.1, RatingCount=263, PriceLevel=None, OpeningHours={'openNow': False, 'periods': [{'open': {'day': 0, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 0, 'hour': 22, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}}, {'open': {'day': 1, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 22, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 2, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 22, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 3, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 22, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 4, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 22, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 5, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 5, 'hour': 22, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 6, 'hour': 12, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 6, 'hour': 22, 'minute': 30, 'date': {'year': 2025, 'month': 3, 'day': 29}}}], 'weekdayDescriptions': ['Monday: 12:00\u2009–\u200910:00\u202fPM', 'Tuesday: 12:00\u2009–\u200910:00\u202fPM', 'Wednesday: 12:00\u2009–\u200910:00\u202fPM', 'Thursday: 12:00\u2009–\u200910:00\u202fPM', 'Friday: 12:00\u2009–\u200910:30\u202fPM', 'Saturday: 12:00\u2009–\u200910:30\u202fPM', 'Sunday: 12:00\u2009–\u200910:00\u202fPM'], 'nextOpenTime': '2025-03-27T04:00:00Z'}, Website='http://www.dopadopacreamery.com/', GoogleLink='https://maps.google.com/?cid=8565757540044942979', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da19bc96222d9d:0x76dfaf196e80ae83!3e0"), PlaceInfo(Id='ChIJ7xlFdKwT2jERXrseJIzS6tI', Name='Citrus By The Pool', Address='3 Woodlands Street 13, Woodlands Swimming Complex, Singapore 738600', Lat=1.4344838, Long=103.77948479999999, Status='OPERATIONAL', Rating=4.9, RatingCount=21379, PriceLevel='PRICE_LEVEL_MODERATE', OpeningHours={'openNow': True, 'periods': [{'open': {'day': 0, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 1, 'hour': 5, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 1, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 2, 'hour': 5, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 2, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 3, 'hour': 5, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 3, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 2}}, 'close': {'day': 3, 'hour': 23, 'minute': 59, 'truncated': True, 'date': {'year': 2025, 'month': 4, 'day': 2}}}, {'open': {'day': 4, 'hour': 0, 'minute': 0, 'truncated': True, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 5, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 4, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 5, 'hour': 5, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 5, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 6, 'hour': 5, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}}, {'open': {'day': 6, 'hour': 11, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 0, 'hour': 5, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}}], 'weekdayDescriptions': ['Monday: 11:00\u202fAM\u2009–\u20095:00\u202fAM', 'Tuesday: 11:00\u202fAM\u2009–\u20095:00\u202fAM', 'Wednesday: 11:00\u202fAM\u2009–\u20095:00\u202fAM', 'Thursday: 11:00\u202fAM\u2009–\u20095:00\u202fAM', 'Friday: 11:00\u202fAM\u2009–\u20095:00\u202fAM', 'Saturday: 11:00\u202fAM\u2009–\u20095:00\u202fAM', 'Sunday: 11:00\u202fAM\u2009–\u20095:00\u202fAM'], 'nextCloseTime': '2025-03-26T21:00:00Z'}, Website='http://www.citrusbythepool.com/', GoogleLink='https://maps.google.com/?cid=15198191391858408286', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da13ac744519ef:0xd2ead28c241ebb5e!3e0"), PlaceInfo(Id='ChIJs5IIbEdy2TERpBAR81eyBfY', Name='Bintan Indah Mall', Address='WCJR+JHG, Tanjungpinang Kota, Tanjung Pinang Kota, Tanjung Pinang City, Riau Islands, Indonesia', Lat=0.9315743, Long=104.4414432, Status='OPERATIONAL', Rating=4, RatingCount=455, PriceLevel=None, OpeningHours={'openNow': False, 'periods': [{'open': {'day': 0, 'hour': 7, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}, 'close': {'day': 0, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 30}}}, {'open': {'day': 1, 'hour': 7, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}, 'close': {'day': 1, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 31}}}, {'open': {'day': 2, 'hour': 7, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}, 'close': {'day': 2, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 4, 'day': 1}}}, {'open': {'day': 3, 'hour': 7, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 26}}, 'close': {'day': 3, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 26}}}, {'open': {'day': 4, 'hour': 7, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}, 'close': {'day': 4, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 27}}}, {'open': {'day': 5, 'hour': 7, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}, 'close': {'day': 5, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 28}}}, {'open': {'day': 6, 'hour': 7, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}, 'close': {'day': 6, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 3, 'day': 29}}}], 'weekdayDescriptions': ['Monday: 7:00\u202fAM\u2009–\u20095:00\u202fPM', 'Tuesday: 7:00\u202fAM\u2009–\u20095:00\u202fPM', 'Wednesday: 7:00\u202fAM\u2009–\u20095:00\u202fPM', 'Thursday: 7:00\u202fAM\u2009–\u20095:00\u202fPM', 'Friday: 7:00\u202fAM\u2009–\u20095:00\u202fPM', 'Saturday: 7:00\u202fAM\u2009–\u20095:00\u202fPM', 'Sunday: 7:00\u202fAM\u2009–\u20095:00\u202fPM'], 'nextOpenTime': '2025-03-27T00:00:00Z'}, Website=None, GoogleLink='https://maps.google.com/?cid=17727771599023706276', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31d972476c0892b3:0xf605b257f31110a4!3e0")], 200)


### Fetching post/ website shop info ###

# returns resp.text if html and resp.json if json
def fetch_website(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 10,
    allow_redirects: bool = True,
    is_html = True
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    logger.info(f"Fetching website: {url}")
    print("fetching website", url)
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            data=data,
            json=json_data,
            timeout=timeout,
            allow_redirects=allow_redirects
        )
        response.raise_for_status()
        if is_html:
            return response.text, None
        return response.json(), None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        return None, error_msg
    except ValueError as e:
        error_msg = f"Failed to decode JSON response: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        return None, error_msg

# ocr from image
def extract_text_from_url(image_url):
    logger.info(f"extracting text from url: {image_url}")
    print("extracting text from url", image_url)
    response = requests.get(image_url)
    if response.status_code != 200:
        # return f"Failed to download image: HTTP {response.status_code}"
        logger.error(f"Failed to download image: from {image_url}", exc_info=True)
        print(f"Failed to download image: from {image_url}")
        return ''
    image_bytes = io.BytesIO(response.content)
    img = Image.open(image_bytes)

    # preprocess ## todo - find a more refined preprocessor 
    # grayscale
    img_array = np.array(img)
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    # sharpen
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(gray, -1, kernel)
    # CLAHE (Contrast Limited Adaptive Histogram Equalization) to separate text from photo background
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    clahe_img = clahe.apply(sharpened)
    kernel = np.ones((2, 2), np.uint8)
    eroded = cv2.erode(clahe_img, kernel, iterations=1)
    dilated = cv2.dilate(eroded, kernel, iterations=1)
    # EasyOCR
    reader = easyocr.Reader(['en'])
    easyocr_results = reader.readtext(dilated, detail=0)
    easyocr_text = " ".join(easyocr_results)
    return easyocr_text

# Handle tiktok data:

# fetches from image links found
def handle_tiktok_photo(tiktok_url):
    logger.info(f"extracting text from tiktok photo: {tiktok_url}")
    print("extracting text from tiktok photo", tiktok_url)
    url = TIKTOK_PHOTO_URL
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/json',
        'origin': TIKTOK_PHOTO_URL,
        'priority': 'u=1, i',
        'referer': TIKTOK_PHOTO_REFERER_URL,
        'user-agent': 'Mozilla/5.0'
    }
    payload = {
        "query": tiktok_url,
        "language_id": "1"
    }
    data, err = fetch_website(url=url, headers=headers, method="POST", params=payload, timeout=timeout)
    if err != None:
        return None, err
    soup = BeautifulSoup(data, 'html.parser')   
    urls = []
    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        if 'tiktokcdn' in link and link[-8:] == "sc=image":
            urls.append(a_tag['href'])
    texts = []
    for image_url in urls:
        text = extract_text_from_url(image_url)
        texts.append(text)
    result = '. '.join(texts)
    logger.info(f"extracted text from tiktok photo: {result}")
    print("extracted text from tiktok photo", result)
    return result, None

# get subtitles and description from video if possible
def handle_tiktok_video(tiktok_url):
    logger.info(f"extracting text from tiktok video: {tiktok_url}")
    print("extracting text from tiktok video", tiktok_url)
    url = TIKTOK_VIDEO_URL + tiktok_url
    headers = {
        'Origin': 'https://script.tokaudit.io',
        'Referer': 'https://script.tokaudit.io/',
        'User-Agent': 'Mozilla/5.0 ()',
        'Host': 'scriptadmin.tokbackup.com',
        'x-api-key': 'Toktools2024@!NowMust'
    }
    data, err = fetch_website(url=url, headers=headers, timeout=timeout, is_html=False)
    if err != None:
        return None, err
    subtitle = fetch_subtitles(data)
    description = fetch_descriptions(data['data'])
    logger.info(f"extracted subtitle: {subtitle}, description: {description}")
    print(f"extracted subtitle: {subtitle}, description: {description}")
    return description + ' ' + subtitle, None
 
def fetch_descriptions(data):
    if not data or 'desc' not in data:
        return ""
    return data['desc']
    
def fetch_subtitles(data):
    subtitles = []
    if 'subtitles' not in data or not data['subtitles']:
        return ""
    for i in data['subtitles'].split('\n\n'): #parsing manually as millisecond is missing for webvtt-py to work
        sub = i.split('\n')
        if len(sub) <= 1:
            continue
        subtitles.append(sub[1])
    return ' '.join(subtitles)

# reduce external api calls
def check_tiktok_type(url: str) -> str:
    if "/photo/" in url:
        return 'photo'
    elif "/video/" in url:
        return 'video'
    else:
        logger.warn(f"unknown media type in url: {url}")
        return f"unknown media type in url: {url}"


# Handle rednote data:

def handle_rednote_photo(url):
    logger.info(f"extracting text from rednote photo: {url}")
    print("extracting text from rednote photo", url)
    data, err = fetch_website(url=url)
    if err != None:
        return None, err
    soup = BeautifulSoup(data, 'html.parser') 
    desc = soup.find('meta', {'name': 'description'}).get('content')
    links = [i.get('content') for i in soup.find_all('meta', {'name': 'og:image'})]
    texts = []
    for image_url in links:
        text = extract_text_from_url(image_url)
        texts.append(text)
    result = '. '.join(texts)
    logger.info(f"extracted text from rednote photo: {result}")
    print("extracted text from rednote photo", result)
    return result, None


# Handle normal (blog post) website data:

def handle_website(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    data, err = fetch_website(url=url, headers=headers)
    if err != None:
        return None, err
    soup = BeautifulSoup(response.text, 'html.parser')
    result = "\n".join([text.strip() for text in soup.stripped_strings])
    return result, None

@app.route('/scrapper', methods=["GET", "POST"])
# @sleep_and_retry
# @lru_cache(maxsize=256) #lru local cache on top of redis caching
def scrape_address() -> Response:
    '''
    handles urls based on its origin, and returns a list of PlaceInfo objects to display
    '''
    url = request.args.get("url")
    if not url:
        return generate_response({"error": "URL is empty"}, 400)
    parsed = urlparse(url)
    if not all([parsed.scheme, parsed.netloc]):
        return generate_response({"error": "Invalid URL format"}, 400)
    print("requested url", url)
    logger.info("requested url = {url}")
    cache_key = get_cache_key(url)
    cached_data = get_cache(cache_key)
    if cached_data:
        logger.info("cache hit")
        print("cache hit")
        return generate_response(cached_data, 200)
    res, err = None, None
    # fetch from tiktok
    if parsed.netloc in ("vt.tiktok.com", "www.tiktok.com"):
        try:
            response = requests.head(url, allow_redirects=True)
            url = response.url
        except Exception as e:
            err = f"cannot fetch ultimate url of tiktok post, err: {e}"
            logger.error(err, exc_info=True)
            print(err)
            return generate_response({"error": err}, 400)
        media_type = check_tiktok_type(url)
        if media_type == 'photo':
            res, err = handle_tiktok_photo(url)
        elif media_type =='video':
            res, err = handle_tiktok_video(url)
        else:
            err = "tiktok post type cannot be identified"
    # fetch from rednote
    elif parsed.netloc == "www.xiaohongshu.com":
         res, err = handle_rednote_photo(url)
    # fetch from instagram or facebook
    elif parsed.netloc == "www.instagram.com" or parsed.netloc == "www.facebook.com":
        err = "instagram and facebook links are not supported" 
    # fetch from website
    else:
        res, err = handle_website(url)
    if err:
        logger.error(err, exc_info=True)
        print(f"failed to fetch from {url}, err={err}")
        return generate_response({"error": f"failed to fetch from {url}, err={err}"}, 500)
    logger.info("text identified = {res}")
    print("text identified =", res)
    address = generate_address_from_model(res)
    logger.info("generated information = {address}")
    print("address", address)
    result = generate_markers(address, 3)
    logger.info("generated information = {address}")
    print("result", result)
    # Convert PlaceInfo objects to dictionaries
    result_dicts = [vars(place) for place in result]
    if len(result) > 0:
        set_cache(cache_key, result_dicts)
    return generate_response(result_dicts, 200)

def generate_response(res: any, status: int) -> Response:
    response = jsonify(res)
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.status_code = status
    return response 


def get_cache_key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()

def set_cache(key: str, data: Any) -> None:
    try:
        app.redis.setex(key, redis_expiry, json.dumps(data))
    except redis.RedisError as e:
        logger.error(f"Redis cache error: {str(e)}")
        print(f"Redis cache error: {str(e)}")

def get_cache(key: str) -> Optional[Any]:
    try:
        data = app.redis.get(key)
        if data:
            return json.loads(data)
    except (redis.RedisError, json.JSONDecodeError) as e:
        print(f"Redis cache retrieval error: {str(e)}")
    return None

def generate_address_from_model(text: str) -> Dict[str, List[str]]: #todo more address than needed is fetched in https://www.lemon8-app.com/@quinnelovv/7227439546152272385?region=sg do some parsing for websites, find a prompt that generates the top relevant ones
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
            { "role": "system", "content": "You are a helpful assistant. The following messages are scrapped from websites or video captions/audio that contains one or more location recommendations. Use your best discretion to discern which businesses are relevant, then extract their names and addresses. Return only a json map object with the business name as key, and a string array of addresses of that business as value (empty array if not found)." },
            {"role": "developer", "content": text}
            # todo - replace prompt and add hints e.g numbered point forms
            # todo - focus on eliminating false positives - better exclude than to be wrong
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

def generate_markers(addressStruct: Dict[str, List[str]], mode: int = 2) -> List[PlaceInfo]:
    '''
    takes address map and queries, for each address, its location information as defined by PlaceInfo
    '''
    address_info = []
    for name, addresses in addressStruct.items():
        if len(addresses) == 0:
            addresses.append('')
        for address in addresses:
            info = map_info(name + " " + address, mode)
            if not info:
                continue
            address_info.append(info)
    return address_info

@app.route('/single_address', methods=["GET", "POST"])
def generate_single_address() -> Response:
    address = request.args.get('address')
    print("address", address)
    if not address:
        return jsonify({"error": "address is required"}), 400
    res = map_info(address)
    print("res", res)
    response = jsonify(res)
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.status_code = 200 
    return response

def map_info(address: str, mode: int = 2) -> Optional[PlaceInfo]:
    allowed_fields = [PlaceSearchFieldsNew_Free, PlaceSearchFieldsNew_Basic, PlaceSearchFieldsNew_Premium][:mode]
    fields = ','.join(list(itertools.chain(*allowed_fields)))
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
