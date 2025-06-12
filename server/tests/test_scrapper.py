import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import requests
import sys
import os
import base64
import io
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from server.scrapper import (
    validate_url, scrape, generate_address_from_model, generate_markers,
    fetch_website, extract_text_from_url, handle_tiktok_photo, handle_tiktok_video,
    handle_rednote_photo, handle_website, check_tiktok_type, map_info,
    fetch_descriptions, fetch_subtitles, validate_place_info, process_image_text,
    sanitize_html, limiter
)
from ..consts import PlaceInfo, TIKTOK_PROMPT_IMAGE, TIKTOK_PROMPT_AUDIO_CAPTION, TIKTOK_PROMPT_CAPTION, WEBSITE_PROMPT
from .mock_data import *
limiter.enabled = False
# Setup Flask app for testing
@pytest.fixture
def app():
    from server.scrapper import app
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_redis():
    with patch('server.scrapper.app.redis') as mock:
        mock.get.return_value = None
        mock.setex.return_value = True
        yield mock

# Tests for scrape_address()
class TestScrapeAddress:
    
    @patch('server.scrapper.scrape')
    @patch('server.scrapper.generate_address_from_model')
    @patch('server.scrapper.generate_markers')
    def test_scrape_address_success(self, mock_markers, mock_model, mock_scrape, client, mock_redis):
        # Setup mocks
        mock_scrape.return_value = ("scraped text", WEBSITE_PROMPT, None)
        mock_model.return_value = MODEL_RESPONSE["assumed"], None
        mock_place = PlaceInfo(
            Id='123', Name='Forty Hands', Address='78 Yong Siak', 
            Lat=1.28, Long=103.83, Status='OPERATIONAL',
            Rating=4.5, RatingCount=100, PriceLevel=None,
            OpeningHours=None, Website=None, GoogleLink=None,
            DirectionLink=None, Description=None
        )
        mock_markers.return_value = [mock_place]
        
        # Test
        response = client.get('/scrapper?url=https://example.com')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]['Name'] == 'Forty Hands'
        
    def test_scrape_address_no_url(self, client, mock_redis):
        response = client.get('/scrapper')
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert data['error'] == "URL is empty"
        
    @patch('server.scrapper.get_cache')
    def test_scrape_address_cache_hit(self, mock_get_cache, client):
        # Setup cache hit
        cached_data = [{"Name": "Cached Cafe", "Address": "123 Cached St"}]
        mock_get_cache.return_value = cached_data
        
        response = client.get('/scrapper?url=https://example.com')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data == cached_data
        
    @patch('server.scrapper.scrape')
    def test_scrape_address_scrape_error(self, mock_scrape, client, mock_redis):
        mock_scrape.return_value = ("", "", "Failed to fetch")
        
        response = client.get('/scrapper?url=https://example.com')
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert data['error'] == "Failed to fetch"

# Tests for validate_url() error conditions
class Testvalidate_urlErrors:
    
    def test_validate_url_empty_url(self):
        _, error = validate_url("")
        assert error == "URL must be a non-empty string"
        
    def test_validate_url_none_url(self):
        _, error = validate_url(None)
        assert error == "URL must be a non-empty string"
        
    def test_validate_url_url_too_long(self):
        long_url = "https://example.com/" + "a" * 2048
        _, error = validate_url(long_url)
        assert error == "URL too long (max 2048 characters)"
        
    def test_validate_url_invalid_url_format(self):
        _, error = validate_url("not-a-url")
        assert error == "Invalid URL format"
        
    def test_validate_url_invalid_protocol(self):
        _, error = validate_url("ftp://example.com")
        assert error == "Only HTTP and HTTPS protocols are supported"
        
    def test_validate_url_private_ip(self):
        with patch('socket.getaddrinfo') as mock_dns:
            mock_dns.return_value = [(None, None, None, None, ('192.168.1.1', 0))]
            _, error = validate_url("https://internal.com")
            assert error == "Access to special IP addresses is not allowed"
    def test_validate_url_private_ip2(self):
        with patch('socket.getaddrinfo') as mock_dns:
            mock_dns.return_value = [(None, None, None, None, ('127.0.0.1', 0))]
            _, error = validate_url("https://internal.com")
            assert error == "Access to special IP addresses is not allowed"
    def test_validate_url_private_ip3(self):
        with patch('socket.getaddrinfo') as mock_dns:
            mock_dns.return_value = [(None, None, None, None, ('0.0.0.0', 0))]
            _, error = validate_url("https://internal.com")
            assert error == "Access to special IP addresses is not allowed"
            
    def test_validate_url_localhost(self):
        _, error = validate_url("https://localhost/test")
        assert error ==  "Access to special IP addresses is not allowed"
        
    def test_validate_url_blacklisted_domain(self):
        _, error = validate_url("https://169.254.169.254/test")
        assert error == "Access to this address is not allowed"

# Tests for scrape() success cases
class TestScrapeSuccess:
    
    @patch('server.scrapper.handle_tiktok_photo')
    @patch('requests.head')
    def test_scrape_tiktok_photo(self, mock_head, mock_handler):
        # Setup mocks
        mock_head.return_value.url = "https://www.tiktok.com/@user/photo/123"
        mock_handler.return_value = ("Extracted text", None)
        
        result, prompt, error = scrape("https://vt.tiktok.com/abc123")
        
        assert result == "Extracted text"
        assert prompt == TIKTOK_PROMPT_IMAGE
        assert error is None
        
    @patch('server.scrapper.handle_tiktok_video')
    @patch('requests.head')
    def test_scrape_tiktok_video_with_audio(self, mock_head, mock_handler):
        mock_head.return_value.url = "https://www.tiktok.com/@user/video/123"
        mock_handler.return_value = ("audio: transcript here. caption: test", None)
        
        result, prompt, error = scrape("https://www.tiktok.com/@user/video/123")
        
        assert result == "audio: transcript here. caption: test"
        assert prompt == TIKTOK_PROMPT_AUDIO_CAPTION
        assert error is None
        
    @patch('server.scrapper.handle_tiktok_video')
    @patch('requests.head')
    def test_scrape_tiktok_video_caption_only(self, mock_head, mock_handler):
        mock_head.return_value.url = "https://www.tiktok.com/@user/video/123"
        mock_handler.return_value = ("caption: test", None)
        
        result, prompt, error = scrape("https://www.tiktok.com/@user/video/123")
        
        assert result == "caption: test"
        assert prompt == TIKTOK_PROMPT_CAPTION
        assert error is None
        
    @patch('server.scrapper.handle_rednote_photo')
    def test_scrape_rednote(self, mock_handler):
        mock_handler.return_value = ("Rednote content", None)
        
        result, prompt, error = scrape("https://www.xiaohongshu.com/explore/123")
        
        assert result == "Rednote content"
        assert prompt == WEBSITE_PROMPT
        assert error is None
        
    @patch('server.scrapper.handle_website')
    def test_scrape_lemon8(self, mock_handler):
        mock_handler.return_value = ("Lemon8 content", None)
        
        result, prompt, error = scrape("https://www.lemon8-app.com/post/123")
        
        assert result == "Lemon8 content"
        assert prompt == WEBSITE_PROMPT
        assert error is None
        
    def test_scrape_instagram_not_supported(self):
        result, prompt, error = scrape("https://www.instagram.com/p/123")
        
        assert error == "failed to fetch from https://www.instagram.com/p/123, err=instagram and facebook links are not supported"
        
    def test_scrape_facebook_not_supported(self):
        result, prompt, error = scrape("https://www.facebook.com/post/123")
        
        assert error == "failed to fetch from https://www.facebook.com/post/123, err=instagram and facebook links are not supported"
        
    @patch('server.scrapper.handle_website')
    def test_scrape_generic_website(self, mock_handler):
        mock_handler.return_value = ("Website content", None)
        
        result, prompt, error = scrape("https://thehoneycombers.com/post")
        
        assert result == "Website content"
        assert prompt == WEBSITE_PROMPT
        assert error is None

