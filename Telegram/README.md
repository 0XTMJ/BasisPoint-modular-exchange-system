# Telegram Bot for Funding Rate Notifications

This Telegram bot sends hourly notifications about:
- Highest funding rates (top 5 contracts)
- Lowest funding rates (bottom 5 contracts)
- Best arbitrage opportunities (top 5 opportunities)

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Chat ID

1. Send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for the `"chat":{"id":123456789}` value in the response
4. Copy the chat ID number

### 3. Configure Environment Variables

Add these to your `.env` file:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 4. Install Dependencies

```bash
pip install schedule
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Running the Bot

### Start the Bot

```bash
python Telegram/start_bot.py
```

Or:

```bash
python -m Telegram.bot
```

### Bot Behavior

- Sends a welcome message when started
- Sends hourly reports at the top of each hour (e.g., 1:00, 2:00, 3:00)
- Sends one report immediately upon startup
- Continues running until stopped with Ctrl+C

### Example Report

```
📊 Funding Rate Report
_2024-01-15 14:00:00 UTC_

🔺 Highest Funding Rates:
• BTC (BINANCE)
  Rate: 0.0500% | APR: 54.75% | 8h
• ETH (KUCOIN)
  Rate: 0.0400% | APR: 43.80% | 8h

🔻 Lowest Funding Rates:
• SOL (HYPERLIQUID)
  Rate: -0.0200% | APR: -21.90% | 1h
• AVAX (BACKPACK)
  Rate: -0.0150% | APR: -16.43% | 1h

💰 Best Arbitrage Opportunities:
• BTC: BINANCE ↔ KUCOIN
  Spread: 12.50% APR
• ETH: KUCOIN ↔ HYPERLIQUID
  Spread: 8.75% APR
```

## Troubleshooting

### Bot Not Sending Messages

1. Verify `TELEGRAM_BOT_TOKEN` is correct
2. Verify `TELEGRAM_CHAT_ID` is correct
3. Make sure you've sent at least one message to the bot first
4. Check that the database is running and accessible

### Database Connection Errors

- Ensure PostgreSQL is running
- Verify database credentials in `.env` file
- Check that `exchange_data` table exists and has data

### No Data in Reports

- Ensure the main data collection system is running (`python main.py`)
- Check that contracts have been collected recently
- Verify `contract_metadata.is_active = true` for active contracts

## Integration with System

The bot integrates with:
- `exchange_data` table for current funding rates
- `arbitrage_spreads` table for arbitrage opportunities
- `contract_metadata` table to filter active contracts

## Customization

### Change Report Frequency

Edit `Telegram/bot.py`:

```python
# For every 30 minutes:
schedule.every(30).minutes.do(self.send_hourly_report)

# For every 2 hours:
schedule.every(2).hours.do(self.send_hourly_report)
```

### Change Number of Items

Edit the `limit` parameter in:
- `get_highest_funding_rates(limit=5)`
- `get_lowest_funding_rates(limit=5)`
- `get_best_arbitrage_opportunities(limit=5)`

### Modify Message Format

Edit the formatting methods:
- `format_funding_rate_message()`
- `format_arbitrage_message()`
- `generate_hourly_report()`


