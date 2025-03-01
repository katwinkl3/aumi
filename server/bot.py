import os
from typing import Dict, Any
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from consts import *
import redis

# Configure Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Configure logging
logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Telegram bot token from environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
AUMI_URL = os.getenv("AUMI_URL")

@dataclass
class ApiResponse:
    Code: int
    Msg: str
    Data: Dict

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command
    """
    user_info = await get_user_info(update, context)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Access App",
                web_app=AUMI_URL
            )]
        ]
    )
    save_user(user_info["user_id"])
    await update.message.reply_text(
        text=f"Hey {user_info['first_name']}, either paste your link here or enter the app interface from the button below",
        reply_markup=keyboard
    )

def save_user(userId: int) -> None:
    """Save user ID to Redis cache"""
    # try:
    #     redis_client.set(f"user:{userId}", "active")
    #     logger.info(f"User {userId} saved to Redis cache")
    # except redis.RedisError as e:
    #     logger.error(f"Failed to save user {userId} to Redis: {str(e)}")
    return

async def get_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Dict[str, Any]:
    user = update.effective_user
    message = update.effective_message
    chat = update.effective_chat
    
    user_info = {
        # Basic user information
        "user_id": user.id,
        "is_bot": user.is_bot,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "language_code": user.language_code,
        
        # Chat information
        "chat_id": chat.id,
        "chat_type": chat.type,
        "chat_title": chat.title if chat.type != "private" else None,
        
        # Message information
        "message_id": message.message_id,
        "message_text": message.text,
        "message_date": message.date.isoformat(),
    }
    
    # Add optional user data if available
    if hasattr(user, 'can_join_groups') and user.can_join_groups is not None:
        user_info["can_join_groups"] = user.can_join_groups
        
    if hasattr(user, 'can_read_all_group_messages') and user.can_read_all_group_messages is not None:
        user_info["can_read_all_group_messages"] = user.can_read_all_group_messages
        
    if hasattr(user, 'supports_inline_queries') and user.supports_inline_queries is not None:
        user_info["supports_inline_queries"] = user.supports_inline_queries
    
    # Log user information
    logger.info(f"Received message from user: {user.id} ({user.username or user.first_name})")
    
    return user_info

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages"""
    user_info = await get_user_info(update, context)
    await update.message.reply_text(
        f"I've received your message: '{user_info['message_text']}'\n\n"
        f"User ID: {user_info['user_id']}\n"
        f"Chat ID: {user_info['chat_id']}"
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming location messages"""
    user_info = await get_user_info(update, context)
    location = update.message.location
    await update.message.reply_text(
        f"I've received your location!\n\n"
        f"Latitude: {location.latitude}\n"
        f"Longitude: {location.longitude}\n\n"
        f"User ID: {user_info['user_id']}\n"
        f"Chat ID: {user_info['chat_id']}"
    )

def setup_telegram_bot() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Telegram bot token not found. Make sure TELEGRAM_BOT_TOKEN is set in your .env file.")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    bot.run_webhook( #event based instead of polling
            listen="0.0.0.0",
            port=8443,
            url_path=TELEGRAM_BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
    )
    return application


@app.route('/api/validate', methods=['POST'])
def validate_webapp():
    """API endpoint to validate Telegram Mini App data and return user info"""
    data = request.json
    if not data or 'initData' not in data:
        return ApiResponse(400, "missing initData", {})
    init_data = data['initData']
    
    # Validate the data
    if not validate_telegram_webapp_data(init_data):
        return ApiResponse(403, "missing initData", {})
    
    # Parse user data from initData
    init_data_dict = dict(parse_qsl(init_data))
    user_data = json.loads(init_data_dict.get('user', '{}'))
    
    user_id = user_data.get('id')
    if not user_id:
        return jsonify({"error": "User ID not found in initData"}), 400
    
    # Get additional user info from our store if available
    stored_user_data = user_data_store.get(user_id, {})
    
    # Merge data from initData with our stored data
    combined_user_data = {**user_data, **stored_user_data}
    
    return jsonify({
        "success": True,
        "userData": combined_user_data
    })