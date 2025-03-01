from flask import request
from server import app, OpenAIToken, GoogleToken
from bs4 import BeautifulSoup
from openai import OpenAI
import requests
from functools import lru_cache
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from ratelimit import limits, sleep_and_retry
import googlemaps
from bot import *
from consts import *

logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)
logger = logging.getLogger(__name__)

try:
    gmaps = googlemaps.Client(key=GoogleToken)
except Exception as error:
    logger.error(f"failed to initialize google maps, err = {error}")
    raise

PremiumUser = True

@app.route('/')
def hewwo():
    return "hewwwoo"

@app.route('/google_token', methods=["GET"])
def get_google_token():
    return GoogleToken

@app.route('/openai_token', methods=["GET"])
def get_openai_token():
    return OpenAIToken

@dataclass
class PlaceInfo:
    Id: str
    Name: str
    Address: str
    Lat: float
    Long: float
    Status: str
    Rating: Optional[float]
    RatingCount: Optional[int]
    PriceLevel: Optional[str]
    OpeningHours: Optional[Dict]
    Website: Optional[str]
    GoogleLink: Optional[str]
    DirectionLink: Optional[str]

@app.route('/scrapper', methods=["GET"])
@sleep_and_retry
@limits(calls=1, period=60) #todo - supposedly doesnt work quite well, but im not expecting massive traffic so... DEFERRED
@lru_cache(maxsize=256)
def scrape_address() -> ApiResponse:
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
        return ApiResponse(response.status_code, "failed to retrieve page", {})
    soup = BeautifulSoup(response.text, 'html.parser')
    response.close()
    text = "\n".join([text.strip() for text in soup.stripped_strings])
    address = generate_address(text)
    logger.info("generated information = {address}")
    return ApiResponse(200, "success", address)

def generate_address(text: str) -> Dict[str, List[str]]:
    '''
    model parses html text and returns json containing address information
    '''
    client = OpenAI(
        api_key = ""#OpenAIToken
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
    resp = resp.replace('```', '').replace('\n', '') #todo: find a prompt that tells it NOT to do this
    if resp[:4] == 'json':
        resp = resp[4:]
    try:
        address = eval(resp)
    except Exception as error:
        logger.error(f"failed to extract {resp}, err = {error}")
        raise
    return address

def map_info(address: str) -> Optional[PlaceInfo]:
    fields = ','.join(PlaceSearchFieldsNew_Free + PlaceSearchFieldsNew_Basic + (PlaceSearchFieldsNew_Premium if PremiumUser else []))
    detail_params = {
        "textQuery": address
    }
    detail_headers = {
        "X-Goog-Api-Key": "",#GoogleToken,
        "X-Goog-FieldMask":fields 
    }
    try:
        detail_response = requests.get(
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
    

def generate_markers(addressStruct: Dict[str, List[str]]) -> List[PlaceInfo]:
    '''
    takes address map and queries, for each address, its location information as defined by PlaceInfo
    '''
    address_info = []
    for name, addresses in addressStruct:
        for address in addresses:
            info = map_info(name + " " + address)
            if not info:
                continue
            address_info.append(info)
    return address_info

if __name__ == "__main__":
    bot = setup_telegram_bot()
    logger.info("Telegram bot starting...")
    logger.info("Mini app starting...")
    app.run(debug=True)