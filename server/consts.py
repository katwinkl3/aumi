
PlaceSearchDomainNew = "https://places.googleapis.com/v1/places:searchText"
PlaceSearchFieldsNew_Free = ["places.id"] #0
PlaceSearchFieldsNew_Basic = ["places.formattedAddress","places.businessStatus","places.location","places.googleMapsUri",
                              "places.utcOffsetMinutes","places.displayName","places.googleMapsLinks"] #places.photos #0.032
PlaceSearchFieldsNew_Premium = ["places.priceLevel","places.rating","places.websiteUri","places.currentOpeningHours",
                                "places.userRatingCount"]  #0.035
PlaceSearchField_LEGACY = ["business_status","formatted_address","geometry", "name","photos","place_id","plus_code","permanently_closed","types"]