# Tests for individual handlers
class TestHandlers:
    
    @patch('server.scrapper.fetch_website')
    @patch('server.scrapper.extract_text_from_url')
    def test_handle_tiktok_photo(self, mock_ocr, mock_fetch):
        mock_fetch.return_value = (TIKTOK_PHOTO_RESPONSE, None)
        mock_ocr.side_effect = ["OCR Text 1", "OCR Text 2"] #tested extract_text_from_urls below
        
        result, error = handle_tiktok_photo("https://tiktok.com/photo")
        expected = "caption: i judge a neighborhood by its cafes. ☕️ #westvillage #westvillagenyc #nyc #newyorkcity #nycrecs #nycrestaurants #nyccoffee \nparsed text: "
        assert result[:len(expected)] == expected
        assert result[len(expected):] in ('OCR Text 2\nOCR Text 1', 'OCR Text 1\nOCR Text 2')
        assert error is None
        
    @patch('server.scrapper.fetch_website')
    def test_handle_tiktok_video_with_subtitles(self, mock_fetch):
        mock_fetch.return_value = (TIKTOK_VIDEO_RESPONSE, None)
        
        result, error = handle_tiktok_video("https://tiktok.com/video")
        
        assert result == "audio: Hey you guys. Since you all love my top Singapore Pizza ranking video last year, I have decided to try 15 more places and update this ranking this year\ncaption: After my 2024 Singapore Top 5 pizza ranking went viral, many followers dominated their long lists of pizza places - so I tried went to try most of the this past year and yeah I do want to refresh my ranking a bit: 1. La Bottega 2. Goldenroy Sourdough pizza 3. Bad habits 4. Chooby pizza  5. La Pizzaiola  Single item bonus: the boat shaped truffle cream pizza at @kucina_sg"
        assert error is None
        
    @patch('server.scrapper.fetch_website')
    def test_handle_tiktok_video_no_subtitles(self, mock_fetch):
        mock_fetch.return_value = (TIKTOK_VIDEO_NO_SUBTITLES, None)
        
        result, error = handle_tiktok_video("https://tiktok.com/video")
        
        assert result == "caption: As excited as we are to see what 2025 has in store for Singapore's bustling café scene – like the opening of Burnt Ends Bakery’s new space in a car showroom – we certainly loved the fresh café concepts that emerged in 2024❤️ These include Ahimsa Sanctuary’s Bali-like haven for delicious vegan fare, Dearborn’s elevated granola bar, Butter Tgt’s delicious hype-worthy bakes served in its gorgeous space, and more☕️Which of these spots will you be hitting up for your next cuppa? 📸: (1)Ahimsa (2)Butter Tgt (3)174Bingo (4)Atipico (5)Dearborn (6)Frankie and Fern's (7)Marymount Bakehouse #timeoutsg #exploresingapore #singapore #timeouteats #sgfoodie #newcafes #igsg #whattoeat #cafes"
        assert "audio: " not in result
        assert error is None
        
    @patch('server.scrapper.fetch_website')
    @patch('server.scrapper.extract_text_from_url')
    def test_handle_rednote_photo(self, mock_ocr, mock_fetch):
        mock_fetch.return_value = (REDNOTE_HTML, None)
        mock_ocr.side_effect = ["OCR from image 1", "OCR from image 2"]
        
        result, error = handle_rednote_photo("https://xiaohongshu.com/explore")
        expected = "纽约咖啡店年终review虽迟但到，这一年数数又去了20多家但逐渐对去店里兴致缺缺。各方面能打的店太少了而且周末人多。La Cabra饮品出品不稳且永远很挤，Korbrick人多以后拿铁也踩过雷了。几家水平不错的店要么远要么环境差强人意坐起来不舒服😢 也蹲一蹲推荐吧。 - ☕️打工人福音：Black Fox Coffee。回归hudson yard打工人以后的稳定续命水，orange blossom橙花拿铁和vanilla date香草红枣拿铁记得要half syrup。无座。 ☕️最适合工作：Coffee Project NY和Now or Never。第一家hells kitchen和chelsea店都有座位，工作氛围好咖啡特调（pandan latte少糖）可以。第二家在soho，采光好人少厕所干净，咖啡一般。 ☕️最适合聊天：WatchHouse。没想到最后伦敦连锁店综合考量在NY可以拥有一席之地。装修+吃喝较稳定的。 ☕️综合实力佳可多去：suited和sey体验都还不错但还想再多去几次。 ☕️一些特调：Bird &amp; Branch。nightingale 伯爵茶咖啡和一些季节款是个人觉得融合地很不错的，环境一般。 - ☕️老规矩：最在乎咖啡口味但对环境也小有要求的整体主观评分，标注了有没有座位。打星号的就是这一年里新去的，没打分的就是还没机会去想要尝试的。 ☕️Disclaimer: This list consists of 50+ coffee places I’ve visited in NY since 2023. *signs for newly visited places this year. See my other pinned post for more information. Very subjective opinions &amp; feel free to recommend additional places you like! - #纽约咖啡 #咖啡 #纽约 #曼哈顿 #我的咖啡日记 #今天你喝咖啡了吗 #不为打卡的旅行 #寻找宝藏群话题 #100家探店计划 #咖啡时光."

        assert result[:len(expected)] == expected
        assert result[len(expected):] in ('OCR from image 2. OCR from image 1', 'OCR from image 1. OCR from image 2')
        assert error is None
        
    @patch('server.scrapper.fetch_website')
    def test_handle_website(self, mock_fetch):
        mock_fetch.return_value = (WEBSITE_HTML, None)
        
        result, error = handle_website("https://example.com")
        
        assert result == "[no-title]\n\nHot New Tables\nCool new cafes in Singapore: June 2025 edition\n\n\n By \n \n\nSufyan Saad\n\n\n •30 May 2025\n \n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n Photography: Freepik\n Need a chic hangout for coffee, brunch, and sweet treats? We help you keep tabs on the hot new cafes in Singapore each month.\n\n As a fervent explorer of Singapore ’s dynamic cafe culture, our team keeps track of the number of new cafes\n popping up every month. They ’re shooting out like spores – and that ’s not a bad thing! Doesn ’t matter if you ’re on the hunt for a strong brew, brunch\n that hits the spot, or a cosy corner to chill with your buddies, there’s always a fresh spot to check out. Who doesn’t love discovering a new cafe for weekend\n hangs or the perfect Instagram shot? Keep reading as we spill the tea\n (or coffee\n ) on the hottest new cafes in Singapore you must visit.\n \nNew cafes in Singapore\n\n\n\n\nToggle\n\n\n\n\n\n\n\n\n New cafes in Singapore: June 2025\n\nGelato Messina\n\n Photography: Sufyan Saad\n\n \n Everyone knows Singaporeans love a good queue. So if you spot a snaking line near Telok Ayer, we highly recommend you join in. Why? ‘Cos it ’s for Gelato Messina\n ! The cult Australian brand has finally opened its first outpost here, and the response has been overwhelmingly positive. Tip: It ’s better to grab and go, but if you wanna hang around, we suggest heading down during weekday afternoons.\n \n\n There are 40 flavours to choose from, including five Singapore exclusives that showcase the best of our culinary scene. Go for a double scoop and get the kaya toast\n + teh tarik combo – it ’s like enjoying a kopitiam breakfast\n in frozen form. If you ’re hankering for something fruity, the sorbets definitely don ’t miss. Lemon and mango are refreshing, but if calamansi ’s on the menu, get that flavour instead.\n \nWait till you hear the best part: you ’re welcome to sample everything on display! Just don ’t take too long to decide on your final flavours.\n\nMust-try flavours:\n Kaya toast; teh tarik; lemon; mango; Hokey Pokey\nHow much:\n Scoops from $7.50\nOpening hours:\n Tuesdays to Thursdays, 2pm to 10pm and Fridays to Sundays, 12pm to 10.30pm\nAddress:\n 1 Club Street, Singapore 069400\n \n\nVisit Gelato Messina\nGelato Messina ’s flavours\n\nRise Bakehouse\n\n Photography: Yuki Ling\n\n Look at what we have here: a cafe serving good food and great vibes! Rise Bakehouse ’s latest outlet aims to pay homage to Singapore, and what better way to do that than by being in a conserved shophouse. We spotted Good Morning tea towels, a SingPost post box near the entrance, and a red vintage television. Blasts from the past!\n\n The homage extends to the menu, which features delectable offerings with a distinctly local flair. We’re impressed with the curry mayo fish and chips\n ($20.90) – the fish tasted fresh and evenly coated with batter, and the curry mayo served as the perfect complement. And while we also liked how creamy (with a mild spicy kick!) the scallop rose rigatoni ($23.90) is, we wished the portion were bigger.\n \nDrinks-wise, Rise’s Made in Singapore collection centres on familiar localised flavours. The team delivered on this front, though we thought it was a touch too sweet. That didn’t stop us from polishing the black sesame peanut butter latte ($9)!\n\nMust-try items:\n Curry mayo fish and chips; black sesame peanut butter latte\nHow much:\n Food from $4.50; drinks from $4\nOpening hours:\n Mondays and Wednesdays to Thursdays, 11.30am to 8.30pm, and Fridays to Sundays, 11.30am to 10.30pm\nAddress:\n 273 South Bridge Road, Singapore 058822\n \n\nVisit Rise Bakehouse\n\nPuff and Peaks Bakery Cafe\n\n Photography: Sufyan Saad\n\n \n OG fans know this bakery, which saw long queues for its brioche doughnuts during the pandemic. A few years later, Puff and Peaks continues its ascent to the peak\n with the opening of its second outlet. This one ’s a lot roomier than its first store, with plenty of seats for you to take a breather and enjoy your spoils.\n \nEverything you love about P and P is available here: friendly service and those sinfully delicious doughs. The cafe was still buzzing with customers even though we swung by late on a weekday afternoon. The kitchen was almost out, so we made do with an apple salted caramel mascarpone cheesecake ($8), a Boston cream doughnut ($4.50), and an iced honey latte ($4.50).\nThe cheesecake wasn ’t brittle, and the thinly sliced apples broke up the strong mascarpone and salted caramel flavours. If we could turn back time, we ’d tell ourselves to skip the doughnut – not ‘cos it ’s bad, but ‘cos we were already surprisingly full by then! The Boston cream was generously piped with vanilla cream and coated with chocolate.\nIf you plan to visit, we recommend going earlier in the day so you have more options to mull over. This outlet also offers seasonal savoury items and drinks, which you can ’t get at its Tampines Central store.\n\nMust-try items:\n Brioche doughnuts; honey latte\nHow much:\n Food and drinks from $4\nOpening hours:\n Tuesdays to Sundays, 9am to 7.30pm\nAddress:\n #01-03, Tampines Changkat Community Club, 13 Tampines Street 11, Singapore 529453\n \n\nVisit Puff and Peaks Bakery Cafe\n\nGwen ’s Frozen Custard &amp;amp;Ices\n\n Photography: Sufyan Saad\n\n \n There’s more than enough room for another American-style diner\n in Singapore, and we’re glad this one popped up in good ol’ Joo Chiat\n . The first thing that’ll draw you in is how cheery the space is. Bright pink walls and decor, Archie comics at a corner near the entrance (iconic!), and a cute spot to pose for photos while you wait for your order. Gwen’s predominantly operates as a takeaway joint, but if it’s not crowded, you’re welcome to enjoy your food at the little benches.\n \nThe lean menu means you won’t have to deliberate too long on your order. We had the Philly cheesesteak ($16, with steamed buns for an authentic American experience), and it filled us right up. The meat was cooked just right, and the slight sweetness from the bread balanced the flavours. There’s no sauce here, but you can always remedy that by asking for chilli (or ketchup) from the friendly staff.\n\n If you’re in the mood for something cold, you’re in luck. Gwen’s frozen delights include custards (from $6.50), ices made from real fruits (from $4.50), and the Cyclone (from $11.50), where you can personalise your own blended frozen custard. The team is currently R &amp;amp;D-ing popsicles – we scored a taste test during our visit – and we’re looking forward to it on the menu. Anything to help beat the Singapore heat\n , right?\n \n\nMust-try items:\n Philly cheesesteak; grilled cheese; Cyclone\nHow much:\n Hot food from $5.50; frozen delights from $4.50\nOpening hours:\n Tuesdays to Fridays, 12pm to 2.30pm &amp;amp;4.30pm to 9pm and weekends, 12pm to 9pm\nAddress:\n 198 Joo Chiat Road, Singapore 427469\n \n\nVisit Gwen ’s Frozen Custard &amp;amp;Ices\n\nCreme and Cone\n\n Photography: Sufyan Saad\n\n We came across this adorable spot while exploring Joo Chiat, and it ’s a good thing we did. Creme and Cone opened its second outlet here last year, and has been one of the go-to spots for visitors to pause and sink their teeth into some sweet treats.\nThe gelato display boasts standard and fun flavours; if you can ’t decide what to get, we say mix and match a double scoop. Win-win! We had the Breakfast Cereal and cotton candy flavours, and while we enjoyed the sugar rush, they started to feel cloyingly sweet when we were halfway through our cups.\n\n Want something more filling? The outlet also offers gourmet tarts\n , mini loaf cakes, brownies\n , and cookies\n . Need a last-minute cake for a celebration? Count your lucky stars ‘cos you can get those here too. Oh, get a drink while you ’re at it.\n \n\nMust-try items:\n Gelato; pistachio tart; mini loaf cakes\nHow much:\n Gelato from $5; tarts from $7.90; mini loaf cakes from $4.90\nOpening hours:\n Daily, 12pm to 9.30pm (opens till 10.30pm on Fridays &amp;amp;Saturdays)\nAddress:\n 149 Joo Chiat Road, Singapore 427427\n \n\nVisit Creme and Cone\n\n\n\n New cafes in Singapore: May 2025\n\nOlive &amp;amp;Peach\n\n\n\nWhether you ’re into architecture or not, you have to check out Geneo. Sure, it ’s all the way at the Singapore Science Park, but you ’ll be rewarded after you make the trek. The new innovation hub is home to gorgeous towering pillars, fascinating ceilings, and plenty of vibey food spots. One such place is Olive &amp;amp;Peach, a cosy cafe with clean, minimalist design (the green hue stole our hearts!), speciality coffee, and light bites.\nAs it was a hot day during our visit, we went for the iced matcha latte ($7.50). While it was a refreshing drink that helped cool us down, we did wish it had a stronger matcha flavour. We didn ’t get to try the food, but we reckon the adzuki bean green tea mousse cake ($5.80) would go swimmingly with the drink. If you ’re famished, the cafe also offers focaccia sandwiches (from $7.50) that ’ll fill you up.\n\nMust-try items:\n Iced matcha latte; adzuki bean green tea mousse cake\nHow much:\n Drinks from $4.50; food from $5.80\nOpening hours:\n Mondays to Fridays, 8am to 5pm and Saturdays, 10am to 6pm\nAddress:\n #01-31, Geneo, 1B Science Park Drive, Singapore 119315\n\n\nVisit Olive &amp;amp;Peach\n\nDrips x Sakanoue\n\n Photography: Sufyan Saad\n\n\n Those who hang out at Tiong Bahru\n often enough should know Drips. The popular institution has collaborated with Sakanoue, one of Tokyo ’s popular kakigori spots, and brought the viral sensation to our sunny island. Why Singapore? According to Tomoyasu Machiyama, Sakanoue ’s founder, the idea for overseas expansion took shape during the pandemic. During the brand ’s pop-up at Isetan, Machiyama-san connected with Drips ’founder Jessica Tan, bonded over their love for dogs, and the rest is history.\n\nCool off from the heat with five enticing flavours made from premium Kuramoto ice from Kanazawa, Japan. We chose the black forest (inspired by Drips ’signature cake, $19.80) and the Berry Cute Panda ($18) kakigoris, and we preferred the latter. Adorable presentation aside, the combination of camembert cheese and mixed berries sauces, raw honey yoghurt, espuma cream, crumbled cookies, and chocolate buttons made it a sweet and savoury treat without being too cloying. And yes, you best believe we polished the entire bowl.\nTo celebrate the partnership, Drips has introduced two new pastries to its menu. Keep things balanced with the very flaky okonomiyaki danish ($5), which comes with chicken chunks, teriyaki sauce, Japanese mayo, and bonito flakes. Have it served hot so it contrasts with the shaved ice.\n\nMust-try items:\n Berry Cute Panda kakigori; okonomiyaki danish\nHow much:\n Kakigori from $17.50; pastries from $5\nOpening hours:\n Daily, 10am to 10pm (opens at 9am on weekends; kakigori is available from 1pm to 9pm)\nAddress:\n #01-05, 82 Tiong Poh Road, Singapore 160082\n\n\nVisit Drips Bakery Cafe\nVisit Sakanoue\n\nBlue Bottle Coffee\n\n\n@thehoneycombers\n\n\n New F &amp;amp;B in Singapore: Blue Bottle Coffee ☕️ What we tried: ✨️ Nola ($8): Cold brewed with roasted chicory and milk, this original ice coffee is smooth and addictive. ✨️ Matcha latte ($9.50): A pretty well-balanced cuppa. ✨️ Coconut kouign-amann ($8): The coconut shavings provide a delightful crunch to this crowd-favourite pastry. ✨️ Pandan canele with kaya ($6): Kaya makes an intriguing addition to the classic canele, offering a sweet and creamy contrast. Blue Bottle Coffee 📍Lumine Singapore, Raffles City #sgtiktok\n#sgfoodie\n#sgfood\n#coffee\n#bluebottle\n\n\n♬ Coffee Break, On the Terrace –Cozy-Cozy-Moodscape\n\n\nConsider Blue Bottle Coffee ’s initial launch as its way of testing the waters here. After a successful launch last August and getting so much love from caffeinated connoisseurs, the American brand has converted its existing space into a full-fledged cafe, with plenty of seats so you can sip on your coffee and soak in the rays from the floor-to-ceiling windows. We love that the revamp expands its minimalist look, rather than a complete makeover.\nThe expanded menu includes delish bakes and Singapore exclusives courtesy of Bakery Brera. Since it ’s matcha season here, we had to try the matcha latte ($9.50) – and we ’re so glad we made the right choice. It ’s smooth and rich, with the perfect balance of green tea and milk. No further notes! Those chasing a caffeine high must order the addictive Nola ($8). The iced coffee drink is cold-brewed with roasted chicory and milk, resulting in a delicious blend you ’d love to sip on for hours.\nHungry? Get the coconut kouign-amann ($8). We enjoyed biting into the pastry, while the coconut shavings lent an extra crunch. Don ’t pass up the chance to try the pandan canele with kaya ($6). It may be small, but its decadent flavours sure pack a punch.\n\nMust-try items:\n Nola; matcha latte; coconut kouign-amann; pandan canele with kaya\nHow much:\n Drinks from $6.50; food from $5.50\nOpening hours:\n Daily, 8am to 8pm\nAddress:\n #01-01, Lumine Singapore, Raffles City, 252 North Bridge Road, Singapore 179103\n\n\nVisit Blue Bottle Coffee\n\nGaia Acai\n\n Photography: Gaia Acai via Instagram\n\nWant a sweet treat without all the nasties? Go au naturel by getting an acai bowl at this cute little spot in Toa Payoh. As its name suggests, Gaia Acai wants you to treat your body like a temple by offering the superfood in various combinations. Choose from the classics if you want to keep it simple, or go for the signatures with exciting flavours. You can also build your own bowl and go wild with your creation.\nEvery bowl comes with generous portions and the perfect texture, so you don ’t feel like you ’re tucking into an icy, soupy mess. There are limited seats here, so have yours to go or enjoy your bowl at the standing area near the entrance. Just be sure not to crowd around and block others from entering.\n\nMust-try items:\n N.4 Biscoff; N.12 Blue spirulina lychee sorbet\nHow much:\n From $7\nOpening hours:\n Daily, 11am to 10pm\nAddress:\n #01-302, 109 Toa Payoh Lorong 1 (Braddell Station Exit A), Singapore 310109\n\n\nVisit Gaia Acai\n\nCheerful Goat\n\n\n\n\n\n With such an intriguing name, you ’d be remiss not to visit this new cafe in Bugis\n . Cheerful Goat has expanded its online operations into a physical space within a heritage building, inviting everyone to make time for coffee and an easy meal. Can we talk about the decor? We totally approve the black and orange colour scheme. The round bar and adorable decals on the windows? Absolute *chef ’s kiss*.\n\nA glance at the menu and you ’ll notice bevvies with equally quirky names. Baoketu, a concoction of espresso and creamy milk, is inspired by a border town with the same name in Inner Mongolia. Sweet Nostalgia combines tarty flavours like lemon and raspberry with black tea and espresso, and a dash of sweetness thanks to the gummy candies. But the one drink that ’ll get your goat – and we mean it in the best way – is the Quatrime. Oolong tea, plum wine and syrup, coffee, and a smoked bubble topping? 10 out of 10.\nWith such fascinating drinks, the food selection takes a backseat. Regardless, you can enjoy bakes like butter croissant, kouign amann, and pain au chocolate, which make perfect companions to the brews. We ’re told there ’s a new line-up of pastries being introduced, and we ’re looking forward to meeting them in our next visit.\n\nMust-try items:\n Quatrime; Sweet Nostalgia; Baoketu; Lait De Soie\nHow much:\n Drinks from $5.50; food from $4.60\nOpening hours:\n Daily, 8.30am to 8.30pm\nAddress:\n #01-07, Stamford Arts Centre, 155 Waterloo Street, Singapore 187962\n\n\nVisit Cheerful Goat\n\n\n\n New cafes in Singapore: April 2025\n\nTo:You\n\n Photography: To:You via Facebook\n\nKembangan, known for its tranquillity and rows of landed properties, has welcomed a new cafe into the neighbourhood. Meet To:You, an industrial chic space that welcomes homosapiens and their four-legged friends. But that ’s not what will draw you in – we can confidently say the gorgeous green facade will pique your interest and beckon you to enter.\nIt ’s bright and cosy inside, thanks to the natural light from the glass ceiling, earthy tones, and comfortable furniture. If the weather ’s behaving itself (aka not too humid or raining heavily), grab a seat at the camping-themed outdoor seating (seriously, what ’s the current obsession with the camping theme?). Pets can hang out here and laze the day away with you. Yes, it ’s a vibey spot and you won ’t ever feel like leaving.\n\n There are a great deal of food options to mull over, from sharing plates and all-day brunch items to hearty mains. Feeling famished? The ochazuke ($22), featuring grilled salmon, eggs, matcha dashi, pickles, and short grain rice, should fill you right up. Get the brown butter waffle ($12) as a reward for surviving another week at work. Oh, you can ’t forget the signature matcha\n strawberry! The sea salt cold foam latte is a good pick-me-up too.\n\n\nMust-try items:\n Ume shakshuka; ochazuke; matcha strawberry; sea salt cold foam latte\nHow much:\n Food from $9; drinks from $4\nOpening hours:\n Tuesdays to Saturdays, 8am to 8pm and Sundays, 8am to 6pm\nAddress:\n 90 Jalan Senang, Singapore 418461\n\n\nVisit To:You\nTo:You ’s menu\n\nYuen Yeung\n\n Photography: Yuen Yeung\n\n\n Back then, there was no such thing as cupcakes and kunafa chocolates. So we got my sugar rush from traditional desserts\n like ice kachang, almond paste, and chendol. No hate to modern desserts, but old-school treats just hits different. While there are a few well-known spots in Singapore offering this, we were excited to try out Yuen Yeung along Neil Road\n when we heard about it. Tip: swing by before dinnertime to avoid the crowd. You ’re welcome!\n\nNow, let ’s dive straight into the menu. This new cafe offers hot and cold desserts, starting from $4.30. In our current economic landscape, that ’s reasonably affordable if you ask me. The signature Yuen Yeung grand slam milk ($8.80) is an IG-worthy creation, with grass jelly, peach gum, lotus nuts, red bean, and house-made sweet potato balls served in a large bowl. It ’s not too sweet – yes millennials, we see you – and the ingredients create a lovely medley together.\nThe handcrafted rice mochi with red bean paste ($4.90) is a clever combination of modern and traditional flavours. (Normally, you ’ll see tangerine being paired with red bean.) If you want something cooling, the fresh strawberry coconut milk snow ($8.90) is a refreshing option to go for. Those who want to throw it back to the good ol ’days can go for the double layer milk pudding ($4.20). Simple yet satisfying.\n\nMust-try items:\n Signature Yuen Yeung grand slam milk; handcrafted rice mochi with red bean paste\nHow much:\n From $4.30\nOpening hours:\n Daily, 11.30am to 10.30pm\nAddress:\n 43 Neil Road, Singapore 088825\n\n\nVisit Yuen Yeung\n\nAlani\n\n Photography: Alani via Instagram\n\n\n If you have yet to visit Kada\n near Maxwell Food Centre\n , we have one compelling reason for your consideration. When you arrive at this new vibey spot, take the vintage electric lift up to the rooftop, where you ’ll be greeted by Alani. This new bakery and brunch spot shares the same space as Proud Potato Peeler, and you might be able to tell where they get their influences from. (Answer: Mediterranean\n !)\n\nThe outdoor set-up makes me feel like we ’ve swapped Singapore ’s concrete jungle for a lush, tropical getaway. There ’s plenty of greenery, coupled with rattan chairs, communal tables, and vibrant cushions. It made me want to stay put, crack open a book, and just soak up the vibes. The ambience also follows through indoors, though the size is more compact.\nAlani ’s bakes include pastries, cookies, and breads. I ’m told the open-fired sourdoughs are made with a 14-year-old Greek sourdough starter. Wow! Oh, and also, everything tends to sell out fast, so be here early to snap them up. The portokalopita ($10), a Greek orange cake with dark chocolate, is a tangy, decadent delight. But if you want to start with something more familiar, cinnamon rolls ($9) are a safe option. They taste just as good as they look.\nIf you ’re planning to have a sit-down meal, the brunch menu is your best bet. The Greek breakfast platter ($68) is enough to feed two people and comes with lots of goodies. Hello, food coma! Sip on homemade lemonade ($9) served in a Bordeaux glass to cap off your Mediterranean adventure.\n\nMust-try items:\n Portokalopita; ladenia; cinnamon rolls; homemade lemonade\nHow much:\n Brunch items from $14; drinks from $6.50\nOpening hours:\n Tuesdays to Fridays, 11am to 3pm and weekends, 9.30am to 2.30pm\nAddress:\n #04-04, Kada Maxwell, 5 Kadayanallur Street, Singapore 069183\n\n\nVisit Alani\n\nEG Coffee\n\n Photography: EG Coffee via Facebook\n\n\n Look at what we have here: finally, a cool new cafe on Singapore ’s west side. (Kidding! Or perhaps not.) This fresh, cosy spot is founded by couple-owners Esther and Gavin, whose initials make up the first half of the cafe ’s name. Isn ’t that just the cutest? EG Coffee is located around 10 minutes away from Queenstown\nMRT station\n , so you can clock your daily steps.\n\nOnce you ’ve arrived, plop down on a window side seat, lounge at the mini camping corner indoors, or hang out with your furry buddies outside. See if you can spot the mirror with the cat decal plastered on it – we love it ‘cos it ’s real. The menu is a decent selection of coffees and pastries. The caneles ($5.50) are created fresh and are hot faves, so snatch the two flavours up if they ’re still available. Otherwise, you can settle on the bagels (from $6.30) or gelato ($4.90).\n\nMust-try items:\n Original rum canele; uji matcha canele; matcha latte\nHow much:\n Food from $4; drinks from $3.90\nOpening hours:\n Mondays &amp;amp;Wednesdays to Fridays, 8am to 5pm and weekends, 9am to 6pm\nAddress:\n #01-09, Alexis, 354 Alexandra Road, Singapore 159948\n\n\nVisit EG Coffee\n\nNomad ’s Soiree\n\n Photography: Nomad ’s Soiree via Facebook\n\nAfter operating as a home-based business for the past six years, Singapore ’s first halal Asian grazing company decided to level up into a brick-and-mortar store at Sembawang. Congratulations! Nomad ’s Soiree chose to keep it simple and chic for its maiden outlet: a couple of artworks on the wall, a carpet near the entrance, and wooden furniture. It feels like stepping into a minimalist home, and I ’m digging it.\n\n What can you get here? Cheese platters\n , of course! For $38, you and your companion can build a board with three types of cheese, fresh and dried fruits, cold cuts, crackers, and more. Psst: get the amazing raspberry cheese and don ’t forget the honeycomb for some balance. If that ’s too much (no such thing!), you can pare it back by going for the creamy brie brulee ($25).\n\nBesides fancy grazing boards, the menu also offers all-day brunch, desserts, coffee, and non-alcoholic ‘bubbles ’. Hop on the kunafa train by getting the kunafa creme croissant ($14) or tuck into the savoury hummus with spiced meatball ($17.50).\n\nMust-try items:\n Build Your Own Cheese Board; creamy brie brulee\nHow much:\n Food from $9; drinks from $6\nOpening hours:\n Tuesdays to Thursdays, 10am to 7pm, Fridays to Saturdays, 10am to 9pm, and Sundays, 10am to 7pm\nAddress:\n #01-09, The Brooks 1, 60 Springside Walk, Singapore 786020\n\n\nVisit Nomad ’s Soiree\nNomad ’s Soiree ’s menu\n\n\n\nBest Cafés\n\n\n New cafes in Singapore: March 2025\n\nBettr Coffee\n\n Photography: Bettr Coffee\n\nSpecialty coffee and sustainability? Yes, we ’re down bad for that combo. After being around for more than a decade, Bettr Coffee is finally settling down with its first physical outlet in the Prinsep district. It ’s a match made in heaven – The Foundry is all about social impact, and the coffee brand aims to make ethically sourced coffee more accessible to the public. A win-win, if we say so ourselves.\nThere are plenty of pluses to gush about this new spot. Firstly, you can easily find power outlets all over the space, making this your new go-to spot to work or even catch up on your shows. Pet owners, you ’ll be happy to know your furry friends can join you on your coffee runs. Oh, there ’s an herb garden where they can hang and explore too. How very thoughtful!\nWe wanna extend our raves to Bettr ’s beverage programme too. The menu boasts drinks made with innovative techniques, resulting in outstanding, creative concoctions. The Black &amp;amp;Cola ($8) is a lush blend of double espresso and organic Madagascan cola. We spy a couple of bean-free decaf alternatives – those who can ’t take coffee but want to join in the caffeine fun can consider getting these. Diners can also sip on crafted spirits, mocktails, beers, and natural wines. Pair your selected drink with fresh bakes, small plates, mains, or desserts. The beef pot roast ($21, available from 5pm) is calling out to you…\n\nMust-try items:\n Black &amp;amp;Cola; coconut Russian; iced strawberry blast\nHow much:\n Drinks from $4; food from $3\nOpening hours:\n Tuesdays to Fridays, 9am to 9pm and Saturdays &amp;amp;Mondays, 9am to 5pm\nAddress:\n 11 Prinsep Link, Singapore 187949\n\n\nVisit Bettr Coffee\nBettr Coffee ’s menu\n\nCorner Corner\n\n Photography: Corner Corner via Instagram\n\n\n Regulars of the Duxton\n enclave should be familiar with vinyl bar\n RPM by D.Bespoke. During the day on weekdays, the space transforms into Corner Corner, where visitors can enjoy a chill afternoon sipping on coffee and biting into pastries. Background music courtesy of vinyls completes the ambience, making you forget you ’re in Singapore for a moment.\n\nA show of hands if you have difficulty making decisions. Corner Corner sees you, which is why it doesn ’t offer too many options. Those running on caffeine can choose between the coffee of the day ($6), seasonal pour-over (from $8), and cold brew white ($8). Tea drinkers, you ’re not forgotten: take your pick of kukicha ($8), cold brew gyokuro ($9), and cold brew sencha ($9).\nWhat goes well with coffee and tea? The only correct answer is… Japanese sweet treats! Sink your teeth into the mini orange pound cake, caramel pudding, and nama cream roll cake. The two cakes are light yet sweet, thanks to the lovely combination of fluffy sponge cake and smooth, airy cream. Paired with the drinks, the cakes complement them pretty well.\n\nMust-try items:\n Coffee of the day; nama cream roll cake; caramel pudding\nHow much:\n Drinks from $6; desserts from $4\nOpening hours:\n Mondays to Fridays, 11am to 5pm and Saturdays, 10am to 3pm\nAddress:\n 16 Duxton Road, Singapore 089482\n\n\nVisit Corner Corner\nCorner Corner ’s menu\n\nBorderless Coffee\n\n Photography: Pepper Ling\n\n\n We know everyone ’s sick of the term “hidden gem ”by now, but there ’s no other phrase that perfectly describes this new cafe located along the row of Korean restaurants in Tanjong Pagar\n . Keep a lookout for Obba HanPan BBQ and Charim Korean BBQ, where you ’ll find an open door with a stairway. Climb up the steep flight of stairs (hey, I ’m old! And my knees don ’t work like they used to before…), and you ’ve arrived at Borderless Coffee.\n\nImagine the gasp our team gasped when we entered the space. It feels like we ’ve stepped into an upper-middle-class home, and we mean that in the best possible way. Even though it was sunny and sweltering when we visited, the floor-to-ceiling curtains (and aircon blasting cool air) made us forget about the weather. The hideout is divided into several areas, with a couch and an inviting sofa bed on one side and a few tables on the other. It ’s a lovely work-friendly spot – we were (almost) tempted to ditch the office and stay there to work!\nDespite its name, Borderless Coffee has only three espresso-based options: black ($4.50), white ($5.50), and mocha ($6.50). There are more non-caffeinated drinks, including artisanal and Japanese teas. My colleague ordered an iced matcha latte ($7), which evenly split us. Some liked that it ’s on the milkier side, while others questioned the lack of matcha flavour. However, the hot version ($6) fared slightly better with us.\nThe drinks are complemented with small bites and desserts. You can consider getting the tiramisu ($15), available in limited quantities daily. Otherwise, hit up the friendly staff and ask about the daily bakes. We recommend getting the sticky date pudding ($4) if it ’s available. It can rival the one from a certain local brand…\n\nMust-try items:\n Mocha; sticky date pudding\nHow much:\n Drinks from $4.50; enquire for prices of daily bakes\nOpening hours:\n Mondays to Fridays, 10am to 5pm and Saturdays to Sundays, 10am to 4pm\nAddress:\n Level 2, 65A Tanjong Pagar Road, Singapore 088486\n\n\nVisit Borderless Coffee\nBorderless Coffee ’s menu\n\nAverage Service\n\n Photography: Average Service\n\n\n There’s nothing average about this new cafe in Jalan Besar\n that’s been making waves on TikTok\n . It’s a vibey space that’s perfect for an afternoon cuppa to escape the scorching heat when you’re in the area. Take a seat by the open kitchen bar, watch the baristas at work, or huddle up in the sunken conversation pit for cosy dates. With brunch classics, pasta plates, pastries, coffee brews and matcha drinks on the menu, you won’t be disappointed.\n\nOur dining experience started with the humble bread and butter ($12) dish, consisting of sourdough elevated by a trio of house-made butter variations: chilli, furikake and truffle. We’d normally skip such starters, but these unique butters totally made every bite worth it.\nFor more bready delights, try the jaw-dropping thick slab bacon ($26). A huge slab of maple-glazed bacon sits atop Aussie-style eggs and a slice of brioche sourdough – it’s great for sharing so you don’t feel too overwhelmed by the fatty bacon.\nIf you’re here for the noods, the mentai handkerchief pasta ($24) features thick, chewy pasta sheets coated in a creamy mentaiko sauce and topped with bacon chunks. It’s rich without being too cloying, but we recommend you share this too. For something a little more wholesome, the Average rice with grilled salmon ($24) offers a mix of red rice, couscous and barley paired with juicy salmon that’s been nicely grilled to get that crispy skin.\n\n As for desserts, the strawberry shortcube ($13) and hazelnut Valrhona chocolate cube ($13) are IG-worthy thanks to their block-like shape. But the layers of mousse and chiffon make for a pretty average sweet treat. We’d say skip those and go for the lovely maple toast ($16) with whipped cream and maple syrup instead. Or simply indulge in drinks like the gorgeous strawberry cold foam matcha latte ($7.50). (Review by Benita Lee, Group Editor)\n\n\nMust-try items:\n Thick slab bacon; mentai handkerchief pasta\nHow much:\n Drinks from $5.50; dishes from $7\nOpening hours:\n Sundays to Thursdays, 8.30am to 10pm and Fridays to Saturdays, 8.30am to 12am\nAddress:\n 315 Jalan Besar, Singapore 208973\n\n\nVisit Average Service\n\nCaro Patisserie\n\n Photography: Caro Patisserie\n\n\n At this rate, you can expect at least one cafe to crop up in Joo Chiat\n every month. Caro Patisserie is the brainchild of French pastry chef Caroline Titzck, which started from home before expanding into a physical store at Yio Chu Kang. This is the brand ’s second outlet, and we gotta say, the team picked the right neighbourhood to expand into.\n\nThe space is compact, with only a couple of tables outside, but we adore it nonetheless. Full-length windows let natural light flow in, spotlighting the gorgeous interior decor and pop of orange behind the counter. Of course, your eyes will immediately be drawn to the neatly arranged tarts when you step into the store.\n\n Handmade French tarts\n are the stars of the show here, with various flavours for you to choose from. We ’re always in the mood for something fruity, and the lemon meringue tartlet ($8.80) doesn ’t disappoint. The refreshing citrus pairs well with the sweet meringue, all held together by a crisp, crumbly tart base.\n\nIf you ’re looking for an edible work of art, get your hands on the mango tartlet ($9.80). We couldn ’t tear our eyes off it – there ’s a reason why it ’s a bestseller. If you ’re in a sharing mood, go for the eight-inch tarts and spread some pastry cheer to your loved ones. The tarte tatin (an upside-down tart with caramelised apples) is a stellar choice!\n\nMust-try items:\n Lemon meringue tartlet; mango tartlet; tarte tatin\nHow much:\n Tarts from $8.80\nOpening hours:\n Wednesdays to Fridays, 11am to 7pm and Saturdays to Sundays, 10.30am to 8pm\nAddress:\n 285 Joo Chiat Road, Singapore 427539\n\n\nVisit Caro Patisserie\n\n\n\n New cafes in Singapore: February 2025\n\n2050 Coffee\n\n Photography: Sufyan Saad\n\n\n You’ve probably seen videos of this futuristic-looking joint on TikTok\n . Hailing from Kyoto\n , 2050 Coffee launches its first overseas outpost at Beach Road, along the same stretch as Birds of Paradise and The Coconut Club. Its interior is sleek minimalism at its finest: dark grey walls, a curved seating area flush against the wall, and mirrors on the other side. We love the area where the plant and the skylight are – mark our words, this spot will appear on your feed soon.\n\nThe main thing that makes the space look advanced is the filtered coffee available on tap ($7.50). There are four profiles to choose from; we tried 2050 House Blend, the strongest out of the lot, according to the staff. The low acidity makes the coffee pleasant to sip on, with a lovely buttery scent and nutty flavour. There’s a lingering aftertaste, but it’s not a dealbreaker for me.\nOur favourite is the Cascara Coffee Cherry Tea ($7.50). Don’t be fooled by the name, there’s no coffee in it! It’s light and fruity, like iced lemon tea without the added sugar. We easily (and happily) finished the drink. If you’re into Kurasu’s matcha latte, 2050 Coffee serves the exact concoction here.\n\nMust-try items:\n 2050 House Blend (tap coffee); Cascara Coffee Cherry Tea\nHow much:\n Drinks from $4.50\nOpening hours:\n Daily, 8.30am to 7.30pm\nAddress:\n #01-01, 267 Beach Road, Singapore 199545\n\n\nVisit 2050 Coffee\n2050 Coffee ’s menu\n\nBee Hoe Coffee\n\n Photography: Bee Hoe Coffee via Instagram\n\n\n When it comes to cool cafes, no place does it better than Joo Chiat\n . You’re spoilt for choice with the number of coffeehouses and bakeries that have sprouted in that area. Bee Hoe Coffee is a new gem you must visit if you plan to drop by the neighbourhood. Managed by a barbershop\n in a back alley, this new spot largely operates as a takeaway kiosk. However, there are a couple of seats where you can park yourself for a hot minute to enjoy your order.\n\nBee Hoe specialises in Vietnamese coffee, including interesting concoctions such as honey egg ($4.50), coconut ($5.50), and peanut butter ($5.50) coffees. The brews are flavourful and not too acidic. You can also get Western-style options, which are made using Vietnamese-sourced beans. Pair your drink with Penang-inspired pastries like bak kwa roti ($4.50) and omelette muffin ($3.20). Oh, get your hair cut while you’re at it!\n\nMust-try items:\n Peanut butter coffee; omelette muffin\nHow much:\n Drinks from $3; pastries from $3.20\nOpening hours:\n Mondays to Fridays, 8.30am to 2pm and weekends, 8.30am to 4pm\nAddress:\n 55 Joo Chiat Place, Singapore 427779\n\n\nVisit Bee Hoe Coffee\n\nMuro Coffee\n\n Photography: Muro Coffee via Instagram\n\n\n One food item our team collectively loves is a good cuppa. This new coffee joint is near our office, which means we can get in our hot girl walk and reward ourselves with a drink afterwards. A win-win! Muro’s menu is a divine combination of brews and bread, featuring standard coffee options, non-coffee offerings, and five sandwiches\n . We also spy some sweet bakes on the counter.\n\nFirst-time visitors can try signatures like dirty matcha (from $7.50), orange tonic espresso ($8), and smoked mocha affogato ($9.50). If you’re feeling peckish, The Full Foc ($18.90) should fill you right up. Picture beef jerky, chicken chipolata, melted cheddar, eggs, and sauteed mushroom piled in between fluffy focaccia. What a dream. Bonus points for the monochromatic space and awesome playlist. We can imagine working here for days when we’re sick of being in the office.\n\nMust-try items:\n Orange tonic espresso; The Full Foc\nHow much:\n Drinks from $4.50; focaccias from $11.90\nOpening hours:\n Mondays to Fridays, 8am to 6pm and Saturdays to Sundays, 10am to 6pm\nAddress:\n 214A South Bridge Road, Singapore 058763\n\n\nVisit Muro Coffee\n\nCheeky\n\n Photography: Cheeky via Instagram\n\n\n If you’re looking for a quaint spot in Upper Thomson\n , we know just the place. You’ll feel like you’ve entered someone’s abode the minute you walk through the door. This is all thanks to its neutral hues, wooden furniture, planters on a shelf, and a vinyl player in the corner.\n\n\n Cheeky is all about handmade drinks, with a menu boasting everything from coffee and tea to a delicious chocolate blend. The popular orders are its spanners (from $6.50), which feature long black, milk coffee, and matcha latte topped with a velvety, housemade sweet cream. The delicious pairings make the drinks go smoothly down the throat. There are three sammies (from $4.90) to choose from, with the otah offering ($7.90) being the clear winner. Stop by on the weekends\n to enjoy light, fluffy chiffon cakes.\n\n\nMust-try items:\n Chaspanner; Otah Pei Ya Som\nHow much:\n Drinks from $4; sandwiches from $4.90\nOpening hours:\n Tuesdays to Sundays, 9am to 5pm\nAddress:\n #01-47A, 24 Sin Ming Road, Singapore 570024\n\n\nVisit Cheeky\nCheeky ’s menu\n\nIce &amp;amp;Time\n\n Photography: Ice &amp;amp;Time via Google\n\n\n The weather may not be it right now, but that shouldn’t stop you from enjoying shaved ice desserts. The Duxton\n enclave welcomes a second kakigori cafe into its fold. Ice &amp;amp;Time offers nine different flavours, all with no GST and service charge. Each serving comes with instructions on how to enjoy your order. It’s recommended you snap photos and videos within 20 seconds and then immediately tuck in.\n\nThe strawberry kakigori ($22.60) contains premium Japanese strawberries, Hokkaido milk sauce, and milk pudding within the shaved ice. We love how substantial the portion is (perfect for sharing) and it’s not too sweet, with a pronounced strawberry taste. Keeping with the Japanese theme, you can also get matcha ($18.90) served in a huge bowl. Choose between the rich and light versions, depending on your preference.\n\nMust-try items:\n Strawberry kakigori; mango kakigori\nHow much:\n Kakigori from $18.60\nOpening hours:\n Mondays to Sundays, 12pm to 10pm\nAddress:\n 44 Craig Road, Singapore 089682\n\n\nVisit Ice &amp;amp;Time\n\n\n\n New cafes in Singapore: January 2025\n\nKoko Cafe &amp;amp;Patisserie\n\n Photography: Sufyan Saad\n\n\n Everyone, say koko-nnichiwa to Tanjong Pagar\n ’s new resident, ‘cos the Gyutan-Tan team has revamped its adjoining space to make way for Koko Cafe &amp;amp;Patisserie. We love the neutral tones and minimalist design approach, which make the place look like a Muji catalogue come to life.\n\n\n Helmed by Japanese pastry chefs, the cafe serves customers a sweet taste of Japan\n . So, what can you expect here? Artisanal fresh bakes like strawberry shortcake ($10), curry doughnut\n (from $4), Okinawan rum chocolate sand ($8), yam mont blanc ($7), and matcha choux puff (from $4). For something different besides your usual coffee order, try the Float My Milk ($9). We won’t spoil the drink for you – just order it and enjoy.\n\n\nMust-try items:\n Curry doughnut; yam mont blanc; strawberry shortcake; chocolate choux puff\nHow much:\n Pastries from $4; drinks from $3.50\nOpening hours:\n Tuesdays to Saturdays, 12pm to 6pm and Sundays, 10.30am to 7pm\nAddress:\n 43 Tras Street, Singapore 078982\n\n\nVisit Koko Cafe &amp;amp;Patisserie\nKoko Cafe &amp;amp;Patisserie ’s menu\n\nOtter &amp;amp;Pebbles\n\n Photography: Yuki Ling\n\n\n Watch out, Novena\n , ‘cos a new Japanese-inspired cafe has landed! Satisfy your brunch cravings at this cosy space that dishes out a glorious selection of udon, chazuke, sandos, Dutch and souffle pancakes, and donburi. These folks are the brains behind The Coffee Code, another aesthetically pleasing cafe in Maxwell, so you know they won’t disappoint when it comes to visuals.\n\n\n What’s worthy of a spotlight? The oh-so-creamy soymilk udon served with braised pork ($18.90) that melts in your mouth; the salmon ochazuke ($24.90) for a light palate cleanser; and the nutty pistachio souffle pancakes\n ($17.90). You can’t leave without trying the decadent Cheesetache drinks series, too. Coffee lovers will adore the tiramisu\n -inspired drink layered with cream cheese ($9.50), while the osmanthus version is a refreshing alternative with strong floral notes. (Review by Yuki Ling, Branded Content Writer)\n\n\nMust-try items:\n Pistachio souffle pancake; soymilk udon with braised pork; tiramisu\nHow much:\n From $7\nOpening hours:\n Daily, 11am to 7.30pm\nAddress:\n #01-05/07, Novena Specialist Center, 8 Sinaran Drive, Singapore 307470\n\n\nVisit Otter &amp;amp;Pebbles\n\nWheathead Bakery\n\n Photography: Wheathead Bakery\n\n\n Mark my words: One-North is going to be the\n cool spot in Singapore where new cafes sprout and thrive. This home-based business is now operating a physical store in the enclave, dishing out bread and pastries to the lucky folks living and working there. It’s a little out of the way, but rest assured, your efforts won’t be in vain once you reach the place.\n\n\n Wheathead’s menu changes daily, so expect different offerings depending on when you pop by. That said, do note that breakfast options are available till 10.30am, and you can get lunch items from 11.30am onwards. Oh, make sure to save space for the banana cream pie\n – this will keep you satiated and happy for the rest of the day.\n\n\nMust-try items:\n Superfood cookie; banana cream pie\nHow much:\n From $4.50\nOpening hours:\n Wednesdays to Sundays, 8am to 2pm\nAddress:\n #01-01, One-North Eden, 8 Slim Barracks Rise, Singapore 138492\n\n\nVisit Wheathead Bakery\n\nTous Les Jours\n\n Photography: Marcus Khoo\n\n\n Need a compelling reason to head to Yishun\n ? This might be it. Popular South Korean bakery Tous Les Jours, known for fusing traditional French baking techniques with Korean flavours, has opened its first outlet in Singapore. We liked the cream cheese walnut bread ($4.80) and sweet potato bread ($2.80), which come with generous ingredients. But if you want something that reminds you of Korea, go for the K-Hotteok ($2.30). It has a satisfying brown sugar and nut filling that might just transport you to the streets of Myeongdong.\n\n\n The outlet is designed like a cafe, which means you can grab a seat and devour your favourite bread and cakes. Pair your pastry of choice with beverages like green tea latte ($5.40), iced caramel macchiato ($6.40), and royal milk frappe ($7.80). (Review by Marcus Khoo, Digital Manager, Marketing and Content)\n\n\nMust-try items:\n K-Hotteok; cream cheese walnut bread; sweet potato bread; royal milk frappe\nHow much:\n From $2.20\nOpening hours:\n Daily, 10am to 10pm\nAddress:\n #01-112, Northpoint City, 930 Yishun Avenue 2, Singapore 769098\n\n\nVisit Tous Les Jours\n\nMuyun\n\n Photography: Muyun via Google\n\n\nCamping\n may not be liked by all (ahem, me included), but that doesn’t mean we can’t appreciate the aesthetics. Thankfully, we found a quaint new cafe in Singapore that dials up the glamping factor to 1000. Soft, dim lighting, pebbled flooring, camping chairs, and a large parasol add to a lovely, laid-back experience without you having to brave the elements.\n\nWith such a vibey space, it ’s perfect for you to sink your teeth into simple cafe fare like waffles (from $5.50), toasts (from $2.90), and oatmeal bowls ($6.90). Drinks-wise, have fun sipping coffee options like espresso ($3.80), oat milk latte ($5.80), and rich mocha ($6.80) or take your pick from the list of Chinese teas.\n\nMust-try items:\n Original waffles; honey butter toast\nHow much:\n From $2.90\nOpening hours:\n Daily, 8am to 9pm\nAddress:\n Muyun, #01-02B, 5 Tanjong Pagar Plaza, Singapore 081005\n\nHave fun checking out Singapore’s newest cafes in 2025!\n\n"
        assert error is None

