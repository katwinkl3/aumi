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
    return [PlaceInfo(Id='ChIJgU3MUqAX2jER8ytjKoY12Tw', Name='Acoustics Coffee Bar Neil', Address='61 Neil Rd, Singapore 088895', Lat=1.2795196, Long=103.8423325, Status='OPERATIONAL', Rating=None, RatingCount=None, PriceLevel=None, OpeningHours=None, Website=None, GoogleLink='https://maps.google.com/?cid=4384594562574920691', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da17a052cc4d81:0x3cd935862a632bf3!3e0"),
 PlaceInfo(Id='ChIJpSnNNXgZ2jERuw0tzcjzThA', Name='Acoustics Coffee Bar Owen', Address='2 Owen Rd, #01-02, Singapore 218842', Lat=1.3117237, Long=103.85499349999999, Status='OPERATIONAL', Rating=None, RatingCount=None, PriceLevel=None, OpeningHours=None, Website=None, GoogleLink='https://maps.google.com/?cid=1175144596551568827', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da197835cd29a5:0x104ef3c8cd2d0dbb!3e0"),
 PlaceInfo(Id='ChIJ6fBlRHsZ2jERuDtMge1ovMQ', Name='Alice Boulangerie & Restaurant', Address='12 Gopeng St, #01-05/11 Icon Village, Singapore 078877', Lat=1.2752371, Long=103.8444719, Status='OPERATIONAL', Rating=None, RatingCount=None, PriceLevel=None, OpeningHours=None, Website=None, GoogleLink='https://maps.google.com/?cid=14176321096341273528', DirectionLink="https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da197b4465f0e9:0xc4bc68ed814c3bb8!3e0")]

@app.route('/scrapper', methods=["GET", "POST"])
@sleep_and_retry
@limits(calls=1, period=60) #todo - supposedly doesnt work quite well, but im not expecting massive traffic so... DEFERRED
@lru_cache(maxsize=256)
def scrape_address() -> Response:
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
    result = generate_markers(address)
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
