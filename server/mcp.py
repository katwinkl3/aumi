from scrapper import *
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("aumi")

@mcp.tool()
def scraper(url):
    """Retrieves and converts into text, the text, image, video subtitles from any url

    Args:
        url: url string (e.g. https://vt.tiktok.com/example/)
    """
    res, _, err = scrape(url)
    return res or err

@mcp.tool()
def address_info(name):
    """Retrieves location struct from google map containing Id, Name, Address, Lat, Long, 
    Status, Rating, RatingCount, PriceLevel, OpeningHours, Website, GoogleLink, DirectionLink, Description

    Args:
        name: address name string (e.g. bugis junction)
    """
    res, err = map_info(name)
    return str(res) if res else err

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')