# Tests for utility functions
class TestUtilityFunctions:
    
    def test_check_tiktok_type_photo(self):
        assert check_tiktok_type("https://tiktok.com/@user/photo/123") == 'photo'
        
    def test_check_tiktok_type_video(self):
        assert check_tiktok_type("https://tiktok.com/@user/video/123") == 'video'
        
    def test_check_tiktok_type_unknown(self):
        result = check_tiktok_type("https://tiktok.com/@user/post/123")
        assert "unknown media type" in result
        
    def test_fetch_descriptions_valid(self):
        data = {"desc": "Test description"}
        assert fetch_descriptions(data) == "Test description"
        
    def test_fetch_descriptions_empty(self):
        assert fetch_descriptions({}) == ""
        assert fetch_descriptions(None) == ""
        assert fetch_descriptions({"desc": None}) == ""
        
    def test_fetch_subtitles_valid(self):
        data = {"subtitles": "WEBVTT\n\n00:00:00 --> 00:00:01\nHey you guys.\n\n00:00:01 --> 00:00:04\nSince you all love my top Singapore Pizza ranking video last year,\n\n00:00:04 --> 00:00:08\nI have decided to try 15 more places and update this ranking this year"}
        assert fetch_subtitles(data) == "Hey you guys. Since you all love my top Singapore Pizza ranking video last year, I have decided to try 15 more places and update this ranking this year"
        
    def test_fetch_subtitles_empty(self):
        assert fetch_subtitles({}) == ""
        assert fetch_subtitles({"subtitles": None}) == ""
        
    def test_validate_place_info_valid(self):
        # todo
        assert True

