"""
Centralized Telegram messaging module for YAGATI Brain.
Handles all Telegram notifications in one place.
"""

import os
import requests


def send_telegram_message(message: str) -> bool:
    """
    Send a message to Telegram using bot token and chat ID from environment variables.
    
    Args:
        message: The message text to send
        
    Returns:
        True if message was sent successfully, False otherwise
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    
    if not bot_token or not chat_id:
        print("⚠️ Telegram configuration missing (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID)")
        return False
    
    # Basic validation of bot token format (should contain only alphanumeric, hyphens, and underscores)
    # Telegram bot tokens typically look like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
    if not bot_token.replace(":", "").replace("-", "").replace("_", "").isalnum():
        print("⚠️ Invalid TELEGRAM_BOT_TOKEN format")
        return False
    
    # Construct API endpoint using validated token
    api_base = "https://api.telegram.org"
    url = f"{api_base}/bot{bot_token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"⚠️ Telegram API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"⚠️ Failed to send Telegram message: {e}")
        return False
