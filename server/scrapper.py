from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from consts import *
from bot import TelegramBot
from bs4 import BeautifulSoup
from openai import OpenAI
import requests
import trafilatura
from readability import Document
# from telegram.ext import Application, CommandHandler, MessageHandler, filters
from functools import lru_cache
import sys
import logging
from typing import Dict, List, Tuple, Any, Optional
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import itertools
import hashlib
import redis
import json
from urllib.parse import urlparse, quote
# from urllib.request import Request, urlopen
import easyocr
# import pytesseract
import numpy as np
from PIL import Image
import io
import cv2
# import random
import socket
import ipaddress
import re
from html import escape
import nh3

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
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["10 per day", "1 per hour"],
    storage_uri="redis://localhost:6379"
)


CORS(app, resources={
    r"/*": {
        "origins": ["*"],# ["http://localhost:5173/","https://aumi-gamma.vercel.app"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "ngrok-skip-browser-warning"]
    }
})

@app.route('/', methods=["GET", "POST"])
def hewwo():
    return "im up"

@app.route('/google_token', methods=["GET", "POST"])
@limiter.limit("60 per minute") 
def get_google_token():
    return generate_response({"token": GOOGLE_TOKEN}, 200)

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
        # Create session with connection pooling limits
        with requests.Session() as session:
            session.max_redirects = 5  # Limit redirects to prevent loops
            
            response = session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                timeout=timeout,
                allow_redirects=allow_redirects,
                stream=True  # Stream to check content length
            )
            
            # Check content type
            content_type = response.headers.get('Content-Type', '').lower()
            if not any(allowed in content_type for allowed in ALLOWED_CONTENT_TYPES):
                response.close()
                return None, f"Unsupported content type: {content_type}"
            
            # Check content length
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > MAX_CONTENT_LENGTH:
                response.close()
                return None, f"Response too large: {content_length} bytes"
            
            # Read with size limit
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > MAX_CONTENT_LENGTH:
                    response.close()
                    return None, "Response too large"
            
            response.raise_for_status()
            
            if is_html:
                # Decode and return text
                text_content = content.decode('utf-8', errors='ignore')
                return text_content, None
            else:
                # Parse JSON
                json_content = json.loads(content.decode('utf-8', errors='ignore'))
                return json_content, None
        
    except requests.exceptions.Timeout:
        error_msg = f"Request timed out after {timeout} seconds"
        logger.error(error_msg)
        return None, error_msg
    except requests.exceptions.TooManyRedirects:
        error_msg = "Too many redirects"
        logger.error(error_msg)
        return None, error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg
    except (ValueError, json.JSONDecodeError) as e:
        error_msg = f"Failed to decode response: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg

# ocr from image
def process_image_text(image_bytes):
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
    easyocr_results = reader.readtext(dilated, paragraph=True, detail=0)
    easyocr_text = " ".join(easyocr_results)
    return easyocr_text

def extract_text_from_url(image_url, session=None):
    logger.info(f"extracting text from url: {image_url}")
    print("extracting text from url", image_url)
    
    try:
        # Use provided session or create a one-off request
        if session:
            response = session.get(image_url, timeout=timeout, stream=True)
        else:
            response = requests.get(image_url, timeout=timeout, stream=True)
        
        # Check content type is an image
        content_type = response.headers.get('Content-Type', '').lower()
        if not any(img_type in content_type for img_type in ALLOWED_IMG_TYPES):
            logger.error(f"Invalid content type for image: {content_type}")
            return ''
        
        # Limit image size to prevent DoS
        max_image_size = 20 * 1024 * 1024  # 20MB
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > max_image_size:
            logger.error(f"Image too large: {content_length} bytes")
            return ''
        
        # Read image with size limit
        image_data = b''
        for chunk in response.iter_content(chunk_size=8192):
            image_data += chunk
            if len(image_data) > max_image_size:
                response.close()
                logger.error("Image too large during download")
                return ''
        
        if response.status_code != 200:
            logger.error(f"Failed to download image: from {image_url}")
            print(f"Failed to download image: from {image_url}")
            return ''
        
        image_bytes = io.BytesIO(image_data)
        easyocr_text = process_image_text(image_bytes)
        return easyocr_text
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading image from {image_url}: {e}")
        return ''
    except Exception as e:
        logger.error(f"Error processing image from {image_url}: {e}")
        return ''