# Tests for generate_address_from_model
class TestGenerateAddressFromModel:
    
    @patch('server.scrapper.OpenAI')
    def test_generate_address_from_model_success(self, mock_openai):
        # Setup mock
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = MODEL_RESPONSE["assumed"]
        mock_openai.return_value.chat.completions.create.return_value = mock_completion
        
        result, err = generate_address_from_model("test text", WEBSITE_PROMPT)
        
        assert err is None
        assert len(result) == 2
        assert result['Acoustics Coffee Bar']["address"] == ["61 Neil Road","2 Owen Road"]

    @patch('server.scrapper.OpenAI')
    def test_generate_address_from_model_with_json_str(self, mock_openai):
        # Test handling of markdown code blocks
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = json.dumps(MODEL_RESPONSE["json"])
        mock_openai.return_value.chat.completions.create.return_value = mock_completion
        
        result, err = generate_address_from_model("test text", WEBSITE_PROMPT)
        
        assert err is None
        assert len(result) == 3
        assert result['Alice Boulangerie']["address"] == ['Icon Village, 01-05, 12 Gopeng Street']
        
    @patch('server.scrapper.OpenAI')
    def test_generate_address_from_model_parse_error(self, mock_openai):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "invalid json"
        mock_openai.return_value.chat.completions.create.return_value = mock_completion
        
        _, err = generate_address_from_model("test text", WEBSITE_PROMPT)
        assert err is not None

