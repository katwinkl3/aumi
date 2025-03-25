import React, { useEffect, useState } from 'react'
import './App.css'
import WebApp from '@twa-dev/sdk'
import {APIProvider, Map, AdvancedMarker, Pin, InfoWindow} from '@vis.gl/react-google-maps';
import {LoadingSpinner, ErrorMessage} from './components/elements';
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

function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [firstName, setFirstName] = useState<string | null>(null);
  const [url, setUrl] = useState<string>("");
  const [gToken, setGtoken] = useState<string | null>(null); // Initialize state
  const [places, setPlaces] = useState<PlaceInfo[]>([]);
  // const [locations, setLocations] = useState<{ lat: number; lng: number }[]>([]);
  // const [count] = useState(0)
  // const [userData, setUserData]=useState<UserData | null>(null);
  // const [message, setMessage] = useState("");
  // const [buttonText, setButtonText] = useState<string>("Your text will appear here"); // Stores button text

  const Domain = "http://127.0.0.1:5000"
  const ScrapperPath = "/test_scrapper"
  // init tele + gmaps

  const LocationMap = ({ locations }: { locations: PlaceInfo[]}) => {
    if (locations.length == 0 || gToken == null) {
      setError("No locations found or no google maps token");
      return
    }
    const [activeMarker, setActiveMarker] = useState<number | null>(null);

    // Get average of all locations
    const calculateCenter = (locations: PlaceInfo[]) => {
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
    const handleRedirect = (url?: string) => {
      if (url != "") {
        window.open(url, '_blank', 'noopener,noreferrer');
      }
    };
    return <APIProvider apiKey={gToken}>
      <div style={{ height: '100vh', width: '100%' }}>
      <Map
        mapId="60d59c6481bdec7c"
        style={{width: '100vw', height: '100vh'}}
        defaultCenter={calculateCenter(locations)} // TODO: change to average of all location
        defaultZoom={12}
        gestureHandling={'greedy'}
        disableDefaultUI={true}
        reuseMaps={true}
        mapTypeControl={true}
        streetViewControl={true}
        fullscreenControl={true}
      >
      {locations.map((location, index) => (
        console.log("location", location),
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
          {activeMarker === index && (
            <InfoWindow
              position={{ lat: location.Lat, lng: location.Long }}
              onCloseClick={() => setActiveMarker(null)}
            >
              <div style={{ padding: '12px',
                color: '#333',
                fontFamily: 'Arial, sans-serif'
              }}>
                <h3 style={{ marginTop: '0 0 8px 0', color: '#222' }}>{location.Name}</h3>
                <p>{location.Address}</p>
                ${location.Status != "OPERATIONAL" ? `<p>Permanently Closed</p>`: ``}
                ${location.Rating != null ? `<p>Rating: ${location.Rating}</p>` : ``}
                ${location.RatingCount != null ? `<p>Rating Count: ${location.RatingCount}</p>` : ``}
                ${location.PriceLevel != null ? `<p>Price Level: ${location.PriceLevel}</p>` : ``}
                ${location.OpeningHours != null ? `<p>Opening Hours: ${location.OpeningHours}</p>` : ``}
                {location?.Website && (
                      <button
                        onClick={() => handleRedirect(location.Website||"")}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: '#4285F4',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '14px'
                        }}
                      >
                        Visit Website
                      </button>
                )}
                {location.GoogleLink && (
                      <button
                        onClick={() => handleRedirect(location.GoogleLink||"")}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: '#4285F4',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '14px'
                        }}
                      >
                        View on Google Maps
                      </button>
                )}
                {location.DirectionLink && (
                      <button
                        onClick={() => handleRedirect(location.DirectionLink||"")}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: '#4285F4',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '14px'
                        }}
                      >
                        Get Directions
                      </button>
                )}
                </div>
            </InfoWindow>
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
  
  // Fetch user data from backend
  useEffect(() => {
      setLoading(true);
      setError(null);
      const urlParams = new URLSearchParams(window.location.search);
      const messageParam = urlParams.get('message');
      if (messageParam) {
        console.log("messageParam", messageParam);
        setUrl(decodeURIComponent(messageParam));
      }
      try{
        fetch(Domain+"/google_token")
        .then((res) => res.text())
        .then((text) => setGtoken(text || ""));
        console.log("WebApp.initDataUnsafe", WebApp.initDataUnsafe);
        console.log("WebApp.initDataUnsafe.user", WebApp.initDataUnsafe.user);
        setFirstName(WebApp.initDataUnsafe.user?.first_name || null);
        console.log("WebApp.initDataUnsafe.start_param", WebApp.initDataUnsafe.start_param);
        setUrl(WebApp.initDataUnsafe.start_param || "");
      } catch (err) {
        console.error('Error fetching user data:', err);
        setError('Failed to load user data. Please try again.');
      }
      setLoading(false);
  }, []);

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
    const data = await resp.json();
    if (Array.isArray(data)) {
      setPlaces(data);
    } else {
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
        loading ? (<LoadingSpinner message="Loading your information..." />) :
        error ? (<ErrorMessage message={error} />) :
        // url != "" ? (<h1>Url found {url}</h1>) :
        <div className="card"> 
        <h1>Welcome {firstName}</h1>
        <input
          type="text" placeholder="Enter Url" value={url} onKeyDown={fetchInfoEnter} onChange={(e) => setUrl(e.target.value)}
          style={{ padding: 10, width: "80%", marginBottom: 10 }}
        />
        <button onClick={fetchInfo} style={{ padding: 10, width: "80%" }} >Scrape</button>
        {/* <button>
          {buttonText || "Your text will appear here"}
        </button> */}
        {/* <button onClick={() => WebApp.showAlert(`Hello ${url} Current count is ${count}`)}>
            Show Alert
        </button> */}
        {/* <button onClick={sendMessageToBot}>Send to Bot</button> */}
        {gToken != null && places.length > 0 &&
          <LocationMap locations={places} />
        }
      </div>}
    </div>
  )
}

export default App
