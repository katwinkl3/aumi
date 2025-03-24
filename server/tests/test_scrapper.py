import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock, mock_open
import requests
from bs4 import BeautifulSoup
from scrapper import PlaceInfo, ApiResponse
from test_data import MapInfo


# mock google maps api responses to test map_info
@pytest.fixture
def mock_google_maps():
    """Mock the Google Maps API responses"""
    with patch('scrapper.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = MapInfo
        mock_get.return_value = mock_response
        yield mock_get

def test_map_info(mock_google_maps):
    """Test the map_info function"""
    address = "Flag White 106 Jalan Jurong Kechil"
    result = scrapper.map_info(address)
    assert isinstance(result, PlaceInfo)
    assert result.Id == "ChIJCaXKGjAR2jERV2b3bf4hj6Q"
    assert result.Name == "FlagWhite"
    assert result.Address == "106 Jln Jurong Kechil, Singapore"
    assert result.Lat == 1.3408725
    assert result.Long == 103.77243779999999
    assert result.Status == "OPERATIONAL"
    assert result.Rating == 4.5
    assert result.RatingCount == 1014
    assert result.PriceLevel == "MODERATE"
    assert result.Website == "https://www.flagwhitecafe.com/"
    assert result.GoogleLink == "https://maps.google.com/?cid=11857733720540145239"
    assert result.DirectionLink == "https://www.google.com/maps/dir//''/data=!4m7!4m6!1m1!4e2!1m2!1m1!1s0x31da11301acaa509:0xa48f21fe6df76657!3e0"

def test_map_info_error(mock_google_maps):
    """Test the map_info function with an error response"""
    address = "Test Business 123 Main St, City, State"
    mock_google_maps.return_value.ok = False
    mock_google_maps.return_value.text = "Error"
    result = scrapper.map_info(address)
    assert result is None

def test_map_info_empty_response(mock_google_maps):
    """Test the map_info function with an empty response"""
    address = "Test Business 123 Main St, City, State"
    mock_google_maps.return_value.json.return_value = {"places": []}
    result = scrapper.map_info(address)
    assert result is None


# mock request.args.get("url")
@pytest.fixture
def mock_flask_request():
    """Create a mock Flask request object"""
    with patch('scrapper.request') as mock_request:
        mock_request.args.get("url").return_value = "https://hungrygowhere.com/what-to-eat/best-cafes-in-singapore/"
        yield mock_request

# # mock requests.get
# @pytest.fixture
# def mock_requests_get():
#     """Mock the requests.get function"""
#     with patch('scrapper.requests.get') as mock_get:
#         mock_response = MagicMock()
#         mock_response.ok = True
#         mock_response.text = "<html><body><p>Test Address: 123 Main St, City, State</p></body></html>"
#         mock_get.return_value = mock_response
#         yield mock_get

@pytest.fixture
def mock_openai_client():
    """Mock the OpenAI client"""
    with patch('scrapper.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        
        mock_message.content = '{"Business Name": ["123 Main St, City, State"]}'
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client
        
        yield mock_openai


def test_scrape_address(mock_flask_request, mock_openai_client):
    """Test the scrape_address function"""
    with patch('scrapper.generate_address') as mock_generate_address:
        # mock_generate_address.return_value = {"Business Name": ["123 Main St, City, State"]}
        
        result = scrapper.scrape_address()
        
        mock_flask_request.args.get.assert_called_once_with("url")
        mock_requests_get.assert_called_once()
        mock_generate_address.assert_called_once()
        
        assert result.Code == 200
        assert result.Msg == "success"
        print('test_scrape_address')
        print(result.Data)
        # assert result.Data == {"Business Name": ["123 Main St, City, State"]}

def test_scrape_address_error(mock_flask_request, mock_requests_get):
    """Test the scrape_address function with an error response"""
    mock_requests_get.return_value.ok = False
    mock_requests_get.return_value.status_code = 404
    mock_requests_get.return_value.text = "Not Found"
    
    result = scrapper.scrape_address()
    
    assert result.Code == 404
    assert result.Msg == "failed to retrieve page"
    assert result.Data == {}

def test_generate_address(mock_openai_client):
    """Test the generate_address function"""
    text = HtmlText
    result = scrapper.generate_address(text)
    mock_openai_client.assert_called_once()
    assert result == {"Business Name": ["123 Main St, City, State"]}

def test_generate_address_error(mock_openai_client):
    """Test the generate_address function with an error"""
    text = "Business Name: 123 Main St, City, State"
    
    # Set up the mock to return invalid JSON
    mock_openai_client.return_value.chat.completions.create.return_value.choices[0].message.content = "invalid json"
    
    with pytest.raises(Exception):
        scrapper.generate_address(text)

