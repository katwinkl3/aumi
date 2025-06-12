import os
import ipaddress
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

OPENAI_TOKEN = os.getenv('OPENAI_TOKEN')
GOOGLE_TOKEN = os.getenv("GOOGLE_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
AUMI_URL = os.getenv("AUMI_URL")
TIKTOK_PHOTO_URL = os.getenv("TIKTOK_PHOTO_URL")
TIKTOK_PHOTO_ORIGIN_URL = os.getenv("TIKTOK_PHOTO_ORIGIN_URL")
TIKTOK_PHOTO_REFERER_URL = os.getenv("TIKTOK_PHOTO_REFERER_URL")
TIKTOK_VIDEO_URL = os.getenv("TIKTOK_VIDEO_URL")
TIKTOK_VIDEO_ORIGIN_URL = os.getenv("TIKTOK_VIDEO_ORIGIN_URL")
TIKTOK_VIDEO_REFERER_URL = os.getenv("TIKTOK_VIDEO_ORIGIN_URL")
TIKTOK_VIDEO_HOST = os.getenv("TIKTOK_VIDEO_HOST")
TIKTOK_VIDEO_API = os.getenv("TIKTOK_VIDEO_API")

WEBSITE_PROMPT = "The following text is scraped from a website recommending one or more locations. The first line is the title of the article which might contain the country/district these locations belong to, the number of locations listed (if > 1) and the type of locations mentioned (e.g cafes, shops, tourist attraction etc). If multiple locations are recommended, the article might be divided into sections, each starting with the location name, and may be followed by a description of the location, including information like address, price etc. The article might also present a numbered list of location names with minimal to no description. Your tasks are: 1. Use your best discretion to discern which locations are being recommended, then for each, extract their names, list of addresses, and the description of this location. 2. Infer the country/state/district each location is in. The locations could be in the same area, which might be mentioned in the title (e.g. New york, Tiong Bahru), or in different areas, which might be mentioned in the description of that location. 3. Return only a json map object with the structure {name+:{'address':[...(if found else empty arr)],'description': ...(if found else empty str), 'area':infered location (if found else empty str)}"
TIKTOK_PROMPT_AUDIO_CAPTION="The following is the audio transcript and video caption of a tiktok recommending one or more locations. The first part of the audio likely provides context, like the country/district these locations belong to, number of locations (if > 1), type of locations mentioned (e.g cafes, shops, tourist attraction etc). The rest of the audio contain description of the mentioned location(s). The caption might provide background context or specific details of the locations like names (usually in a numbered list, or appears beside a pin emoji like 📍). Your tasks are: 1. Use your best discretion to discern which locations are being recommended, but prioritise the following rules: a.If locations are found in the caption, use only those locations names, and glean their descriptions from relevant audio/caption text. b.In the case where multiple locations are found in the audio but there is only one location in the caption, the multiple locations are part of the caption location, and should be used as description of that one location, and not as independent locations. For each found location, extract their names, list of addresses, and description of this location. 2. Infer the country/state/district each location is in based on audio/description context. 3. Return only a json map object with the structure {name+:{'address':[...(if found else empty arr)],'description': ...(if found else empty str), 'area':infered location (if inferable else empty str)}"
TIKTOK_PROMPT_CAPTION="The following is the video caption of a tiktok recommending one or more locations. The caption might provide background context or specific details of the locations like names (usually in a numbered list, or appears beside a pin emoji like 📍). Your tasks are: 1. Use your best discretion to discern which locations are being recommended, then for each, extract their names, and the description of this location. If no locations are found, leave empty. 2. Infer the country/state/district each location is in. 3. Return only a json map object with the structure {name+:{'address':[...(if found else empty arr)],'description': ...(if found else empty str), 'area':infered location (if inferable else empty str)}"
TIKTOK_PROMPT_IMAGE="The following is the post caption, and text parsed with ocr from a tiktok slideshow post recommending one or more locations. For the parsed text, each line is from one image. The first line likely provides context like the country/district these locations belong to, number of locations (if > 1), type of locations mentioned (e.g cafes, shops, tourist attraction etc). Each subsequent line might contain a location name and its description, if recommending multiple locations, or a new description about the same location, if only recommending one. The caption might provide background context or specific details of the locations like names (usually in a numbered list, or appears beside a pin emoji like 📍). Your tasks are: 1. Use your best discretion to discern which locations are being recommended. The texts will likely contain background image noise so some hanging characters shouldnt be included. 2. Infer the country/state/district each location is in based on audio/description context. 3. Return only a json map object with the structure {name+:{'address':[...(if found else empty arr)],'description': ...(if found else empty str), 'area':infered location (if inferable else empty str)}"

timeout = 10
redis_expiry = 60*60*24

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
    Description: Optional[str]

PlaceSearchDomainNew = "https://places.googleapis.com/v1/places:searchText"
PlaceSearchFieldsNew_Free = ["places.id"] #0
PlaceSearchFieldsNew_Basic = ["places.formattedAddress","places.businessStatus","places.location","places.googleMapsUri",
                              "places.utcOffsetMinutes","places.displayName","places.googleMapsLinks"] #places.photos #0.032
PlaceSearchFieldsNew_Premium = ["places.priceLevel","places.rating","places.websiteUri","places.currentOpeningHours",
                                "places.userRatingCount"]  #0.035
PlaceSearchField_LEGACY = ["business_status","formatted_address","geometry", "name","photos","place_id","plus_code","permanently_closed","types"]

# Security configurations
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max response size
MAX_URL_LENGTH = 2048
ALLOWED_CONTENT_TYPES = ['text/html', 'application/json', 'text/plain']
ALLOWED_IMG_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
BLACKLISTED_DOMAINS = [
    'metadata.google.internal',
    '169.254.169.254',  # AWS metadata endpoint
    '100.100.100.200' # alicloud
    'ecs.aliyun.com'  # ali ecs
]