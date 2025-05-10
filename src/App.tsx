import React, { useEffect, useState, useCallback } from 'react'
import './App.css'
import WebApp from '@twa-dev/sdk'
import {APIProvider, Map, AdvancedMarker, Pin, MapCameraChangedEvent, MapEvent} from '@vis.gl/react-google-maps';
import {Drawer, RatingGroup, CloseButton, VStack, Box, Text, Flex, Button, HStack, Icon, Accordion, ChakraProvider,
   defaultSystem, Spinner, Center, SegmentGroup, Editable, IconButton, Span, Blockquote} from '@chakra-ui/react'
import { toaster, Toaster } from './components/ui/toaster';
import { Polyline } from './components/ui/polyline';
import { FiNavigation, FiGlobe, FiMapPin, FiClock, FiCheck, FiArrowLeft } from 'react-icons/fi';
import { FaMapMarkedAlt } from 'react-icons/fa';
// import {decode} from '@googlemaps/polyline-codec';

// Mapbox
// import Map, { Marker, Popup } from 'react-map-gl';
// import 'mapbox-gl/dist/mapbox-gl.css';

// todo get toaster to work

WebApp.ready();

interface PlaceInfo {
  Id: string;
  Name: string;
  Address: string;
  Lat: number;
  Long: number;
  Status: string;
  Rating: number | null;
  RatingCount: number | null;
  PriceLevel: string | null;
  OpeningHours: Record<string, any> | null;
  Website: string | null;
  GoogleLink: string | null;
  DirectionLink: string | null;
  Description: string | null;
}

interface DirectionInfo {
  idx: number;
  duration: string;
  walkingDuration: string;
  distance: string;
  walkingDistance: string;
  polyline: string;
  mode: string;
}

interface ScrapperErrorResponse {
  error: string; // Error message from Flask
}