def extract_text_from_urls(image_urls):
    """
    Extract text from multiple images concurrently using OCR.
    
    Args:
        image_urls: List of image URLs to process
        
    Returns:
        List of extracted text strings (escaped for safety)
    """
    if not image_urls:
        return []
    if len(image_urls) == 1:
        return [extract_text_from_url(image_urls[0])]
    
    texts = []
    
    # Create a session for connection pooling
    with requests.Session() as session:
        # Configure session for better performance
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=3
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        # Process images concurrently
        with ThreadPoolExecutor(max_workers=min(len(image_urls), 5)) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(extract_text_from_url, url, session): url 
                for url in image_urls
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    text = future.result()
                    if text:
                        texts.append(escape(text))
                except Exception as e:
                    logger.error(f"Failed to extract text from {url}: {e}")
                    print(f"Failed to extract text from {url}: {e}")
    
    return texts

# Handle tiktok data:

# fetches from image links found
def handle_tiktok_photo(tiktok_url):
    logger.info(f"extracting text from tiktok photo: {tiktok_url}")
    print("extracting text from tiktok photo", tiktok_url)
    url = TIKTOK_PHOTO_URL
    headers = {
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': TIKTOK_PHOTO_ORIGIN_URL,
        'priority': 'u=1, i',
        'referer': TIKTOK_PHOTO_REFERER_URL,
        'user-agent': 'Mozilla/5.0'
    }
    payload = "q="+quote(tiktok_url, safe='') + "&lang=en&cftoken="
    data, err = fetch_website(url=url, headers=headers, method="POST", params=payload, timeout=timeout, is_html=False)
    if err != None:
        return None, err
    if 'data' not in data:
        return None, "Invalid response format from TikTok API"
    soup = BeautifulSoup(data['data'], 'html.parser')
    res = ""
    caption = soup.find('h3')
    if caption != None:
        # Escape caption text
        res += ("caption: "+escape(caption.text)+'\n')
    urls = []
    for img in soup.find_all('img'):
        if img.get("alt") != 'savetik':
            continue
        link = img.get("src")
        if link and 'tiktokcdn' in link:
            urls.append(link)
    
    # Extract text from all images concurrently
    texts = extract_text_from_urls(urls)
    if texts:
        res += "parsed text: "
    res += '\n'.join(texts)
    logger.info(f"extracted text from tiktok photo: {res}")
    print("extracted text from tiktok photo", res)
    return res, None

# get subtitles and description from video if possible
def handle_tiktok_video(tiktok_url):
    logger.info(f"extracting text from tiktok video: {tiktok_url}")
    print("extracting text from tiktok video", tiktok_url)
    url = TIKTOK_VIDEO_URL + tiktok_url
    headers = {
        'Origin': TIKTOK_VIDEO_ORIGIN_URL,
        'Referer': TIKTOK_VIDEO_REFERER_URL,
        'User-Agent': 'Mozilla/5.0 ()',
        'Host': TIKTOK_VIDEO_HOST,
        'x-api-key': TIKTOK_VIDEO_API
    }
    data, err = fetch_website(url=url, headers=headers, timeout=timeout, is_html=False)
    if err != None:
        return None, err
    
    # Validate response format
    if not isinstance(data, dict):
        return None, "Invalid response format from TikTok video API"
    
    subtitle = fetch_subtitles(data)
    description = fetch_descriptions(data['data'])
    
    res = ''
    if subtitle:
        res += "audio: " + subtitle
    if description:
        if res:
            res += "\n"
        res += "caption: " + description
    
    logger.info(f"extracted subtitle: {subtitle}, description: {description}")
    print(f"extracted subtitle: {subtitle}, description: {description}")
    return res, None
 
def fetch_descriptions(data):
    if not data or 'desc' not in data:
        return ""
    desc = data.get('desc', '')
    # Ensure it's a string and not None
    return str(desc) if desc else ""
    
def fetch_subtitles(data):
    subtitles = []
    if 'subtitles' not in data or not isinstance(data, dict) or not data['subtitles']:
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
        logger.warning(f"unknown media type in url: {url}")
        return f"unknown media type in url: {url}"


# Handle rednote data:

