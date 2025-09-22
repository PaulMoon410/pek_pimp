# pek_pimp.py
import time
import os
import subprocess
from fetch_market import get_orderbook_top
from place_order import place_order, get_open_orders, get_balance
from datetime import datetime, timedelta

# Read credentials from bot_info.txt
def read_bot_info(path="bot_info.txt"):
    try:
        with open(path, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
            if len(lines) >= 2:
                return lines[0], lines[1]
    except Exception:
        pass
    return None, None

HIVE_ACCOUNT, HIVE_ACTIVE_KEY = read_bot_info(os.path.join(os.path.dirname(__file__), "bot_info.txt"))
HIVE_NODES = ["https://api.hive.blog", "https://anyx.io"]
TOKEN = "PIMP"
TARGET_PRICE = 0.02  # Target price to maintain for PIMP
BUY_SPREAD = 0.0001
SELL_SPREAD = 0.0001
TICK = 0.0000001
DELAY = 60

# Initialize last cancel time
last_cancel_time = None

def pimp_logic(account_name, token):
    global last_cancel_time  # Use global variable to track last cancel time
    cancel_triggered = False  # Flag to ensure cancel orders run only once
    try:
        market = get_orderbook_top(token)
        if not market:
            print("[DEBUG] Market data not available.")
            return
        bid = market["highestBid"]
        ask = market["lowestAsk"]
        print(f"[DEBUG] Market conditions - Highest Bid: {bid}, Lowest Ask: {ask}")

        hive_balance = get_balance(account_name, "SWAP.HIVE")
        pimp_balance = get_balance(account_name, token)
        print(f"[DEBUG] Balances - SWAP.HIVE: {hive_balance}, PIMP: {pimp_balance}")

        open_orders = get_open_orders(account_name, token)

        def has_open_order(order_type, price):
            for order in open_orders:
                if order.get("type") == order_type and float(order.get("price", 0)) == float(price):
                    return True
            return False

        buy_price = round(TARGET_PRICE - BUY_SPREAD, 8)
        print(f"[DEBUG] Calculated Buy Price: {buy_price}")

        # Buy logic: only place buy orders if total market value of PIMP held is less than 0.1999999 HIVE
        pimp_market_value = pimp_balance * ask if ask > 0 else 0
        print(f"[DEBUG] PIMP Market Value: {pimp_market_value}")
        if ask > 0 and ask <= buy_price and hive_balance > 0 and pimp_market_value < 0.1999999:
            if not has_open_order("buy", buy_price):
                max_hive_to_spend = min(hive_balance, 3, 0.1999999 - pimp_market_value)
                if max_hive_to_spend > 0:
                    buy_qty = round(max_hive_to_spend / buy_price, 8)  # Calculate PIMP quantity based on HIVE amount
                    print(f"[INFO] Placing Buy Order - Price: {buy_price}, Quantity: {buy_qty} (spending {max_hive_to_spend} HIVE)")
                    place_order(account_name, token, buy_price, buy_qty, order_type="buy", active_key=HIVE_ACTIVE_KEY, nodes=HIVE_NODES)
                    cancel_triggered = True  # Mark cancel as needed
                    time.sleep(6)
                    # Place PEK buy order after successful PIMP buy
                    pek_market = get_orderbook_top("PEK")
                    pek_ask = pek_market["lowestAsk"] if pek_market and pek_market["lowestAsk"] > 0 else buy_price
                    print(f"[INFO] Placing PEK Buy Order - Price: {pek_ask}, Quantity: 0.00000001")
                    place_order(account_name, "PEK", pek_ask, 0.00000001, order_type="buy", active_key=HIVE_ACTIVE_KEY, nodes=HIVE_NODES)
        # Sell logic: only sell if current market ask exceeds 2
        if ask > 2 and pimp_balance > 0:
            sell_price = round(ask, 8)
            print(f"[DEBUG] Calculated Sell Price: {sell_price}")
            if not has_open_order("sell", sell_price):
                sell_qty = round(pimp_balance * 0.3, 8)  # Sell 30% of PIMP holdings
                hive_value = sell_qty * sell_price  # Calculate HIVE value of the sale
                print(f"[INFO] Placing Sell Order - Price: {sell_price}, Quantity: {sell_qty} (receiving ~{hive_value:.8f} HIVE)")
                place_order(account_name, token, sell_price, sell_qty, order_type="sell", active_key=HIVE_ACTIVE_KEY, nodes=HIVE_NODES)
                cancel_triggered = True  # Mark cancel as needed
                time.sleep(6)
                # Place PEK buy order after successful PIMP sell
                pek_market = get_orderbook_top("PEK")
                pek_ask = pek_market["lowestAsk"] if pek_market and pek_market["lowestAsk"] > 0 else sell_price
                print(f"[INFO] Placing PEK Buy Order - Price: {pek_ask}, Quantity: 0.00000001")
                place_order(account_name, "PEK", pek_ask, 0.00000001, order_type="buy", active_key=HIVE_ACTIVE_KEY, nodes=HIVE_NODES)
        # Stabilize logic
        if hive_balance > 0 and not has_open_order("buy", TARGET_PRICE):
            max_hive_to_spend = min(hive_balance, 3)  # Spend up to 3 HIVE
            buy_qty = round(max_hive_to_spend / TARGET_PRICE, 8)  # Calculate PIMP quantity based on HIVE amount
            print(f"[DEBUG] Calculation: {max_hive_to_spend} HIVE / {TARGET_PRICE} = {max_hive_to_spend / TARGET_PRICE} PIMP")
            print(f"[INFO] Placing Stabilize Buy Order - Price: {TARGET_PRICE}, Quantity: {buy_qty} (spending {max_hive_to_spend} HIVE)")
            place_order(account_name, token, TARGET_PRICE, buy_qty, order_type="buy", active_key=HIVE_ACTIVE_KEY, nodes=HIVE_NODES)
            cancel_triggered = True  # Mark cancel as needed
            time.sleep(6)
            pek_market = get_orderbook_top("PEK")
            pek_ask = pek_market["lowestAsk"] if pek_market and pek_market["lowestAsk"] > 0 else TARGET_PRICE
            print(f"[INFO] Placing PEK Buy Order - Price: {pek_ask}, Quantity: 0.00000001")
            place_order(account_name, "PEK", pek_ask, 0.00000001, order_type="buy", active_key=HIVE_ACTIVE_KEY, nodes=HIVE_NODES)

        # Trigger cancel orders if needed and 4 hours have passed since last cancel
        current_time = datetime.now()
        if cancel_triggered and (last_cancel_time is None or current_time - last_cancel_time >= timedelta(hours=4)):
            try:
                print("[INFO] Running pimp_cancel.py to cancel orders.")
                subprocess.run(["python", "pimp_cancel.py", "--once"], check=True)
                last_cancel_time = current_time  # Update last cancel time
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Failed to execute pimp_cancel.py: {e}")
    except Exception as e:
        print(f"[ERROR] Exception in pimp_logic: {e}")

if __name__ == "__main__":
    while True:
        print("[INFO] Running market stabilization logic.")
        pimp_logic(HIVE_ACCOUNT, TOKEN)
        print("[INFO] Waiting for 45 minutes before the next cycle.")
        time.sleep(2700)  # Wait for 45 minutes (2700 seconds)
