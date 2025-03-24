import os
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

OPENAI_TOKEN = os.environ.get('OPENAI_TOKEN')
GOOGLE_TOKEN = os.getenv("GOOGLE_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
AUMI_URL = os.getenv("AUMI_URL")

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

PlaceSearchDomainNew = "https://places.googleapis.com/v1/places:searchText"
PlaceSearchFieldsNew_Free = ["places.id"] #0
PlaceSearchFieldsNew_Basic = ["places.formattedAddress","places.businessStatus","places.location","places.googleMapsUri",
                              "places.utcOffsetMinutes","places.displayName","places.googleMapsLinks"] #places.photos #0.032
PlaceSearchFieldsNew_Premium = ["places.priceLevel","places.rating","places.websiteUri","places.currentOpeningHours",
                                "places.userRatingCount"]  #0.035
PlaceSearchField_LEGACY = ["business_status","formatted_address","geometry", "name","photos","place_id","plus_code","permanently_closed","types"]