def handle_rednote_photo(url) -> Tuple[Optional[str], Optional[str]]:
    logger.info(f"extracting text from rednote photo: {url}")
    print("extracting text from rednote photo", url)
    data, err = fetch_website(url=url)
    if err != None:
        return None, err
    
    soup = BeautifulSoup(data, 'html.parser')
    
    desc_tag = soup.find('meta', {'name': 'description'})
    desc = ""
    if desc_tag and desc_tag.get('content'):
        desc = escape(desc_tag.get('content'))
    if desc:
        desc += '.'
    
    links = []
    for meta_tag in soup.find_all('meta', {'name': 'og:image'}):
        content = meta_tag.get('content')
        if content:
            links.append(content)
    
    # Extract text from all images concurrently
    texts = extract_text_from_urls(links)
    
    result = desc
    if texts:
        result += '. '.join(texts)
    
    logger.info(f"extracted text from rednote photo: {result}")
    # todo - if fail, fall back on handle_website
    print("extracted text from rednote photo", result)
    return result, None

def handle_lemon8(url):
    logger.info(f"extracting text from lemon8 photo: {url}")
    print("extracting text from lemon8 photo", url)
    data, err = fetch_website(url=url)
    if err != None:
        return None, err
    soup = BeautifulSoup(data, 'html.parser')
    script_tag = soup.find_all('script', {'type': 'application/ld+json'})
    json_data = json.loads(script_tag.string)
    if 'image' in json_data:
        images = [i['url'] for i in json_data['image']]

def get_text_with_tags(soup, tags_to_keep=['b', 'li']):
    for tag in soup.find_all(True):
        if tag.name not in tags_to_keep:
            tag.unwrap()  # Remove the tag but keep its content
    return str(soup)

def sanitize_html(html_content):
    """
    Sanitize HTML content for text extraction using nh3.
    Optimized for:
    1. Security - prevents XSS and other attacks
    2. Text extraction - preserves readable content
    3. Minimal context - removes unnecessary elements to reduce token usage
    """
    if not html_content:
        return ''
    try:
        # Configure nh3 to only keep text-relevant tags
        # This dramatically reduces HTML size while preserving structure for text extraction
        cleaned = nh3.clean(
            html_content,
            tags={
                # Text content tags
                "p", "br", "h1", "h2", "h3", "h4", "h5", "h6",
                "blockquote", "pre", "code",
                # List tags
                "ul", "ol", "li",
                # Semantic tags that may contain important text
                "article", "section", "main", "aside",
                # Table tags (often contain structured data)
                "table", "tr", "td", "th", "thead", "tbody",
                # Inline tags that may affect text meaning
                "b", "strong", "i", "em", "span",
                # Link tags (keep for context but strip href)
                "a"
            },
            # Remove all attributes except these (minimizes output size)
            attributes={
                # Keep alt text for accessibility/context
                "img": {"alt"},
                # Keep table headers for structure understanding
                "th": {"scope"},
                "td": {"colspan", "rowspan"}
            },
            # Strip all URLs to prevent security issues and reduce size
            link_rel=None,
            # Remove comments entirely
            strip_comments=True,
            # Additional security: ensure no javascript: or data: URLs
            url_schemes={"http", "https"},
            # Clean up whitespace
            clean_content_tags={"script", "style"}
        )
        
        # Additional cleanup to minimize tokens
        # Remove excessive whitespace while preserving structure
        cleaned = re.sub(r'\n\s*\n+', '\n\n', cleaned)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        
        return cleaned.strip()
        
    except Exception as e:
        logger.error(f"HTML sanitization with nh3 failed: {e}")
        # Return empty string on error to be safe
        return ""

# Handle normal (blog post) website data:
def handle_website(url, headers: Optional[Dict[str, str]] = {"User-Agent": "Mozilla/5.0"}):
    data, err = fetch_website(url=url, headers=headers)
    if err != None:
        return None, err
    if not data:
        return None, "No data from fetched page"
    # Sanitize HTML to prevent XSS
    cleaned_html = sanitize_html(data)
    if not cleaned_html:
        return None, "Failed to sanitize HTML content"
    
    try:
        # 1. readability
        doc = Document(cleaned_html)
        soup = BeautifulSoup(doc.summary(), 'html.parser')
        txt1 = get_text_with_tags(soup)
        
        # 2. trafilatura with timeout
        txt2 = None
        try:
            downloaded = trafilatura.fetch_url(url, timeout=timeout)
            if downloaded:
                txt2 = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            if len(txt2) > len(txt1):
                txt1 = txt2
        except Exception as e:
            logger.warning(f"Trafilatura extraction failed: {e}")
            print(f"Trafilatura extraction failed: {e}")
        
        # baseline = beautifulsoup
        soup = BeautifulSoup(cleaned_html, 'html.parser')
        control = get_text_with_tags(soup)
        
        # Choose the best extraction
        if len(txt1) < 2000 and len(control)/len(txt1) >= 10:
            result = doc.title() + "\n" + control
        else:
            result = doc.title() + "\n" + txt1
        
        # Final escape of any HTML entities for safety
        result = escape(result, quote=False)
        
        return result, None
        
    except Exception as e:
        error_msg = f"Failed to process website content: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg
 