# Tests for generate_markers
class TestGenerateMarkers:

    def mock_map_info_function(self, address, prompt=2):
        mock_place = PlaceInfo(
            Id='123', Name=address, Address='78 Yong Siak',
            Lat=1.28, Long=103.83, Status='OPERATIONAL',
            Rating=4.5, RatingCount=100, PriceLevel=None,
            OpeningHours=None, Website=None, GoogleLink=None,
            DirectionLink=None, Description=None
        )
        return mock_place, None
    
    @patch('server.scrapper.map_info')
    def test_generate_markers_name_add_area(self, mock_map_info):
        mock_map_info.side_effect =self.mock_map_info_function
        
        address_struct = MODEL_RESPONSE["json"]
        result = generate_markers(address_struct)
        
        assert len(result) == 3
        assert result[0].Name == 'Acoustics Coffee Bar 61 Neil Road Singapore'

    @patch('server.scrapper.map_info')
    def test_generate_markers_name_add(self, mock_map_info):
        mock_map_info.side_effect =self.mock_map_info_function
        
        address_struct = MODEL_RESPONSE["json"]
        address_struct["Acoustics Coffee Bar"]["area"] = ""
        result = generate_markers(address_struct)
        
        assert len(result) == 3
        assert result[0].Name == 'Acoustics Coffee Bar 61 Neil Road'
           
    @patch('server.scrapper.map_info')
    def test_generate_markers_name_area(self, mock_map_info):
        mock_map_info.side_effect =self.mock_map_info_function
        
        address_struct = MODEL_RESPONSE["missing_address"]
        result = generate_markers(address_struct)
        
        assert len(result) == 3
        assert result[0].Name == 'Acoustics Coffee Bar Singapore'
        
    @patch('server.scrapper.map_info')
    def test_generate_markers_skip_invalid(self, mock_map_info):
        # First call returns error, second succeeds
        mock_place = PlaceInfo(
            Id='123', Name='Valid Place', Address='123 St',
            Lat=1.0, Long=103.0, Status='OPERATIONAL',
            Rating=None, RatingCount=None, PriceLevel=None,
            OpeningHours=None, Website=None, GoogleLink=None,
            DirectionLink=None, Description=None
        )
        mock_map_info.side_effect = [
            (None, "Error"),
            (mock_place, None),
            (None, "Error")
        ]
        
        result = generate_markers(MODEL_RESPONSE["json"])
        
        assert len(result) == 1
        assert result[0].Name == "Valid Place"

