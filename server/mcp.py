from scrapper import *
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("aumi")

def scrape_mcp_test(url):
    res =  '''As excited as we are to see what 2025 has in store for Singapore's bustling café scene – like the opening of Burnt Ends Bakery’s new space in a car showroom – we certainly loved the fresh café concepts that emerged in 2024❤️ These include Ahimsa Sanctuary’s Bali-like haven for delicious vegan fare, Dearborn’s elevated granola bar, Butter Tgt’s delicious hype-worthy bakes served in its gorgeous space, and more☕️Which of these spots will you be hitting up for your next cuppa?
📸: (1)Ahimsa (2)Butter Tgt (3)174Bingo (4)Atipico (5)Dearborn (6)Frankie and Fern's (7)Marymount Bakehouse
#timeoutsg  #exploresingapore  #singapore  #timeouteats  #sgfoodie  #newcafes  #igsg  #whattoeat  #cafes'''
    return res, "", None

@mcp.tool()
def scraper(url):
    """Retrieves and converts into text, the text, image, video subtitles from any url

    Args:
        url: url string (e.g. https://vt.tiktok.com/example/)
    """
    res, _, err = scrape_mcp_test(url) # scrape(url)
    return res or err

@mcp.tool()
def address_info(name):
    """Retrieves location struct from google map containing Id, Name, Address, Lat, Long, 
    Status, Rating, RatingCount, PriceLevel, OpeningHours, Website, GoogleLink, DirectionLink, Description

    Args:
        name: address name string (e.g. bugis junction)
    """
    res, err = map_info_mcp_test(name) # map_info(name)
    return str(res) if res else err

@mcp.tool
def reservation_slots(name, pax, date):
    """Retrieves dine in reservation time slots available for some group size on some date

    Args:
        name: dining establishment name string (e.g. awesome cafe)
        pax: number of people to reserve for (e.g. 2)
        date: date to reserve (e.g. 14/05/2025)
    """
    timing = set(f"{random.randint(1, 12)}.{random.choice([0, 30]):02d}{random.choice(['am', 'pm'])}" for _ in range(random.randint(0, 12)))
    return list(timing)

@mcp.tool
def ticket_pricing(name, date):
    """Retrieves the price of tickets for some ticketed location on some date

    Args:
        name: ticketed location name string (e.g. national museum)
        date: date to reserve (e.g. 14/05/2025)
    """
    return random.randint(0, 100)

def map_info_mcp_test(name):
    return PlaceInfo(
        Id="test_id",
        Name=name,
        Address="address",
        Lat=1 + 9/60 + random.random() * 20/60,
        Long=103 + 36/60 + random.random() * 49/60,
        Status=random.choice(["OPERATIONAL", "CLOSED_TEMPORARILY", "CLOSED_PERMANENTLY"]),
        Rating=round(random.uniform(1, 5), 1),
        RatingCount=random.randint(10, 5000),
        PriceLevel=None,
        OpeningHours={'openNow': False, 'periods': [{'open': {'day': 0, 'hour': 9, 'minute': 0, 'date': {'year': 2025, 'month': 5, 'day': 18}}, 'close': {'day': 0, 'hour': 17, 'minute': 30, 'date': {'year': 2025, 'month': 5, 'day': 18}}}, {'open': {'day': 0, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 5, 'day': 18}}, 'close': {'day': 0, 'hour': 21, 'minute': 30, 'date': {'year': 2025, 'month': 5, 'day': 18}}}, {'open': {'day': 1, 'hour': 9, 'minute': 30, 'date': {'year': 2025, 'month': 5, 'day': 19}}, 'close': {'day': 1, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 5, 'day': 19}}}, {'open': {'day': 2, 'hour': 9, 'minute': 30, 'date': {'year': 2025, 'month': 5, 'day': 13}}, 'close': {'day': 2, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 5, 'day': 13}}}, {'open': {'day': 3, 'hour': 9, 'minute': 30, 'date': {'year': 2025, 'month': 5, 'day': 14}}, 'close': {'day': 3, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 5, 'day': 14}}}, {'open': {'day': 4, 'hour': 9, 'minute': 30, 'date': {'year': 2025, 'month': 5, 'day': 15}}, 'close': {'day': 4, 'hour': 17, 'minute': 0, 'date': {'year': 2025, 'month': 5, 'day': 15}}}, {'open': {'day': 5, 'hour': 9, 'minute': 30, 'date': {'year': 2025, 'month': 5, 'day': 16}}, 'close': {'day': 5, 'hour': 17, 'minute': 30, 'date': {'year': 2025, 'month': 5, 'day': 16}}}, {'open': {'day': 5, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 5, 'day': 16}}, 'close': {'day': 5, 'hour': 21, 'minute': 30, 'date': {'year': 2025, 'month': 5, 'day': 16}}}, {'open': {'day': 6, 'hour': 9, 'minute': 0, 'date': {'year': 2025, 'month': 5, 'day': 17}}, 'close': {'day': 6, 'hour': 17, 'minute': 30, 'date': {'year': 2025, 'month': 5, 'day': 17}}}, {'open': {'day': 6, 'hour': 18, 'minute': 0, 'date': {'year': 2025, 'month': 5, 'day': 17}}, 'close': {'day': 6, 'hour': 21, 'minute': 30, 'date': {'year': 2025, 'month': 5, 'day': 17}}}]},
        Website="www.website.com",
        GoogleLink="www.google.com",
        DirectionLink="www.directions.com",
        Description='test description'
    ), None



if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')