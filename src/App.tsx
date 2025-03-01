import { useEffect, useState } from 'react'
import './App.css'
import WebApp from '@twa-dev/sdk'
import {APIProvider, Map, AdvancedMarker, Pin} from '@vis.gl/react-google-maps';
import {LoadingSpinner, ErrorMessage} from './components/elements';
WebApp.ready();

// let map: google.maps.Map;
// async function initMap(): Promise<void> {
//   const { Map } = await google.maps.importLibrary("maps") as google.maps.MapsLibrary;
//   map = new Map(document.getElementById("map") as HTMLElement, {
//     center: { lat: -34.397, lng: 150.644 },
//     zoom: 8,
//   });
// }

// initMap();

function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [firstName, setFirstName] = useState<string | null>(null);
  const [url, setUrl] = useState<string>("");
  const [gToken, setGtoken] = useState<string | null>(null); // Initialize state
  const [scrapedText, setScrapedText] = useState<string | null>(null); // Initialize state  
  const [locations, setLocations] = useState<{ lat: number; lng: number }[]>([]);
  // const [count] = useState(0)
  // const [userData, setUserData]=useState<UserData | null>(null);
  // const [message, setMessage] = useState("");
  // const [buttonText, setButtonText] = useState<string>("Your text will appear here"); // Stores button text

  const Domain = "http://localhost:5000"
  const ScrapperPath = "/scrapper"
  // init tele + gmaps
  
  // Fetch user data from backend
  useEffect(() => {
      setLoading(true);
      setError(null);
      try{
        fetch(Domain+"/google_token")
        .then((res) => res.json())
        .then((data) => setGtoken(data.key));
        setFirstName(WebApp.initDataUnsafe.user?.first_name || null)
      } catch (err) {
        console.error('Error fetching user data:', err);
        setError('Failed to load user data. Please try again.');
      } finally {
        setLoading(false);
      }
      
    // if (WebApp.initDataUnsafe.user) {
    //   setUserData(WebApp.initDataUnsafe.user as UserData);
    //   console.log(userData);
    // }
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
    setScrapedText(data.text);
    // setButtonText(url); // Update button text when Enter is pressed
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

  // google map api
  const generateLocations = async () => {

  }

  // 
  // const sendMessageToBot = async () => {
  //   if (!message.trim()) return;
    
  //   await fetch("http://localhost:5000/echo", {
  //     method: "POST",
  //     headers: { "Content-Type": "application/json" },
  //     body: JSON.stringify({ userId: userData?.id, text: message }),
  //   });

  //   // window.Telegram.WebApp.sendEvent("web_app_data_send", { message });
  //   setMessage(""); // Clear input
  // };

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: setScrapedText != null ? "flex-end" : "center",
      height: "100vh",
      padding: 20,
    }}>
      {
        loading ? (<LoadingSpinner message="Loading your information..." />) :
        error ? (<ErrorMessage message={error} />) :
        <div className="card"> 
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
        {gToken != null && scrapedText != null &&
          <APIProvider apiKey={""}>
            <Map
            style={{width: '100vw', height: '100vh'}}
            defaultCenter={{lat: 22.54992, lng: 0}}
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