@app.route('/scrapper', methods=["GET", "POST"])
@limiter.limit("10 per minute") 
# @sleep_and_retry
# @lru_cache(maxsize=256) #lru local cache on top of redis caching
def scrape_address() -> Response:
    url = request.args.get("url")
    if not url:
        return generate_response({"error": "URL is empty"}, 400)
    cache_key = get_cache_key(url)
    cached_data = get_cache(cache_key)
    if cached_data:
        logger.info("cache hit")
        print("cache hit")
        return generate_response(cached_data, 200)
    scraped, prompt, err = scrape(url)
    if err != None:
        return generate_response({"error": err}, 400)
    address, err = generate_address_from_model(scraped, prompt)
    if err != None:
        return generate_response({"error": err}, 400)
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

def validate_url(url):
    """
    Validate and sanitize URL for security.
    
    Args:
        url: The URL to validate
        
    Returns:
        Tuple[Optional[ParseResult], Optional[str]]: (parsed_url, error_message)
        Returns (parsed_url, None) if valid, or (None, error_message) if invalid
    """
    # Basic URL validation
    if not url or not isinstance(url, str):
        return None, "URL must be a non-empty string"
    
    # Limit URL length to prevent DoS
    if len(url) > MAX_URL_LENGTH:
        return None, "URL too long (max 2048 characters)"
    
    # Parse and validate URL structure
    parsed = urlparse(url)
    if not all([parsed.scheme, parsed.netloc, parsed.hostname]):
        return None, "Invalid URL format"
    
    # Only allow HTTP(S) protocols
    if parsed.scheme not in ('http', 'https'):
        return None, "Only HTTP and HTTPS protocols are supported"
    
    # Domain blacklist check
    if parsed.hostname in BLACKLISTED_DOMAINS:
        return None, "Access to this address is not allowed"
    
    # Check for suspicious patterns in hostname
    if re.search(r'[\x00-\x1f\x7f-\x9f]', parsed.hostname):
        return None, "Invalid characters in hostname"
    
    # Prevent URL encoding attacks
    if quote(url, safe="-._~:/?#[]@!$&'()*+,;=%") != url:
        return None, "URL contains invalid characters"
    
    # SSRF Protection: Resolve hostname and check IP
    try:
        # Get all IP addresses for the hostname
        ip_addresses = socket.getaddrinfo(parsed.hostname, None) #todo add all ip addresses
        
        for addr_info in ip_addresses:
            ip_str = addr_info[4][0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)
                
                # Additional checks for special addresses
                if ip_obj.is_private or ip_obj.is_reserved or ip_obj.is_loopback or ip_obj.is_link_local:
                    return None, "Access to special IP addresses is not allowed"
                    
            except ValueError:
                continue
                
    except (socket.gaierror, socket.error) as e:
        # Log but continue - hostname might be valid but temporarily unresolvable
        logger.warning(f"DNS resolution failed for {parsed.hostname}: {e}")
        print(f"DNS resolution failed for {parsed.hostname}: {e}")
        return None, "DNS resolution failed, try again"
    
    return parsed, None

