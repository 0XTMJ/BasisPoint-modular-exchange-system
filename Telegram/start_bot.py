"""
Startup script for Telegram bot
================================
Run this script to start the Telegram bot for hourly notifications.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Telegram.bot import TelegramBot
from utils.logger import setup_logger

logger = setup_logger("TelegramBotStartup")

if __name__ == "__main__":
    try:
        logger.info("Starting Telegram bot...")
        bot = TelegramBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)


