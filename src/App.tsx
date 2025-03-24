import { useEffect, useState } from 'react'
import './App.css'
import WebApp from '@twa-dev/sdk'
import {APIProvider, Map} from '@vis.gl/react-google-maps'; // , AdvancedMarker, Pin
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

  // let map: google.maps.Map;
  // async function initMap(): Promise<void> {
  //   const { Map } = await google.maps.importLibrary("maps") as google.maps.MapsLibrary;
  //   const bounds = new google.maps.LatLngBounds();
  //   places.forEach(place => {
  //     bounds.extend({ lat: place.Lat, lng: place.Long });
  //   });
  //   map = new Map(document.getElementById("map") as HTMLElement, {
  //     center: bounds.getCenter(),
  //     zoom: 12,
  //   });
  // }
  
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
      new Notification("Invalid URL", { body: "Not a valid url" });
    }
    var matches = url.match(/^https?\:\/\/([^\/?#]+)(?:[\/?#]|$)/i);
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
        url != "" ? (<h1>Url found {url}</h1>) :
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
          <APIProvider apiKey={gToken}>
            <Map
              style={{width: '100vw', height: '100vh'}}
              defaultCenter={{lat: places[0].Lat, lng: places[0].Long}}
              defaultZoom={10}
              gestureHandling={'greedy'}
              disableDefaultUI={true}
              reuseMaps={true}
            />
          </APIProvider>
        }
      </div>}
    </div>
  )
}

export default App