def scrape(url):
    '''
    adaptive scraping based on domain with security measures
    '''
    # Validate URL
    parsed, error = validate_url(url)
    if error:
        return "", "", error
    
    print("requested url", url)
    logger.info(f"requested url = {url}")
    res, prompt, err = None, WEBSITE_PROMPT, None
    # fetch from tiktok
    if parsed.netloc in ("vt.tiktok.com", "www.tiktok.com"):
        try:
            response = requests.head(url, allow_redirects=True)
            url = response.url
        except Exception as e:
            err = f"cannot fetch ultimate url of tiktok post, err: {e}"
            logger.error(err, exc_info=True)
            print(err)
            return "", "", err
        media_type = check_tiktok_type(url)
        if media_type == 'photo':
            res, err = handle_tiktok_photo(url)
            prompt=TIKTOK_PROMPT_IMAGE
        elif media_type =='video':
            res, err = handle_tiktok_video(url)
            if len(res)>6 and res[:5] == "audio":
                prompt=TIKTOK_PROMPT_AUDIO_CAPTION
            else:
                prompt=TIKTOK_PROMPT_CAPTION
        else:
            err = "tiktok post type cannot be identified"
    # fetch from rednote
    elif parsed.netloc == "www.xiaohongshu.com":
         res, err = handle_rednote_photo(url)
    # fetch from lemon8
    elif parsed.netloc == "www.lemon8-app.com": #todo: switch to lemon8 handler
        res, err = handle_website(url, headers=None) #weird quirk
    # fetch from instagram or facebook
    elif parsed.netloc == "www.instagram.com" or parsed.netloc == "www.facebook.com":
        err = "instagram and facebook links are not supported" 
    # fetch from website
    else:
        res, err = handle_website(url)
    if err:
        logger.error(err, exc_info=True)
        print(f"failed to fetch from {url}, err={err}")
        return "", "", f"failed to fetch from {url}, err={err}"
    logger.info(f"text identified = {res}")
    print("text identified =", res)
    return res, prompt, None

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

def generate_address_from_model(text: str, prompt: str) -> Dict[str, List[str]]:
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
            { "role": "system", "content": prompt },
            {"role": "developer", "content": text}
        ]
    )
    resp = completion.choices[0].message.content
    if not isinstance(resp, str):
        logger.error(f"response not string: {resp}")
        return  None, f"response not string: {resp}"
    resp = resp.replace('```', '').replace('\n', '') #todo: find a fix
    print("resp", resp)
    if resp[:4] == 'json':
        resp = resp[4:]
    try:
        address = json.loads(resp)
    except Exception as error:
        logger.error(f"failed to extract {resp}, err = {error}")
        return None, f"failed to extract {resp}, err = invalid json"
    return address, None

def validate_place_info(place_info: Optional[PlaceInfo], name: str) -> bool:
    if not place_info:
        return False
    # if place_info.Name not in name: #todo: come up with validation using more examples
    #     return False
    return True

def generate_markers(addressStruct: Dict[str, List[str]], mode: int = 2) -> List[PlaceInfo]:
    '''
    takes address map and queries, for each address, its location information as defined by PlaceInfo
    '''
    address_info = []
    address_check = True
    for name, addresses_struct in addressStruct.items():
        address_check &= ('address' in addresses_struct) # if some locations dont have addresses, treat all as noise
    for name, addresses_struct in addressStruct.items():
        addresses = []
        location = name
        if 'address' in addresses_struct:
            addresses = addresses_struct['address']
        if len(addresses) > 0 and address_check:
            location += (' ' + addresses[0])
        if 'area' in addresses_struct and addresses_struct['area'] != '':
            location += (' ' + addresses_struct['area'])
        info, err = map_info(location, mode)
        if err != None or not validate_place_info(info, name):
            continue
        if 'description' in addresses_struct:
            info.Description = addresses_struct['description']
        address_info.append(info)
    return address_info

@app.route('/single_address', methods=["GET", "POST"])
def generate_single_address() -> Response:
    address = request.args.get('address')
    print("address", address)
    if not address:
        return jsonify({"error": "address is required"}), 400
    res, err = map_info(address)
    print("res", res)
    response = jsonify(res)
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.status_code = 200 if err == None else 400
    return response

def map_info(address: str, mode: int = 2) -> Tuple[Optional[PlaceInfo], Optional[Dict]]:
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
        err = f"google info fetch failed, param={detail_params}, err = {error}"
        logger.error(err)
        print(err)
        return {"error": err}, err
    detail_data = detail_response.json().get("places", "")
    if not detail_response.ok or not detail_data:
        err = f"google info fetch failed, param={detail_params}, err = {detail_response.text}"
        print(err)
        logger.error(err)
        return {"error": err}, err
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
        DirectionLink=detail.get("googleMapsLinks",  {}).get("directionsUri", None),
        Description=''
    ), None

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

if __name__ == "__main__": #for debugging
    app.run()