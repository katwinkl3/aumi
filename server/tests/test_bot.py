import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
from telegram import Update, User, Chat, Message, InlineKeyboardMarkup
import bot

@pytest.fixture
def mock_update():
    """Create a mock Update object for testing"""
    update = MagicMock(spec=Update)
    user = MagicMock(spec=User)
    chat = MagicMock(spec=Chat)
    message = MagicMock(spec=Message)
    
    # Configure user mock
    user.id = 12345
    user.is_bot = False
    user.first_name = "Test"
    user.last_name = "User"
    user.username = "testuser"
    user.language_code = "en"
    
    # Configure chat mock
    chat.id = 12345
    chat.type = "private"
    chat.title = None
    
    # Configure message mock
    message.message_id = 67890
    message.text = "Test message"
    message.date.isoformat.return_value = "2023-01-01T12:00:00"
    message.reply_text = AsyncMock()
    
    # Link mocks together
    update.effective_user = user
    update.effective_chat = chat
    update.effective_message = message
    update.message = message
    
    return update

@pytest.fixture
def mock_context():
    """Create a mock context for testing"""
    return MagicMock()

@pytest.mark.asyncio
async def test_start_command(mock_update, mock_context):
    """Test the start_command function"""
    with patch('bot.save_user') as mock_save_user, \
         patch('bot.get_user_info') as mock_get_user_info, \
         patch('bot.InlineKeyboardMarkup') as mock_keyboard_markup:
        
        # Configure mocks
        mock_get_user_info.return_value = {
            "user_id": 12345,
            "first_name": "Test"
        }
        
        # Call the function
        await bot.start_command(mock_update, mock_context)
        
        # Assertions
        mock_save_user.assert_called_once_with(12345)
        mock_update.message.reply_text.assert_called_once()
        assert "Hey Test" in mock_update.message.reply_text.call_args[1]['text']
        assert 'reply_markup' in mock_update.message.reply_text.call_args[1]

def test_save_user():
    """Test the save_user function"""
    # Currently the function is commented out, so just test that it returns None
    result = bot.save_user(12345)
    assert result is None

@pytest.mark.asyncio
async def test_get_user_info(mock_update, mock_context):
    """Test the get_user_info function"""
    with patch('bot.logger') as mock_logger:
        result = await bot.get_user_info(mock_update, mock_context)
        
        # Assertions
        assert result["user_id"] == 12345
        assert result["first_name"] == "Test"
        assert result["last_name"] == "User"
        assert result["username"] == "testuser"
        assert result["chat_id"] == 12345
        assert result["message_text"] == "Test message"
        mock_logger.info.assert_called_once()

@pytest.mark.asyncio
async def test_handle_message(mock_update, mock_context):
    """Test the handle_message function"""
    with patch('bot.get_user_info') as mock_get_user_info:
        # Configure mocks
        mock_get_user_info.return_value = {
            "user_id": 12345,
            "chat_id": 67890,
            "message_text": "Test message"
        }
        
        # Call the function
        await bot.handle_message(mock_update, mock_context)
        
        # Assertions
        mock_update.message.reply_text.assert_called_once()
        assert "Test message" in mock_update.message.reply_text.call_args[0][0]
        assert "12345" in mock_update.message.reply_text.call_args[0][0]
        assert "67890" in mock_update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_handle_location(mock_update, mock_context):
    """Test the handle_location function"""
    with patch('bot.get_user_info') as mock_get_user_info:
        # Configure mocks
        mock_get_user_info.return_value = {
            "user_id": 12345,
            "chat_id": 67890
        }
        mock_update.message.location.latitude = 40.7128
        mock_update.message.location.longitude = -74.0060
        
        # Call the function
        await bot.handle_location(mock_update, mock_context)
        
        # Assertions
        mock_update.message.reply_text.assert_called_once()
        assert "40.7128" in mock_update.message.reply_text.call_args[0][0]
        assert "-74.0060" in mock_update.message.reply_text.call_args[0][0]
        assert "12345" in mock_update.message.reply_text.call_args[0][0]
        assert "67890" in mock_update.message.reply_text.call_args[0][0]

def test_setup_telegram_bot():
    """Test the setup_telegram_bot function"""
    with patch('bot.Application') as mock_application, \
         patch('bot.CommandHandler') as mock_command_handler, \
         patch('bot.MessageHandler') as mock_message_handler, \
         patch('bot.TELEGRAM_BOT_TOKEN', 'test_token'), \
         patch('bot.bot') as mock_bot:
        
        # Configure mocks
        mock_app = MagicMock()
        mock_application.builder.return_value.token.return_value.build.return_value = mock_app
        
        # Call the function
        result = bot.SetupTelegramBot()
        
        # Assertions
        assert result == mock_app
        mock_app.add_handler.assert_called()
        assert mock_app.add_handler.call_count == 3
        mock_bot.run_webhook.assert_called_once()