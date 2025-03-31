import React, { useEffect, useState, useCallback } from 'react'
import './App.css'
import WebApp from '@twa-dev/sdk'
import {APIProvider, Map, AdvancedMarker, Pin, MapCameraChangedEvent, MapEvent} from '@vis.gl/react-google-maps';
import {LoadingSpinner, ErrorMessage} from './components/elements';
import {Drawer, RatingGroup, CloseButton, VStack, Box, Text, Flex, Button, HStack, Icon, ChakraProvider, defaultSystem} from '@chakra-ui/react'
import { FiNavigation, FiGlobe, FiMapPin, FiClock } from 'react-icons/fi';
import { FaMapMarkedAlt } from 'react-icons/fa';

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
}

interface ScrapperErrorResponse {
  error: string; // Error message from Flask
}

function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [firstName, setFirstName] = useState<string | null>(null);
  const [url, setUrl] = useState<string>("");
  const [gToken, setGtoken] = useState<string | null>(null);
  const [places, setPlaces] = useState<PlaceInfo[]>([]);
  const [travelData, setTravelData] = useState<Record<string, any>>({});
  const [displayTravelTime, setDisplayTravelTime] = useState(false);
  const [activeMarker, setActiveMarker] = useState<number | null>(null);
  const [newCenter, setNewCenter] = useState<google.maps.LatLngLiteral>();
  const [newZoom, setNewZoom] = useState(12);
  // const [userData, setUserData]=useState<UserData | null>(null);
 

  const Domain = "http://127.0.0.1:5000"
  const ScrapperPath = "/test_scrapper"
  const DirectionPath = "/direction"

  // Fetch user and url data from telegram
  useEffect(() => {
    setLoading(true);
    setError(null);
    const urlParams = new URLSearchParams(window.location.search);
    const messageParam = urlParams.get('message');
    if (messageParam) {
      console.log("messageParam from telegram", decodeURIComponent(messageParam));
      setUrl(decodeURIComponent(messageParam));
    }
    try{
      fetch(Domain+"/google_token")
      .then((res) => res.text())
      .then((text) => setGtoken(text || ""));
      // console.log("WebApp.initDataUnsafe", WebApp.initDataUnsafe);
      // console.log("WebApp.initDataUnsafe.user", WebApp.initDataUnsafe.user);
      setFirstName(WebApp.initDataUnsafe.user?.first_name || null);
      // console.log("WebApp.initDataUnsafe.start_param", WebApp.initDataUnsafe.start_param);
      setUrl(WebApp.initDataUnsafe.start_param || "");
    } catch (err) {
      console.error('Error fetching user data:', err);
      setError('Failed to load user data. Please try again.');
    }
    setLoading(false);
  }, []);

  const isMobile = Math.min(window.screen.width, window.screen.height) < 768 || navigator.userAgent.indexOf("Mobile") > -1;

  // init tele + gmaps

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

    // Get bounds of all locations with 10% buffer
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
      var north = 0, south = 0, east = 0, west = 0;
      // var north = 85;
      // var south = -85;
      // var east = 180;
      // var west = -180
      locations.forEach(loc => {
        if (loc.Lat > north) north = loc.Lat;
        if (loc.Lat < south) south = loc.Lat;
        if (loc.Long > east) east = loc.Long;
        if (loc.Long < west) west = loc.Long;
      });
      return { north: north, south: south,east: east, west: west};
    }

  // UI component for map
  const LocationMap = ({ locations }: { locations: PlaceInfo[]}) => { //todo - switch to mapbox
    if (locations.length == 0 || gToken == null) {
      setError("No locations found or no google maps token");
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
      // console.log("zoom", e.detail.zoom);
    }, []);

    const onDragEnd = useCallback((e: MapEvent) => {
      // console.log("drag end: center", e.map.getCenter(), "zoom", e.map.getZoom(), "bounds", e.map.getBounds());
      if (e.map.getCenter() != null) {
        // console.log("drag end: center", e.map.getCenter()?.toJSON());
        setNewCenter(e.map.getCenter()?.toJSON());
      }
      // if (e.map.getZoom() != null) {
      //   console.log("drag end: zoom", e.map.getZoom());
      //   setNewZoom(e.map.getZoom() ?? 12);
      // }
    }, []);

    return <APIProvider apiKey={gToken}>
      <div style={{ height: '100vh', width: '100%' }}>
      <Map
        mapId="60d59c6481bdec7c"
        style={{width: '100vw', height: '100vh'}}
        defaultCenter={newCenter}
        defaultZoom={newZoom}
        onDragend={onDragEnd}
        onZoomChanged={onZoomChanged}
        gestureHandling={'greedy'}
        disableDefaultUI={true}
        reuseMaps={true}
        mapTypeControl={true}
        streetViewControl={true}
        fullscreenControl={true}
      >
         <div style={{
          position: 'absolute',
          top: 10,
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 1,
          backgroundColor: 'white',
          color: '#333',
          padding: '8px 12px',
          borderRadius: '4px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          border: '1px solid #dadce0'
        }} onClick={() => setDisplayTravelTime(!displayTravelTime)}>
          Display Travel Time
        </div>
      {locations.map((location, index) => (
        // console.log("location", location),
        <React.Fragment key={index}>
          <AdvancedMarker
            key={index}
            position={{ lat: location.Lat, lng: location.Long}}
            title={location.Name}
            onClick={() => setActiveMarker(index)}
          >
            <Pin
              background={activeMarker === index ? '#FF0000' : '#22ccff'}
              borderColor={'#1e89a1'}
              glyphColor={'#0f677a'}
            />
          </AdvancedMarker> 
          {/* todo - if address is wrong, allow edit */}
          {activeMarker === index &&(
          <ChakraProvider value={defaultSystem}>
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
                        <Text fontSize="sm" color="gray.500" ml={1}>({location.RatingCount})</Text>
                      </Flex>
                      {places[activeMarker?? 0].Status != "OPERATIONAL" && 
                        <Text color="red">{location.Status}</Text>
                      }
                      {location.PriceLevel != null && 
                        <Text color="gray.500" fontSize="sm" ml={1}>{location.PriceLevel}</Text>
                      }
                    </Box>
                  </Drawer.Header>
                  <Drawer.CloseTrigger asChild>
                    <CloseButton size="sm" colorScheme="white" onClick={() => setActiveMarker(null)}/>
                  </Drawer.CloseTrigger>
                  <Drawer.Body>
                    <HStack gap={4} mb={4}>
                      {location.DirectionLink && 
                        <Button colorScheme="blue.500" rounded="full" flex="1" asChild>
                          <a href={location.DirectionLink ?? ""} target="_blank" rel="noopener noreferrer">
                            <FiNavigation/> Directions
                          </a>
                        </Button>
                      }
                      {location.GoogleLink && 
                        <Button variant="outline" rounded="full" flex="1" asChild>
                          <a href={location.GoogleLink ?? ""} target="_blank" rel="noopener noreferrer">
                            <FaMapMarkedAlt /> View on Google
                          </a>
                        </Button>
                      }
                      {location.Website && 
                        <Button variant="outline" rounded="full" flex="1" asChild>
                          <a href={location.Website ?? ""} target="_blank" rel="noopener noreferrer">
                            <FiGlobe /> Website
                          </a>
                        </Button>
                      }
                    </HStack>
                    <VStack gap={3} align="stretch">
                      <Flex align="center">
                        <Icon as={FiMapPin} mr={2} color="gray.500" />
                        <Text color="gray.500">{location.Address}</Text>
                      </Flex>
                      <Flex align="center">
                        <Icon as={FiClock} mr={2} color="gray.500" />
                        {location.OpeningHours?.openNow !== undefined && 
                        <Text color="gray.500">{location.OpeningHours?.openNow ? "Open Now" : "Closed"}</Text>}
                        {/* todo: add opening hours */}
                      </Flex>
                    </VStack>
                  </Drawer.Body>
                  <Drawer.Footer />
                </Drawer.Content>
              </Drawer.Positioner>
            </Drawer.Root>
          </ChakraProvider>
        )}
        </React.Fragment>
        ))}
        </Map>
      </div>
    </APIProvider>
}

