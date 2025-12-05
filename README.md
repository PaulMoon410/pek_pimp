# PEK PIMP Bot

A Hive Engine market maker bot for trading PIMP tokens on the Hive blockchain. This bot implements an automated trading strategy to maximize volume growth through bid-ask spread capture.

## Features

- **Market Maker Strategy**: Automatically buys below market and sells above to capture spreads
- **Volume Growth Optimization**: Prioritizes accumulating PIMP tokens through aggressive trading parameters
- **Dynamic Reserve System**: Maintains a growing reserve starting at 1 PIMP, incrementing by 0.00000001 per cycle
- **15-Minute Trading Cycles**: Executes trading logic every 15 minutes
- **Automatic Order Management**: Cancels orders every 3rd cycle to refresh positions
- **Real-time Portfolio Tracking**: Displays balance, portfolio value, and growth metrics

## Requirements

- Python 3.7+
- `beem` - Hive blockchain library
- `requests` - HTTP client

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd pek_pimp_bot
```

2. Install dependencies:
```bash
pip install beem requests
```

3. Create `bot_info.txt` in the project root with your Hive account credentials:
```
YOUR_HIVE_ACCOUNT
YOUR_ACTIVE_KEY
```

**Important**: Never commit `bot_info.txt` to version control. Add it to `.gitignore`.

## Configuration

Edit the trading parameters in `pek_pimp.py`:

```python
TARGET_PRICE = 0.02  # Target price to maintain
MARKET_MAKING_SPREAD = 0.0010  # 1% base spread
SELL_PERCENTAGE = 0.10  # 10% of holdings per cycle
BUY_BACK_PERCENTAGE = 1.0  # 100% of HIVE to buyback
INITIAL_PIMP_RESERVE = 1.0  # Starting reserve
MAX_HIVE_TO_HOLD = 2.0  # Threshold for converting HIVE back
AGGRESSIVE_SPREAD_MULTIPLIER = 2.0  # Multiplier for faster fills
```

## Usage

Run the bot:
```bash
python pek_pimp.py
```

The bot will:
1. Fetch current market data (bid/ask prices)
2. Sell a portion of PIMP holdings just below the ask price to generate HIVE
3. Buy back PIMP with generated HIVE just above the bid price
4. Repeat every 15 minutes
5. Cancel orders every 3rd cycle to refresh

## Project Structure

- `pek_pimp.py` - Main trading logic and market maker strategy
- `place_order.py` - Order execution and balance fetching
- `fetch_market.py` - Market data retrieval from Hive Engine API
- `pimp_cancel.py` - Order cancellation utility
- `bot_info.txt` - Credentials file (excluded from version control)

## How It Works

### Trading Strategy

The bot implements a market maker strategy designed for volume growth:

1. **Sell Phase**: Sells 10% of excess PIMP holdings at an aggressive discount (just below market ask)
2. **Generate Capital**: Converts PIMP to HIVE with each sale
3. **Buy Phase**: Uses 100% of HIVE to buy back PIMP at a slight premium (just above market bid)
4. **Net Gain**: Captures spread difference, accumulating more PIMP tokens over time

### Reserve System

- Starts with 1 PIMP reserve
- Grows by 0.00000001 per 15-minute cycle
- Ensures minimum holdings protection while maximizing tradeable capital

### Cycle Timing

- **Execution**: Every 15 minutes (900 seconds)
- **Order Cancellation**: Every 3rd cycle (45 minutes)
- **Continuous Operation**: Runs indefinitely until stopped

## Hive Engine API

The bot uses the Hive Engine API to:
- Fetch order book data
- Query open orders
- Execute buy/sell trades
- Check account balances

API Endpoint: `https://api.hive-engine.com/rpc/contracts`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This bot trades real assets on the Hive blockchain. Use at your own risk. The authors are not responsible for any losses incurred. Test thoroughly in a safe environment before deploying with real funds.

## Support

For issues, questions, or suggestions, please open an issue on the repository.