function App() {
  const [loading, setLoading] = useState(true);
  const [firstName, setFirstName] = useState<string | null>(null);
  const [url, setUrl] = useState<string>("");
  const [teleUrl, setTeleUrl] = useState<string>("");
  const [gToken, setGtoken] = useState<string | null>(null);
  const [places, setPlaces] = useState<PlaceInfo[]>([]);
  const [activeMarker, setActiveMarker] = useState<number | null>(null);
  const [newCenter, setNewCenter] = useState<google.maps.LatLngLiteral>();
  const [newZoom, setNewZoom] = useState<number>();
  const [userLocation, setUserLocation] = useState<google.maps.LatLngLiteral>();
  const [transportMode, setTransportMode] = useState<"TRANSIT" | "DRIVE">("TRANSIT");
  const [directionData, setDirectionData] = useState<DirectionInfo | null>(null);
  const [showInfo, setShowInfo] = useState(false);
  const [lastFetchTime, setLastFetchTime] = useState<number>(0);
  // const [newBounds, setNewBounds] = useState<google.maps.LatLngBoundsLiteral>();
  // const [userData, setUserData]=useState<UserData | null>(null);
  // const [travelData, setTravelData] = useState<Record<string, any>>({});

  const Domain = "https://caa0-2406-3003-2005-5c1e-34bd-3b9d-7747-1f10.ngrok-free.app"//"http://127.0.0.1:5000"
  const ScrapperPath = "/scrapper"
  const DirectionAPI = "https://routes.googleapis.com/directions/v2:computeRoutes"
  const AddressPath = "/single_address"

  // fetch google token if null
  useEffect(() => {
    if (gToken != null) return; 
    setLoading(true);
    try{
      fetch(Domain+"/google_token", {
        headers: {
        'ngrok-skip-browser-warning':'skip',
      }})
      .then((res) => res.json())
      .then((text) => setGtoken(text.token || ""));
    } catch (err) {
      console.error('Error fetching Google Maps API key:', err);
      toaster.create({
        title: '500',
        description: 'Failed to load Google Maps API key, err: ' + err,
        type: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  }, []);

  // fetch telegram information (user info, location, url)
  useEffect(() => {
    setLoading(true);
    const urlParams = new URLSearchParams(window.location.search);
    const messageParam = urlParams.get('message');
    if (messageParam) {
      setTeleUrl(decodeURIComponent(messageParam).trim());
    }
    try{
      // console.log("WebApp.initDataUnsafe", WebApp.initDataUnsafe);
      // console.log("WebApp.initDataUnsafe.user", WebApp.initDataUnsafe.user);
      setFirstName(WebApp.initDataUnsafe.user?.first_name || null);
      // console.log("WebApp.initDataUnsafe.start_param", WebApp.initDataUnsafe.start_param);
      // setUrl(WebApp.initDataUnsafe.start_param || "");
    } catch (err) {
      console.error('Error fetching user data:', err);
      toaster.create({
        title: '500',
        description: 'Failed to load user data. Err= '+ err,
        type: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  }, []);

  // Triggers fetching of place info when url is updated
  useEffect(() => {
    if (!teleUrl) return;
    setLoading(true);
    const loadPlaces = async () => {
      try {
        await fetchInfo();
      } catch (err) {
        console.error('Error fetching user data:', err);
        toaster.create({
          title: '500',
          description: 'Failed to load locations. Err= '+ err,
          type: 'error',
          duration: 5000,
        });
      } finally {
        setLoading(false);
      }
    }
    loadPlaces();
  }, [teleUrl]);

  const isMobile = Math.min(window.screen.width, window.screen.height) < 768 || navigator.userAgent.indexOf("Mobile") > -1;

  // Helper functions for GMap initialization

  // Calculate initial zoom based on location lat long
  const calculateZoom = (locations: PlaceInfo[]) => { //todo check if this is correct
    if (!locations || locations.length === 0) {
      return 12;
    }
    const bounds = initializeBounds(locations);
    const latSpan = bounds.north - bounds.south;
    const lngSpan = bounds.east - bounds.west;
    const maxSpan = Math.max(latSpan, lngSpan);
    let zoomLevel = Math.floor(Math.log2(360 / maxSpan));
    console.log("zoomLevel", zoomLevel);
    return Math.min(Math.max(zoomLevel, 1), 20);
  }

  // Get average of all locations and set for initial view
  const initializeCenter = (locations: PlaceInfo[]) => { //todo - when adding new location, calculate include new location
    if (locations.length === 0) return { lat: 0, lng: 0 };
    const sum = locations.reduce(
      (acc, loc) => ({
        lat: acc.lat + loc.Lat,
        lng: acc.lng + loc.Long
      }),
      { lat: 0, lng: 0 }
    );
    return {
      lat: sum.lat / locations.length,
      lng: sum.lng / locations.length
    };
  }

  // Get bounds of all locations
  const initializeBounds = (locations: PlaceInfo[]) => {
    if (!locations || locations.length === 0) {
      // Return default bounds (world view)
      return {
        north: 85,
        south: -85,
        east: 180,
        west: -180
      };
    }
    var north = -85, south = 85, east = -180, west = 180;
    locations.forEach(loc => {
      north = Math.max(north, loc.Lat);
      south = Math.min(south, loc.Lat);
      east = Math.max(east, loc.Long);
      west = Math.min(west, loc.Long);
    });
    console.log("north", north, "south", south, "east", east, "west", west);
    return { north: north, south: south,east: east, west: west};
  }

  // Mapbox UI component for map
  // const MapboxLocationMap = ({ locations }: { locations: PlaceInfo[]}) =>{
  //   return (
  //     <Map
  //     mapboxAccessToken="YOUR_MAPBOX_TOKEN"
  //     initialViewState={{
  //       latitude: 51.505,
  //       longitude: -0.09,
  //       zoom: 13
  //     }}
  //     style={{ width: '100%', height: 400 }}
  //     mapStyle="mapbox://styles/mapbox/streets-v11"
  //   >
  //     {locations.map(location => (
  //       <Marker
  //         key={location.id}
  //         latitude={location.lat}
  //         longitude={location.lng}
  //         onClick={() => setSelectedMarker(location)}
  //       >
  //         <div style={{ color: 'red', cursor: 'pointer' }}>📍</div>
  //       </Marker>
  //     ))}

  //     {activeMarker && (
  //       <Popup
  //         latitude={activeMarker.lat}
  //         longitude={activeMarker.lng}
  //         onClose={() => setActiveMarker(null)}
  //       >
  //         <div>{activeMarker.name}</div>
  //       </Popup>
  //     )}
  //   </Map>
  //   )
  // }

const getUserLocation = async (): Promise<void> => {
  if (userLocation) { //todo assume fresh
    return;
  }
  // 1. get from telegram
  // if (WebApp?.initDataUnsafe?.user?.id) {
  //   try {
  //     const location = await new Promise((resolve, reject) => {
  //       WebApp.requestLocation(resolve, reject);
  //     });
  //     setUserLocation({
  //       lat: location.latitude,
  //       lng: location.longitude,
  //       id: 'user'
  //     });
  //     return;
  //   } catch (telegramError) {
  //     console.error('Telegram location failed:', telegramError);
  //   }
  // }
  // 2. get from browser
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const userLocation = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        setUserLocation(userLocation);
        return;
      },
      (error) => {
        console.error("Error getting user location from browser:", error.message);
      },
      // {
      //   enableHighAccuracy: true,  // Request high accuracy (uses more battery)
      //   timeout: 5000,             // Time to wait for a position
      //   maximumAge: 0              // Don't use a cached position
      // }
    );
  }
  // 3. get from ipapi
  try {
    const response = await fetch('https://ipapi.co/json/');
    const data = await response.json();
    console.log("location: ",data);
    if (data.latitude && data.longitude) {
      setUserLocation({
        lat: parseFloat(data.latitude),
        lng: parseFloat(data.longitude),
      });
      return;
    }
  } catch (ipError) {
    console.error('IP-based location failed:', ipError);
  }
  toaster.create({
    title: '400',
    description: 'User location cannot be found. Please try again.',
    type: 'error',
    duration: 5000,
  });
}

const editUserLocation = async (location: string) => {
  console.log("editUserLocation", location);
  
  const resp = await fetch(Domain+AddressPath+`?address=${encodeURIComponent(location)}`, {
    headers: { //todo: remove headers
    'ngrok-skip-browser-warning': 'skip',
  }});
  const data = await resp.json();
  console.log("data: ", data);
  // check if data is valid
  if (data.Lat && data.Long) {
    setUserLocation({
      lat: data.Lat,
      lng: data.Long,
    });
    setActiveMarker(null);
    setShowInfo(false);
    setDirectionData(null);
  } else {
    toaster.create({
      title: '400',
      description: 'Invalid location',
      type: 'error',
      duration: 5000,
    });
  }
}

const deleteLocation = (index: number) => {
  console.log("deleteLocation", index);
  // setPlaces(places.filter((_, i) => i !== index));
  // setNewCenter(initializeCenter(places));
  // setNewZoom(calculateZoom(places));
}

const editLocation = (index: number) => {
  console.log("editLocation", index);
}

// convert number of seconds to hours minutes and seconds string
const formatTime = (seconds: number) => {
  const hours = Math.floor(seconds / 3600); 
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;
  return `${hours > 0 ? hours + "h " : ""}${minutes > 0 ? minutes + "m " : ""}${remainingSeconds > 0 ? remainingSeconds + "s" : ""}`;
}

// convert number of meters to kilometers string
const formatDistance = (meters: number) => {
  if (meters < 1000) {
    return `${meters}m`;
  }
  return `${meters / 1000}km`;
}

// fetch travel time from google maps api
const fetchTravelTime = async (idx: number) => {
  getUserLocation();
  setActiveMarker(idx);
  setShowInfo(true);
  setDirectionData(null);
  if (userLocation == null) {
    console.error("no user location");
    return;
  }
  if (gToken == null) {
    console.error("Google Maps API key not found");
    return;
  }
  // const key = `(${userLocation?.lat},${userLocation?.lng}),(${places[idx].Lat},${places[idx].Long}),${transportMode}`; //if using lat long over place id
  const key = `(${userLocation?.lat},${userLocation?.lng})_${places[idx].Id}_${transportMode}`;
  const cachedVal = localStorage.getItem(key);
  if (cachedVal) {
    console.log("found in cache", cachedVal);
    setDirectionData(JSON.parse(cachedVal));
    return;
  }
  const resp = await fetch(DirectionAPI, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      "X-Goog-FieldMask": "routes.legs",
      'X-Goog-Api-Key': gToken ?? ""
    },
    body: JSON.stringify({
      origin: {
        "location": {
          "latLng":{
            "latitude": userLocation?.lat,
            "longitude": userLocation?.lng
          }
        }
      },
      destination: {
        "placeId": places[idx].Id
      },
      travelMode: transportMode,
      units: "METRIC"
    })
  });
  const data = await resp.json();
  console.log("data: ", data);
  if ((!resp.ok || !data || !data['routes'])){
    toaster.create({
      title: 'Directions could not be fetched from google maps',
      description: data.error, //todo: block from user
      type: 'error',
      duration: 5000,
    });
    console.log("error: ", data.error);
    return;
  }
  try{
    const legs = data['routes'][0]['legs'][0];
    const duration = Number(legs['duration'].slice(0, -1));
    const distance = Number(legs['distanceMeters']);
    let walkingDuration = 0;
    let walkingDistance = 0;
    for (const step of legs['steps']) {
      if (step['travelMode'] == 'WALK') {
        walkingDuration += Number(step['staticDuration'].slice(0, -1));
        walkingDistance += Number(step['distanceMeters']);
      }
    }
    const polyline = legs['polyline']['encodedPolyline'];
    // const decodedPath = decode(polyline);
    console.log("duration: ", duration, "distance: ", distance, "walkingDuration: ", walkingDuration, "walkingDistance: ", walkingDistance);
    localStorage.setItem(key, JSON.stringify({
      idx: idx,
      duration: formatTime(duration),
      walkingDuration: formatTime(walkingDuration),
      distance: formatDistance(distance),
      walkingDistance: formatDistance(walkingDistance),
      polyline: polyline,
      mode: transportMode,
    }));
    setDirectionData({
      idx: idx,
      duration: formatTime(duration),
      walkingDuration: formatTime(walkingDuration),
      distance: formatDistance(distance),
      walkingDistance: formatDistance(walkingDistance),
      polyline: polyline,
      mode: transportMode,
    });
  } catch (error) {
    console.log("error: ", error);
    toaster.create({
      title: 'Location could not be processed',
      description: error, //todo: block from user
      type: 'error',
      duration: 5000,
    });
  }
}
  // fetchAddress sends url to /scrapper to fetch addresses
  const fetchInfo = async () => {
    // Rate limiting logic
    const now = Date.now();
    const cooldownPeriod = 3 * 1000; // 10 seconds in milliseconds
    const urlParam = teleUrl || url.trim();
    
    // Check cooldown period
    if (now - lastFetchTime < cooldownPeriod) {
      toaster.create({
        title: 'Request too frequent',
        description: `Please wait before retrying`,
        type: 'warning',
        duration: 5000,
      });
      return;
    }
    
    // Update rate limit tracking
    setLastFetchTime(now);
    setLoading(true);
    if (!isValidHttpUrl(urlParam)){
      console.log("Invalid URL", urlParam);
      toaster.create({
        title: '400',
        description: 'Not a valid url.',
        type: 'error',
        duration: 5000,
      });
      setLoading(false);
      return;
    }
    var matches = urlParam.match(/^https?\:\/\/([^\/?#]+)(?:[\/?#]|$)/i);
    // todo: invalid url match no notification
    var domain = matches && matches[1];
    switch (domain) {
      case "youtu.be":
        toaster.create({
          title: 'Invalid URL', description: "cant handle youtube videos yet", type: 'warning', duration: 5000,
        });
        setLoading(false);
        return
      case "www.instagram.com":
        toaster.create({
          title: 'Invalid URL', description: "cant handle instagram videos yet", type: 'warning', duration: 5000,
        });
        setLoading(false);
        return
      default:
    }
    try {
      const resp = await fetch(Domain+ScrapperPath+`?url=${encodeURIComponent(urlParam)}`, {
        headers: { //todo: remove headers
        'ngrok-skip-browser-warning': 'skip',
      }});
      if (resp.status === 429) {
        toaster.create({
          title: 'Rate Limit Exceeded', description: "Please try again later", type: 'error', duration: 5000,
        });
        setLoading(false);
        return;
      }
      if (!resp.ok) {
        const errorData: ScrapperErrorResponse = await resp.json();
        toaster.create({
          title: '500', description: errorData.error, type: 'error', duration: 5000,
        });
        setLoading(false);
        return;
      }
      const data = await resp.json();
      if (!Array.isArray(data)){
        toaster.create({
          title: '500', description: "empty response", type: 'error', duration: 5000,
        });
        setPlaces([]);
        return;
      }
      setPlaces(data);
      setNewCenter(initializeCenter(data));
      // setNewBounds(initializeBounds(data));
      setNewZoom(calculateZoom(data));
    } catch (error) {
      console.log("error: ", error);
      toaster.create({
        title: '500', description: "unknown error", type: 'error', duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  }
  
  const fetchInfoEnter = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.nativeEvent.key == "Enter") {
      fetchInfo()
    }
  };

  const isValidHttpUrl = (str: string): boolean => {
    const pattern = new RegExp(
      '^(https?:\\/\\/)?' + // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|' + // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))' + // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+@]*)*' + // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?' + // query string
        '(\\#[-a-z\\d_]*)?$', // fragment locator
      'i'
    );
    return pattern.test(str);
  }

   // UI component for map
   const LocationMap = ({ locations }: { locations: PlaceInfo[]}) => { //todo - switch to mapbox
    if (locations.length == 0 || gToken == null) {
      toaster.create({
        title: '500',
        description: 'Failed to load map display. Please try again.',
        type: 'error',
        duration: 5000,
      });
      return
    }

    // Update state when the map is moved
    // const onCenterChanged = useCallback((e: MapCameraChangedEvent) => {
    //   setNewCenter(e.detail.center);
    //   console.log("center", e.detail.center);
    // }, []);

    // Update state when the zoom is changed
    const onZoomChanged = useCallback((e: MapCameraChangedEvent) => {
      setNewZoom(e.detail.zoom);
      console.log("zoom", e.detail.zoom);
    }, []);

    const onDragEnd = useCallback((e: MapEvent) => {
      // console.log("drag end: center", e.map.getCenter(), "zoom", e.map.getZoom(), "bounds", e.map.getBounds());
      if (e.map.getCenter() != null) {
        console.log("drag end: center", e.map.getCenter()?.toJSON());
        setNewCenter(e.map.getCenter()?.toJSON());
      }
      // if (e.map.getZoom() != null) {
      //   console.log("drag end: zoom", e.map.getZoom());
      //   setNewZoom(e.map.getZoom() ?? 12);
      // }
      // if (e.map.getBounds() != null) {
      //   console.log("drag end: bounds", e.map.getBounds()?.toJSON());
      //   setNewBounds(e.map.getBounds()?.toJSON());
      // }
      // if (e.map.getZoom() != null) {
      //   console.log("drag end: zoom", e.map.getZoom());
      //   setNewZoom(e.map.getZoom() ?? newZoom);
      // }
    }, []);

    // if (directionData?.polyline) {
    //   const decodedPath = decode(directionData?.polyline ?? "");
    //   // console.log("decodedPath", decodedPath);
    //   const map = useMap();
    //   const maps = useMapsLibrary("maps");
    //   console.log("map", map);
    //   console.log("maps", maps);
    //   if (maps) {
    //     const path = new maps.Polyline({
    //       path: decodedPath.map(([lat, lng]) => ({ lat, lng })),
    //       geodesic: true,
    //       strokeColor: "#FF0000",
    //       strokeOpacity: 1.0,
    //       strokeWeight: 2,
    //     });
    //     path.setMap(map);
    //   }
    // }

    // const editable = useEditable({
    //   defaultValue: "Click to edit",
      
    // })

    const priceLevel = (str: string): string => {
      if (str == "PRICE_LEVEL_FREE"){
        return "Free"
      } 
      if (str == "PRICE_LEVEL_INEXPENSIVE"){
        return "$"
      } 
      if (str == "PRICE_LEVEL_MODERATE"){
        return "$$"
      } 
      if (str == "PRICE_LEVEL_EXPENSIVE"){
        return "$$$"
      } 
      if (str == "PRICE_LEVEL_VERY_EXPENSIVE"){
        return "$$$$"
      } 
      return ""
    }

    return(
    <APIProvider apiKey={gToken}>
      <div style={{ 
         height: '100vh', 
         width: '100vw', 
         position: 'fixed',
         top: 0,
         left: 0,
         right: 0,
         bottom: 0,
         overflow: 'hidden'
       }}>
      <Map
        mapId="60d59c6481bdec7c"
        style={{
          width: '100%', 
          height: '100%',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0
        }}
        defaultCenter={newCenter}
        defaultZoom={newZoom}
        // defaultBounds={newBounds}
        onDragend={onDragEnd}
        onZoomChanged={onZoomChanged}
        onClick={() => setActiveMarker(null)}
        gestureHandling={'greedy'}
        disableDefaultUI={true}
        reuseMaps={true}
        mapTypeControl={true}
        streetViewControl={true}
        fullscreenControl={true}
      >
        <Box 
          position="absolute" 
          bottom={isMobile ? 20 : 30} 
          left={isMobile ? 10 : 20} 
          zIndex={10}
        >
          <Button
            onClick={() => {
              setPlaces([]);
              setActiveMarker(null);
              setShowInfo(false);
              setDirectionData(null);
              setUrl("");
              setTeleUrl("");
            }}
            colorScheme="blue"
            size={isMobile ? "sm" : "md"}
            boxShadow="md"
          >
            <FiArrowLeft/>
            Back
          </Button>
        </Box>
        
        <HStack 
          position="absolute" 
          top={isMobile ? 5 : 10} 
          left="50%" 
          transform="translateX(-50%)" 
          zIndex={1} 
          gap={2}
        >
          <SegmentGroup.Root defaultValue={transportMode === "TRANSIT" ? "Public Transport" : "Driving"} onValueChange={(details) => {
            const mode = details.value === "Public Transport" ? "TRANSIT" : "DRIVE";
            setTransportMode(mode);
          }}>
            <SegmentGroup.Indicator />
            <SegmentGroup.Items items={["Public Transport", "Driving"]}/>
          </SegmentGroup.Root>
          {/* wrap editable in a box that fits it exactly and set background color */}
          {/* <Box bg="grey" p={1} borderRadius="md" opacity={0.5}> */}
            <Editable.Root defaultValue="Edit current location" opacity={0.8}
              bg={"white"}
              // onFocusOutside={(e) => {}}
              onValueCommit={(details) => editUserLocation(details.value!)}>
              <Editable.Preview color={"black"}/>
              <Editable.Input color={"black"}/>
              <Editable.Control>
                <Editable.SubmitTrigger color={"white"} asChild>
                <IconButton variant="outline" size="xs" color={"white"} >
                  <FiCheck />
                </IconButton>
              </Editable.SubmitTrigger>
              </Editable.Control>
            </Editable.Root>
          {/* </Box> */}
        </HStack>
      {locations.map((location, index) => (
        // console.log("location", location),
        <React.Fragment key={index}>
          <AdvancedMarker
            key={index}
            position={{ lat: location.Lat, lng: location.Long}}
            title={location.Name}
            onClick={() => fetchTravelTime(index)}
          >
            <Pin
              background={activeMarker === index ? '#FF0000' : '#22ccff'}
              borderColor={'#1e89a1'}
              glyphColor={'#0f677a'}
              scale={isMobile ? 0.6 : 1}
            />
          </AdvancedMarker> 
          {/* todo - if address is wrong, allow edit */}
          {activeMarker === index && showInfo &&(
            <Drawer.Root open={activeMarker != null} placement={isMobile ? "bottom" : "start"} size="sm">
              <Drawer.Backdrop />
              <Drawer.Trigger />
              <Drawer.Positioner>
                <Drawer.Content maxH={isMobile ? "70vh" : "100vh"} borderTopRadius={isMobile ? "lg" : "none"}>
                  <Drawer.Header borderBottomWidth="1px" display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Drawer.Title color="gray.900" fontSize="xl" fontWeight="bold">{location.Name}</Drawer.Title>
                      <Flex align="center" mt={1}>
                        <RatingGroup.Root allowHalf readOnly count={5} defaultValue={location.Rating ?? 0} size="sm" colorPalette="yellow">
                          <RatingGroup.HiddenInput />
                          <RatingGroup.Label color="gray.500" fontSize="sm" fontWeight="medium">{location.Rating}</RatingGroup.Label>
                          <RatingGroup.Control />
                        </RatingGroup.Root>
                        <Text fontSize="sm" color="gray.500" ml={1}>({location.RatingCount ? location.RatingCount : "N/A"})</Text>
                        {location.PriceLevel != null && 
                          <Text color="gray.500" fontSize="sm" ml={1}>{priceLevel(location.PriceLevel)}</Text>
                        }
                      </Flex>
                      {places[activeMarker?? 0].Status != "OPERATIONAL" && 
                        <Text color="red">{location.Status}</Text>
                      }
                    </Box>
                  </Drawer.Header>
                  <Drawer.CloseTrigger asChild>
                    <CloseButton size="sm" bg="white" onClick={() => setShowInfo(false)}/>
                  </Drawer.CloseTrigger>
                  <Drawer.Body>
                    <HStack gap={4} mb={4}>
                      {location.DirectionLink && 
                        <Button bg="blue.500" rounded="full" flex="1" asChild>
                          <a href={location.DirectionLink ?? ""} target="_blank" rel="noopener noreferrer">
                            <FiNavigation color='white'/>
                            <Span color={"white"}>Directions</Span>
                          </a>
                        </Button>
                      }
                      {location.GoogleLink && 
                        <Button variant="outline" rounded="full" flex="1" asChild>
                          <a href={location.GoogleLink ?? ""} target="_blank" rel="noopener noreferrer">
                            <FaMapMarkedAlt color='blue.500'/>
                            <Span color={"blue.500"}>View on Google</Span>
                          </a>
                        </Button>
                      }
                      {location.Website && 
                        <Button variant="outline" rounded="full" flex="1" asChild>
                          <a href={location.Website ?? ""} target="_blank" rel="noopener noreferrer">
                            <FiGlobe color='blue.500'/>
                            <Span color={"blue.500"}>Website</Span>
                          </a>
                        </Button>
                      }
                    </HStack>
                    <VStack gap={3} align="stretch">
                    {location.Description != null && location.Description.length > 0 &&
                        <Blockquote.Root>
                          <Blockquote.Content>
                            <Text color="gray.500">{location.Description}</Text>
                            </Blockquote.Content>
                        </Blockquote.Root>
                      }
                      <Flex align="center">
                        <Icon as={FiMapPin} mr={2} color="gray.500" />
                        <Text color="gray.500">{location.Address}</Text>
                      </Flex>
                      <Flex align="center">
                        {location.OpeningHours?.openNow !== undefined && 
                          <Accordion.Root collapsible>
                            <Accordion.Item key={0} value={""}> 
                              {/* location.OpeningHours?.openNow ? "Open Now" : "Closed" */}
                              <Accordion.ItemTrigger bg={"white"}>
                                <Icon as={FiClock} mr={2} color="gray.500" />
                                <Span flex="1" color={location.OpeningHours?.openNow ? "green" : "red"}>{location.OpeningHours?.openNow ? "Open Now" : "Closed"}</Span>
                                <Accordion.ItemIndicator />
                              </Accordion.ItemTrigger>
                              <Accordion.ItemContent>
                                <Accordion.ItemBody color="gray.500">
                                  {location.OpeningHours?.weekdayDescriptions.map((day: string, index: number) => (
                                    <Text key={index}>{day}</Text>
                                  ))}
                                  {/* {location.OpeningHours?.weekdayDescriptions.join("\n")} */}
                                </Accordion.ItemBody>
                              </Accordion.ItemContent>
                            </Accordion.Item>
                          </Accordion.Root>
                        }
                      </Flex>
                      {directionData && 
                        <Flex flexDirection="column" gap={1}>
                          <Text color="gray.500">Travel time via {directionData.mode}:</Text>
                          <Text color="gray.500">Total duration: {directionData.duration} {directionData.walkingDuration ? `(Walking duration: ${directionData.walkingDuration})` : ""}</Text>
                          <Text color="gray.500">Total distance: {directionData.distance} {directionData.walkingDistance ? `(Walking distance: ${directionData.walkingDistance})` : ""}</Text>
                        </Flex>
                      }
                      <HStack gap={2}>
                        <Button bg={"blue.500"} rounded="full" flex="1" asChild>
                          <a href="#" data-disabled="" onClick={() => deleteLocation(index)}>
                            <Span color="white">Delete</Span>
                          </a>
                        </Button>
                        <Button bg="blue.500" rounded="full" flex="1" asChild>
                          <a href="#" data-disabled="" onClick={() => editLocation(index)}>
                            <Span color="white">Edit</Span>
                          </a>
                        </Button>
                      </HStack>
                    </VStack>
                  </Drawer.Body>
                  <Drawer.Footer />
                </Drawer.Content>
              </Drawer.Positioner>
            </Drawer.Root>
          )}
          {activeMarker != null && directionData && directionData.polyline.length > 0 &&
            <Polyline
            encodedPath={directionData.polyline}
            strokeColor="#FF0000"
            strokeOpacity={1.0}
            strokeWeight={4}
          />
          }
          {userLocation != null && <AdvancedMarker position={{ lat: userLocation.lat, lng: userLocation.lng }}>
            <Pin background="#e8e54a" borderColor="#7a792a" glyphColor="#0f677a" glyph={"𖨆"} scale={isMobile ? 0.6 : 1} />
          </AdvancedMarker>}
        </React.Fragment>
        ))}
        </Map>
      </div>
    </APIProvider>
    )
  }

  // show main screen until address is scraped
  if (places.length == 0 || gToken == null){
    return (
      <ChakraProvider value={defaultSystem}>
        <div style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: places.length > 0 ? "flex-end" : "center",
          height: "100vh",
          padding: 20,
        }}>
          <div className="card"> 
              <h1>{firstName ? "Hi "+firstName+',' : ""} Enter link below to begin</h1>
              <input
                type="text" placeholder="Enter Url" value={url} onKeyDown={fetchInfoEnter} onChange={(e) => setUrl(e.target.value)}
                style={{ padding: 10, width: "80%", marginBottom: 10 }}
              />
              <button onClick={fetchInfo} style={{ padding: 10, width: "80%" }} >Scrape</button>
              {loading && <Box pos="absolute" inset="0" bg="bg/80">
                <Center h="full">
                  <Spinner color="teal.500" />
                </Center>
              </Box>}
              <Toaster/>
            
          </div>
        </div>
      </ChakraProvider>
    )
  }

  return (
    <ChakraProvider value={defaultSystem}>
      <div style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: places.length > 0 ? "flex-end" : "center",
        height: "100vh",
        padding: 20,
      }}>
        {/* // url != "" ? (<h1>Url found {url}</h1>) : */}
        <Box position="relative" aria-busy="true" userSelect="none">
          <Toaster />
          {gToken != null &&
            <LocationMap locations={places} />
          }
          {loading && <Box pos="absolute" inset="0" bg="bg/80">
            <Center h="full">
              <Spinner color="teal.500" />
            </Center>
          </Box>}
        </Box>
      </div>
    </ChakraProvider>
  )
}

export default App