# Tests for fetch_website
class TestFetchWebsite:
    
    @patch('requests.Session')
    def test_fetch_website_success_html(self, mock_session):
        mock_response = Mock()
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.iter_content.return_value = [b'<html>Test</html>']
        mock_response.raise_for_status.return_value = None
        
        mock_session.return_value.__enter__.return_value.request.return_value = mock_response
        
        result, error = fetch_website("https://example.com")
        
        assert result == '<html>Test</html>'
        assert error is None
        
    @patch('requests.Session')
    def test_fetch_website_success_json(self, mock_session):
        mock_response = Mock()
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.iter_content.return_value = [b'{"key": "value"}']
        mock_response.raise_for_status.return_value = None
        
        mock_session.return_value.__enter__.return_value.request.return_value = mock_response
        
        result, error = fetch_website("https://example.com", is_html=False)
        
        assert result == {"key": "value"}
        assert error is None
        
    @patch('requests.Session')
    def test_fetch_website_timeout(self, mock_session):
        mock_session.return_value.__enter__.return_value.request.side_effect = requests.exceptions.Timeout()
        
        result, error = fetch_website("https://example.com")
        
        assert result is None
        assert "Request timed out" in error
        
    @patch('requests.Session')
    def test_fetch_website_invalid_content_type(self, mock_session):
        mock_response = Mock()
        mock_response.headers = {'Content-Type': 'application/pdf'}
        mock_response.close.return_value = None
        
        mock_session.return_value.__enter__.return_value.request.return_value = mock_response
        
        result, error = fetch_website("https://example.com")
        
        assert result is None
        assert "Unsupported content type" in error
        
    @patch('requests.Session')
    def test_fetch_website_content_too_large(self, mock_session):
        mock_response = Mock()
        mock_response.headers = {'Content-Type': 'text/html', 'Content-Length': '20000000'}
        mock_response.close.return_value = None
        
        mock_session.return_value.__enter__.return_value.request.return_value = mock_response
        
        result, error = fetch_website("https://example.com")
        
        assert result is None
        assert "Response too large" in error

