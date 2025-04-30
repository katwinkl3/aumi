import os
from typing import Dict, Any
import logging
from consts import TELEGRAM_BOT_TOKEN, AUMI_URL, WEBHOOK_URL
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import redis
from urllib.parse import urlparse, quote

# Configure Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Configure logging
logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)
logger = logging.getLogger(__name__)

# Telegram handling
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command
    """
    user_info = await get_user_info(update, context)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Access App",
                web_app=WebAppInfo(url=AUMI_URL)
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

# def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: #todo - queue + rate limit
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages"""
    message = update.effective_message
    if message.text:
        print(message.text)
        encoded_message = quote(message.text)
        keyboard=[
            [InlineKeyboardButton(
                text="Access App below",
                web_app=WebAppInfo(url=AUMI_URL + "?message=" + encoded_message)
            )]
        ]
        await update.message.reply_text(
            text=f"Access the web app below: '{message.text}'",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif message.location:
        print(message.location)
        await update.message.reply_text(
            f"I've received your location: '{message.location}'"
        )
    else:
        print(message)
        update.message.reply_text(
            f"Unable to process message:'{message}'"
        )


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming location messages"""
    user_info = get_user_info(update, context)
    location = update.message.location
    print(location)
    await update.message.reply_text(
        f"I've received your location!\n\n"
        f"Latitude: {location.latitude}\n"
        f"Longitude: {location.longitude}\n\n"
        f"User ID: {user_info['user_id']}\n"
        f"Chat ID: {user_info['chat_id']}"
    )

# def set_webhook():
#     # TelegramBot.delete_webhook()  # Clean previous webhooks
#     TelegramBot.bot.set_webhook(
#         url=WEBHOOK_URL,
#         secret_token=TELEGRAM_BOT_TOKEN,
#         max_connections=40
#     )

bot = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
global TelegramBot
TelegramBot = bot

if __name__ == "__main__":
    try:
        bot.add_handler(CommandHandler("start", start_command))
        bot.add_handler(MessageHandler(filters.LOCATION, handle_location))
        bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        bot.run_polling()
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot has been stopped")
    # application.bot.set_webhook(f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")