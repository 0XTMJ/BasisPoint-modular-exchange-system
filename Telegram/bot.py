"""
Telegram Bot for Funding Rate Notifications
============================================
Sends hourly notifications about highest/lowest funding rates and best arbitrage opportunities.
"""

import os
import time
import schedule
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from config.settings import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DATABASE,
    POSTGRES_USER,
    POSTGRES_PASSWORD
)
from utils.logger import setup_logger
from dotenv import load_dotenv

load_dotenv()

logger = setup_logger("TelegramBot")


class TelegramBot:
    """
    Telegram bot for sending funding rate and arbitrage notifications.
    """
    
    def __init__(self):
        """
        Initialize the Telegram bot.
        """
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID environment variable not set")
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.db_config = {
            'host': POSTGRES_HOST,
            'port': POSTGRES_PORT,
            'database': POSTGRES_DATABASE,
            'user': POSTGRES_USER,
            'password': POSTGRES_PASSWORD
        }
        self.logger = logger
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """
        Test Telegram bot connection.
        """
        try:
            response = requests.get(f"{self.api_url}/getMe", timeout=10)
            response.raise_for_status()
            bot_info = response.json()
            if bot_info.get("ok"):
                self.logger.info(f"Telegram bot connected: @{bot_info['result']['username']}")
            else:
                raise ValueError(f"Telegram API error: {bot_info}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Telegram: {e}")
            raise
    
    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a message to the configured chat.
        
        Args:
            text: Message text to send
            parse_mode: Telegram parse mode (Markdown or HTML)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                self.logger.info("Message sent successfully")
                return True
            else:
                self.logger.error(f"Telegram API error: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    def get_highest_funding_rates(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get contracts with highest funding rates (APR).
        
        Args:
            limit: Number of top contracts to return
            
        Returns:
            List of contracts with highest funding rates
        """
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            cur = conn.cursor()
            
            query = """
                SELECT 
                    ed.exchange,
                    ed.symbol,
                    ed.base_asset,
                    ed.funding_rate,
                    ed.apr,
                    ed.funding_interval_hours,
                    ed.last_updated
                FROM exchange_data ed
                LEFT JOIN contract_metadata cm
                    ON ed.exchange = cm.exchange AND ed.symbol = cm.symbol
                WHERE ed.apr IS NOT NULL
                    AND (cm.is_active = true OR cm.is_active IS NULL)
                    AND ed.last_updated > NOW() - INTERVAL '1 day'
                ORDER BY ed.apr DESC
                LIMIT %s
            """
            
            cur.execute(query, (limit,))
            results = cur.fetchall()
            
            contracts = []
            for row in results:
                contracts.append({
                    'exchange': row['exchange'],
                    'symbol': row['symbol'],
                    'base_asset': row['base_asset'] or row['symbol'],
                    'funding_rate': float(row['funding_rate']) if row['funding_rate'] else 0,
                    'apr': float(row['apr']) if row['apr'] else 0,
                    'funding_interval_hours': row['funding_interval_hours'] or 8,
                    'last_updated': row['last_updated']
                })
            
            return contracts
            
        except Exception as e:
            self.logger.error(f"Error getting highest funding rates: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_lowest_funding_rates(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get contracts with lowest funding rates (APR).
        
        Args:
            limit: Number of bottom contracts to return
            
        Returns:
            List of contracts with lowest funding rates
        """
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            cur = conn.cursor()
            
            query = """
                SELECT 
                    ed.exchange,
                    ed.symbol,
                    ed.base_asset,
                    ed.funding_rate,
                    ed.apr,
                    ed.funding_interval_hours,
                    ed.last_updated
                FROM exchange_data ed
                LEFT JOIN contract_metadata cm
                    ON ed.exchange = cm.exchange AND ed.symbol = cm.symbol
                WHERE ed.apr IS NOT NULL
                    AND (cm.is_active = true OR cm.is_active IS NULL)
                    AND ed.last_updated > NOW() - INTERVAL '1 day'
                ORDER BY ed.apr ASC
                LIMIT %s
            """
            
            cur.execute(query, (limit,))
            results = cur.fetchall()
            
            contracts = []
            for row in results:
                contracts.append({
                    'exchange': row['exchange'],
                    'symbol': row['symbol'],
                    'base_asset': row['base_asset'] or row['symbol'],
                    'funding_rate': float(row['funding_rate']) if row['funding_rate'] else 0,
                    'apr': float(row['apr']) if row['apr'] else 0,
                    'funding_interval_hours': row['funding_interval_hours'] or 8,
                    'last_updated': row['last_updated']
                })
            
            return contracts
            
        except Exception as e:
            self.logger.error(f"Error getting lowest funding rates: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_best_arbitrage_opportunities(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get best arbitrage opportunities.
        
        Args:
            limit: Number of top opportunities to return
            
        Returns:
            List of arbitrage opportunities
        """
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            cur = conn.cursor()
            
            query = """
                SELECT 
                    asset,
                    exchange_a,
                    exchange_b,
                    apr_spread,
                    timestamp
                FROM arbitrage_spreads
                WHERE timestamp > NOW() - INTERVAL '1 hour'
                ORDER BY apr_spread DESC
                LIMIT %s
            """
            
            cur.execute(query, (limit,))
            results = cur.fetchall()
            
            opportunities = []
            for row in results:
                opportunities.append({
                    'asset': row['asset'],
                    'exchange_a': row['exchange_a'],
                    'exchange_b': row['exchange_b'],
                    'apr_spread': float(row['apr_spread']) if row['apr_spread'] else 0,
                    'timestamp': row['timestamp']
                })
            
            # If no recent opportunities, try to get from exchange_data directly
            if not opportunities:
                opportunities = self._calculate_arbitrage_from_current_data(limit)
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error getting arbitrage opportunities: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def _calculate_arbitrage_from_current_data(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Calculate arbitrage opportunities from current exchange_data.
        
        Args:
            limit: Number of opportunities to return
            
        Returns:
            List of arbitrage opportunities
        """
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            cur = conn.cursor()
            
            query = """
                WITH asset_rates AS (
                    SELECT 
                        COALESCE(ed.base_asset, ed.symbol) as asset,
                        ed.exchange,
                        ed.symbol,
                        ed.funding_rate,
                        ed.apr,
                        ed.funding_interval_hours
                    FROM exchange_data ed
                    LEFT JOIN contract_metadata cm
                        ON ed.exchange = cm.exchange AND ed.symbol = cm.symbol
                    WHERE ed.funding_rate IS NOT NULL
                        AND (cm.is_active = true OR cm.is_active IS NULL)
                        AND ed.last_updated > NOW() - INTERVAL '1 hour'
                ),
                pairs AS (
                    SELECT 
                        a1.asset,
                        a1.exchange as exchange_a,
                        a2.exchange as exchange_b,
                        a1.apr as apr_a,
                        a2.apr as apr_b,
                        ABS(a1.apr - a2.apr) as apr_spread
                    FROM asset_rates a1
                    JOIN asset_rates a2 ON a1.asset = a2.asset
                    WHERE a1.exchange < a2.exchange
                        AND (a1.funding_rate * a2.funding_rate < 0)
                )
                SELECT 
                    asset,
                    exchange_a,
                    exchange_b,
                    apr_spread
                FROM pairs
                WHERE apr_spread > 1.0
                ORDER BY apr_spread DESC
                LIMIT %s
            """
            
            cur.execute(query, (limit,))
            results = cur.fetchall()
            
            opportunities = []
            for row in results:
                opportunities.append({
                    'asset': row['asset'],
                    'exchange_a': row['exchange_a'],
                    'exchange_b': row['exchange_b'],
                    'apr_spread': float(row['apr_spread']) if row['apr_spread'] else 0,
                    'timestamp': datetime.now(timezone.utc)
                })
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error calculating arbitrage from current data: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def format_funding_rate_message(self, contract: Dict[str, Any]) -> str:
        """
        Format a single funding rate contract for display.
        
        Args:
            contract: Contract data dictionary
            
        Returns:
            Formatted string
        """
        exchange = contract['exchange'].upper()
        asset = contract['base_asset']
        symbol = contract['symbol']
        funding_rate = contract['funding_rate']
        apr = contract['apr']
        interval = contract['funding_interval_hours']
        
        rate_pct = funding_rate * 100
        apr_pct = apr
        
        return f"• {asset} ({exchange})\n  Rate: {rate_pct:.4f}% | APR: {apr_pct:.2f}% | {interval}h"
    
    def format_arbitrage_message(self, opp: Dict[str, Any]) -> str:
        """
        Format an arbitrage opportunity for display.
        
        Args:
            opp: Opportunity data dictionary
            
        Returns:
            Formatted string
        """
        asset = opp['asset']
        exchange_a = opp['exchange_a'].upper()
        exchange_b = opp['exchange_b'].upper()
        spread = opp['apr_spread']
        
        return f"• {asset}: {exchange_a} ↔ {exchange_b}\n  Spread: {spread:.2f}% APR"
    
    def generate_hourly_report(self) -> str:
        """
        Generate the hourly notification report.
        
        Returns:
            Formatted message string
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Get data
        highest = self.get_highest_funding_rates(limit=5)
        lowest = self.get_lowest_funding_rates(limit=5)
        arbitrage = self.get_best_arbitrage_opportunities(limit=5)
        
        # Build message
        message = f"📊 *Funding Rate Report*\n_{timestamp}_\n\n"
        
        # Highest funding rates
        if highest:
            message += "🔺 *Highest Funding Rates:*\n"
            for contract in highest:
                message += self.format_funding_rate_message(contract) + "\n"
            message += "\n"
        else:
            message += "⚠️ No high funding rate data available\n\n"
        
        # Lowest funding rates
        if lowest:
            message += "🔻 *Lowest Funding Rates:*\n"
            for contract in lowest:
                message += self.format_funding_rate_message(contract) + "\n"
            message += "\n"
        else:
            message += "⚠️ No low funding rate data available\n\n"
        
        # Best arbitrage opportunities
        if arbitrage:
            message += "💰 *Best Arbitrage Opportunities:*\n"
            for opp in arbitrage:
                message += self.format_arbitrage_message(opp) + "\n"
        else:
            message += "⚠️ No arbitrage opportunities found\n"
        
        return message
    
    def send_hourly_report(self):
        """
        Send the hourly report.
        """
        try:
            report = self.generate_hourly_report()
            success = self.send_message(report)
            
            if success:
                self.logger.info("Hourly report sent successfully")
            else:
                self.logger.error("Failed to send hourly report")
                
        except Exception as e:
            self.logger.error(f"Error sending hourly report: {e}")
    
    def run(self):
        """
        Run the bot with hourly scheduling.
        """
        self.logger.info("Starting Telegram bot...")
        
        # Send initial welcome message
        welcome = "🤖 *Telegram Bot Started*\n\nHourly funding rate reports will be sent automatically."
        self.send_message(welcome)
        
        # Schedule hourly reports (at the top of each hour)
        schedule.every().hour.at(":00").do(self.send_hourly_report)
        
        # Also send one immediately
        self.send_hourly_report()
        
        self.logger.info("Bot is running. Press Ctrl+C to stop.")
        
        # Keep the bot running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
            self.send_message("🤖 *Bot Stopped*\n\nHourly reports have been disabled.")


if __name__ == "__main__":
    try:
        bot = TelegramBot()
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"Error: {e}")
        print("\nPlease ensure:")
        print("1. TELEGRAM_BOT_TOKEN is set in .env file")
        print("2. TELEGRAM_CHAT_ID is set in .env file")
        print("3. Database is running and accessible")