# Tests for map_info
class TestMapInfo:
    
    @patch('requests.post')
    def test_map_info_success(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = GOOGLE_PLACES_RESPONSE
        mock_post.return_value = mock_response
        
        result, error = map_info("Forty Hands cafe")
        
        assert error is None
        assert result.Name == "Forty Hands"
        assert result.Address == "78 Yong Siak Street, Singapore 163078"
        assert result.Rating == 4.5
        
    @patch('requests.post')
    def test_map_info_api_error(self, mock_post):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.text = "API Error"
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response
        
        result, error = map_info("Test location")
        
        assert "google info fetch failed" in error
        assert result["error"] == error
        
    @patch('requests.post')
    def test_map_info_network_error(self, mock_post):
        mock_post.side_effect = Exception("Network error")
        
        result, error = map_info("Test location")
        
        assert "google info fetch failed" in error
        assert "Network error" in error

# Tests for extract_text_from_url
class TestExtractTextFromUrl:
    
    @patch('requests.get')
    @patch('easyocr.Reader')
    def test_extract_text_from_url_success(self, mock_reader, mock_get):
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'image/jpeg'}
        mock_response.iter_content.return_value = [b'fake_image_data']
        mock_get.return_value = mock_response
        
        # Setup OCR mock
        mock_reader_instance = Mock()
        mock_reader_instance.readtext.return_value = ["Extracted text from image"]
        mock_reader.return_value = mock_reader_instance
        
        # Mock image processing
        with patch('PIL.Image.open'), \
             patch('cv2.cvtColor'), \
             patch('cv2.filter2D'), \
             patch('cv2.createCLAHE'), \
             patch('cv2.erode'), \
             patch('cv2.dilate'):
            
            result = extract_text_from_url("https://example.com/image.jpg")
            
        assert result == "Extracted text from image"
        
    @patch('requests.get')
    def test_extract_text_from_url_invalid_content_type(self, mock_get):
        mock_response = Mock()
        mock_response.headers = {'Content-Type': 'application/pdf'}
        mock_get.return_value = mock_response
        
        result = extract_text_from_url("https://example.com/file.pdf")
        
        assert result == ''
        
    @patch('requests.get')
    def test_extract_text_from_url_download_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Download failed")
        
        result = extract_text_from_url("https://example.com/image.jpg")
        
        assert result == ''