const handleMapError = async (): Promise<void> => {
  const mapElement = document.getElementById('map');
  if (mapElement) {
    mapElement.innerHTML = 
      '<div style="text-align:center; padding:20px;">' +
      '<h3>Error loading Google Maps</h3>' +
      '<p>Please check your API key and internet connection.</p>' +
      '</div>';
  }
}

const fetchTravelTime = async (locationId: string) => {
  if (travelData[locationId]) return; // Already cached
  try {
    // const response = await fetch(`${Domain+DirectionPath}?id=${locationId}`);
    // const data = await response.json();
    const data = {duration: 10, distance: 10};
    setTravelData(prev => ({ ...prev, [locationId]: data }));
  } catch (error) {
    console.error('Failed to fetch travel time:', error);
  }
};
  


  useEffect(() => {
    if (displayTravelTime && activeMarker !== null) {
      const locationId = places[activeMarker].Id;
      fetchTravelTime(locationId);
    }
  }, [displayTravelTime, activeMarker]);

  // fetchAddress sends url to /scrapper to fetch addresses
  const fetchInfo = async () => {
    if (!isValidHttpUrl(url)){
      console.log("Invalid URL", url);
      new Notification("Invalid URL", { body: "Not a valid url" });
    }
    var matches = url.match(/^https?\:\/\/([^\/?#]+)(?:[\/?#]|$)/i);
    // todo: invalid url match no notification
    var domain = matches && matches[1];
    switch (domain) {
      case "vt.tiktok.com":
        new Notification("Invalid URL", { body: "cant handle tiktok videos yet" });
        return
      case "youtu.be":
        new Notification("Invalid URL", { body: "cant handle youtube videos yet" });
        return
      case "www.instagram.com":
        new Notification("Invalid URL", { body: "cant handle instagram videos yet" });
        return
      default:
    }
    const resp = await fetch(Domain+ScrapperPath+`?url=${encodeURIComponent(url)}`);
    if (!resp.ok) {
      const errorData: ScrapperErrorResponse = await resp.json();
      setError(errorData.error);
      return;
    }
    const data = await resp.json();
    if (Array.isArray(data)) {
      setPlaces(data);
      setNewCenter(initializeCenter(data));
    } else {
      setError("empty response");
      setPlaces([]);
    }
  }
  
  const fetchInfoEnter = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      fetchInfo()
    }
  };

  const isValidHttpUrl = (str: string): boolean => {
    const pattern = new RegExp(
      '^(https?:\\/\\/)?' + // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|' + // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))' + // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*' + // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?' + // query string
        '(\\#[-a-z\\d_]*)?$', // fragment locator
      'i'
    );
    return pattern.test(str);
  }


  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: places.length > 0 ? "flex-end" : "center",
      height: "100vh",
      padding: 20,
    }}>
      {
        loading ? (<LoadingSpinner message="Loading..." />) :
        error ? (<ErrorMessage message={error} />) :
        // url != "" ? (<h1>Url found {url}</h1>) :
        <div className="card"> 
        <h1>Welcome {firstName}</h1>
        <input
          type="text" placeholder="Enter Url" value={url} onKeyDown={fetchInfoEnter} onChange={(e) => setUrl(e.target.value)}
          style={{ padding: 10, width: "80%", marginBottom: 10 }}
        />
        <button onClick={fetchInfo} style={{ padding: 10, width: "80%" }} >Scrape</button>
        {error && ( // todo change to proper error button
          <div style={{
            position: 'fixed',
            top: '20px',
            right: '20px',
            backgroundColor: '#ffebee',
            borderLeft: '4px solid #f44336',
            padding: '16px',
            borderRadius: '4px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <span>{error}</span>
            <button 
              onClick={() => setError(null)}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: '18px',
                color: '#666'
              }}
            >
              ×
            </button>
          </div>
        )}
        {gToken != null && places.length > 0 &&
          <LocationMap locations={places} />
        }
      </div>}
    </div>
  )
}

export default App