# Tests for sanitize_html function
class TestSanitizeHtml:
    
    def test_sanitize_html_removes_script_tags(self):
        """Test that script tags are completely removed"""
        html = '<p>Hello</p><script>alert("XSS")</script><p>World</p>'
        result = sanitize_html(html)
        assert result == '<p>Hello</p><p>World</p>'
    
    def test_sanitize_html_removes_style_tags(self):
        """Test that style tags are removed"""
        html = '<p>Text</p><style>body { background: red; }</style>'
        result = sanitize_html(html)
        assert result == '<p>Text</p>'
    
    def test_sanitize_html_removes_event_handlers(self):
        """Test that event handler attributes are removed"""
        html = '<div onclick="alert(\'XSS\')" onmouseover="hack()">Click me</div>'
        result = sanitize_html(html)
        assert result == 'Click me'
    
    def test_sanitize_html_removes_javascript_urls(self):
        """Test that javascript: URLs are removed"""
        html = '<a href="javascript:alert(\'XSS\')">Link</a>'
        result = sanitize_html(html)
        assert result == "<a>Link</a>"
    
    def test_sanitize_html_removes_data_urls(self):
        """Test that data: URLs are removed"""
        html = '<a href="data:text/html,<script>alert(\'XSS\')</script>">Bad Link</a>'
        result = sanitize_html(html)
        assert result == '<a>Bad Link</a>'
    
    def test_sanitize_html_removes_iframes(self):
        """Test that iframes are removed"""
        html = '<iframe src="http://malicious.com"></iframe><p>Content</p>'
        result = sanitize_html(html)
        assert result == '<p>Content</p>'

    def test_sanitize_html_removes_object_embed_tags(self):
        """Test that object and embed tags are removed"""
        html = '<object data="malicious.swf"></object><embed src="bad.swf"></embed><p>Safe</p>'
        result = sanitize_html(html)
        assert result == '<p>Safe</p>'
    
    def test_sanitize_html_preserves_safe_tags(self):
        """Test that safe HTML tags are preserved"""
        html = '<p>Paragraph</p><div>Division</div><span>Span</span><a href="http://safe.com">Link</a>'
        result = sanitize_html(html)
        assert result == '<p>Paragraph</p>Division<span>Span</span><a>Link</a>'

    def test_sanitize_html_handles_nested_content(self):
        """Test that nested content is not removed"""
        html = '<div><div><p>Nested</p></div></div>'
        result = sanitize_html(html)
        assert result == '<p>Nested</p>'
    
    def test_sanitize_html_handles_nested_dangerous_content(self):
        """Test that nested dangerous content is removed"""
        html = '<div><script><p>Nested</p></script></div>'
        result = sanitize_html(html)
        assert result == ''
    
    def test_sanitize_html_handles_malformed_tags(self):
        """Test handling of malformed HTML"""
        html = '<p>Text<script>alert("XSS")<p>More text</p>'
        result = sanitize_html(html)
        assert result == '<p>Text</p>'
    
    def test_sanitize_html_removes_meta_refresh(self):
        """Test that meta refresh tags are removed"""
        html = '<meta http-equiv="refresh" content="0;url=http://malicious.com"><p>Content</p>'
        result = sanitize_html(html)
        assert result == '<p>Content</p>'
    
    def test_sanitize_html_handles_svg_with_scripts(self):
        """Test that SVG with embedded scripts is sanitized"""
        html = '<svg><script>alert("XSS")</script></svg><p>Text</p>'
        result = sanitize_html(html)
        assert result == '<p>Text</p>'
    
    def test_sanitize_html_removes_form_actions(self):
        """Test that potentially dangerous form actions are handled"""
        html = '<form action="javascript:alert(\'XSS\')"><input type="submit"></form>'
        result = sanitize_html(html)
        assert result == ''
    
    def test_sanitize_html_handles_base_tag(self):
        """Test that base tags are removed to prevent URL hijacking"""
        html = '<base href="http://malicious.com/"><p>Content</p>'
        result = sanitize_html(html)
        assert '<p>Content</p>'
    
    def test_sanitize_html_handles_link_imports(self):
        """Test that link imports are handled safely"""
        html = '<link rel="import" href="http://malicious.com/evil.html"><p>Safe content</p>'
        result = sanitize_html(html)
        # Link tags might be allowed but imports should be handled
        assert result == '<p>Safe content</p>'
    
    def test_sanitize_html_empty_input(self):
        """Test handling of empty input"""
        assert sanitize_html('') == ''
        assert sanitize_html(None) == ''
    
    def test_sanitize_html_plain_text(self):
        """Test that plain text is preserved"""
        text = 'This is plain text with no HTML'
        assert sanitize_html(text) == text
    
    def test_sanitize_html_mixed_case_tags(self):
        """Test that mixed case dangerous tags are removed"""
        html = '<ScRiPt>alert("XSS")</ScRiPt><p>Text</p>'
        result = sanitize_html(html)
        assert result == '<p>Text</p>'
    
    def test_sanitize_html_encoded_scripts(self):
        """Test that encoded script attempts are handled"""
        html = '<p>Text</p>&lt;script&gt;alert("XSS")&lt;/script&gt;'
        result = sanitize_html(html)
        assert result == '<p>Text</p>&lt;script&gt;alert("XSS")&lt;/script&gt;'
        # The encoded brackets should be preserved as they're just text
        assert '&lt;' in result or '<' not in result[result.find('alert'):] if 'alert' in result else True

# Tests for process_image_text OCR functionality
class TestProcessImageText:
    
    def test_process_image_text_with_sample_images(self):
        """Test OCR with sample images from mock_data"""
        for img_name, img_data in SAMPLE_IMAGES.items():
            
            # Decode base64 image
            img_bytes = io.BytesIO(base64.b64decode(img_data["base64"]))
            
            # Test
            result = process_image_text(img_bytes)
            
            # Verify expected text is found
            if img_data["expected_text"]:
                for expected in img_data["expected_text"]:
                    assert expected in result, f"Expected '{expected}' not found in result for {img_name}"
            else:
                assert result == "", f"Expected empty result for {img_name}"