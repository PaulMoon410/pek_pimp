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

# Trading Parameters for VOLUME GROWTH (Priority #1: Increase PIMP Holdings)
TARGET_PRICE = 0.02  # Target price to maintain for PIMP
MARKET_MAKING_SPREAD = 0.0010  # 1% spread for profit per trade cycle
SELL_PERCENTAGE = 0.10  # Sell 10% of available holdings per cycle for max capital
BUY_BACK_PERCENTAGE = 1.0  # Use 100% of HIVE to buy back (maximize growth)
MIN_HIVE_FOR_BUYBACK = 0.01  # Minimum HIVE needed to place buy order
INITIAL_PIMP_RESERVE = 1.0  # Start with 1 PIMP reserve
RESERVE_GROWTH_PER_CYCLE = 0.00000001  # Increase reserve by this amount each cycle
MAX_HIVE_TO_HOLD = 2.0  # Low threshold - quickly convert HIVE back to PIMP
AGGRESSIVE_SPREAD_MULTIPLIER = 2.0  # Be more aggressive with spread for faster fills

# Initialize tracking variables
last_cancel_time = None
initial_portfolio_value = None
pimp_reserve = INITIAL_PIMP_RESERVE  # Dynamic reserve that grows each cycle
cycle_count = 0

def pimp_logic(account_name, token):
    global last_cancel_time, initial_portfolio_value, pimp_reserve, cycle_count
    cancel_triggered = False
    cycle_count += 1
    
    try:
        market = get_orderbook_top(token)
        if not market:
            print("[DEBUG] Market data not available.")
            return
        
        bid = market["highestBid"]
        ask = market["lowestAsk"]
        spread = ask - bid if ask > 0 and bid > 0 else 0
        
        hive_balance = get_balance(account_name, "SWAP.HIVE")
        pimp_balance = get_balance(account_name, token)
        
        # Calculate portfolio metrics
        pimp_market_value = pimp_balance * ask if ask > 0 else 0
        total_portfolio_value = hive_balance + pimp_market_value
        pimp_percentage = (pimp_market_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        hive_percentage = (hive_balance / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        
        # Track portfolio growth
        if initial_portfolio_value is None:
            initial_portfolio_value = total_portfolio_value
        portfolio_growth = ((total_portfolio_value - initial_portfolio_value) / initial_portfolio_value * 100) if initial_portfolio_value > 0 else 0
        
        print(f"[INFO] === Portfolio Status ===")
        print(f"[INFO] HIVE: {hive_balance:.4f} ({hive_percentage:.1f}%) | PIMP: {pimp_balance:.2f} ({pimp_percentage:.1f}%)")
        print(f"[INFO] Total Value: {total_portfolio_value:.4f} HIVE | Growth: {portfolio_growth:+.2f}%")
        print(f"[INFO] Market - Bid: {bid:.8f} | Ask: {ask:.8f} | Spread: {spread:.8f}")
        
        open_orders = get_open_orders(account_name, token)
        
        def has_open_order(order_type, price_range=None):
            for order in open_orders:
                if order.get("type") == order_type:
                    if price_range is None:
                        return True
                    order_price = float(order.get("price", 0))
                    if price_range[0] <= order_price <= price_range[1]:
                        return True
            return False
        
        # === MARKET MAKER STRATEGY ===
        # Strategy: Maintain minimal reserve, sell excess, buy back more to grow holdings
        
        print(f"[RESERVE] Current reserve requirement: {pimp_reserve:.8f} PIMP (Cycle #{cycle_count})")
        
        # STEP 1: SELL PIMP to generate HIVE (aggressive selling for max capital)
        if pimp_balance > pimp_reserve and hive_balance < MAX_HIVE_TO_HOLD:
            # Calculate sell amount - sell larger portion to generate more trading capital
            available_to_sell = pimp_balance - pimp_reserve
            sell_qty = round(available_to_sell * SELL_PERCENTAGE, 8)
            
            # Use aggressive spread for faster fills and more capital generation
            aggressive_spread = MARKET_MAKING_SPREAD * AGGRESSIVE_SPREAD_MULTIPLIER
            sell_price = round(ask * (1 - aggressive_spread), 8)
            
            # Ensure minimum price floor but prioritize volume growth
            if sell_price < TARGET_PRICE * 0.4:
                sell_price = round(TARGET_PRICE * 0.4, 8)
                print(f"[INFO] Adjusted sell price to floor: {sell_price}")
            
            if sell_qty >= 1 and not has_open_order("sell", (sell_price * 0.95, sell_price * 1.05)):
                expected_hive = sell_qty * sell_price
                remaining_pimp = pimp_balance - sell_qty
                potential_buyback = expected_hive / (bid * (1 + aggressive_spread))
                volume_increase = potential_buyback - sell_qty
                
                print(f"[SELL→GROW] Selling {sell_qty:.2f} PIMP at {sell_price}")
                print(f"[CAPITAL] Generating {expected_hive:.4f} HIVE → Est. buyback {potential_buyback:.2f} PIMP")
                print(f"[VOLUME] Expected net increase: +{volume_increase:.2f} PIMP ({(volume_increase/pimp_balance*100):.3f}%)")
                place_order(account_name, token, sell_price, sell_qty, order_type="sell", active_key=HIVE_ACTIVE_KEY, nodes=HIVE_NODES)
                cancel_triggered = True
                time.sleep(6)
                # Increase reserve for next cycle
                pimp_reserve += RESERVE_GROWTH_PER_CYCLE
        
        # STEP 2: BUY BACK PIMP (PRIORITY: Maximize volume acquisition)
        if hive_balance >= MIN_HIVE_FOR_BUYBACK:
            # Use aggressive spread for faster fills and maximum volume growth
            aggressive_spread = MARKET_MAKING_SPREAD * AGGRESSIVE_SPREAD_MULTIPLIER
            buy_price = round(bid * (1 + aggressive_spread), 8)
            
            # Will buy at reasonable prices to maximize accumulation
            if buy_price > TARGET_PRICE * 3:
                print(f"[WARNING] Buy price too high ({buy_price}), skipping buy")
            elif buy_price > 0:
                # Use ALL available HIVE to maximize holdings growth
                max_hive_to_spend = hive_balance * BUY_BACK_PERCENTAGE
                buy_qty = round(max_hive_to_spend / buy_price, 8)
                
                if buy_qty > 0 and not has_open_order("buy", (buy_price * 0.95, buy_price * 1.05)):
                    new_total = pimp_balance + buy_qty
                    growth_pct = (buy_qty / pimp_balance * 100) if pimp_balance > 0 else 0
                    
                    print(f"[BUYBACK→GROW] Buying {buy_qty:.2f} PIMP at {buy_price}")
                    print(f"[VOLUME] {pimp_balance:.2f} → {new_total:.2f} PIMP (+{growth_pct:.3f}%)")
                    print(f"[CAPITAL] Spending ALL {max_hive_to_spend:.4f} HIVE for maximum growth")
                    place_order(account_name, token, buy_price, buy_qty, order_type="buy", active_key=HIVE_ACTIVE_KEY, nodes=HIVE_NODES)
                    cancel_triggered = True
                    time.sleep(6)
        
        # === PRICE FLOOR SUPPORT (Optional) ===
        # Only place support orders if we have extra HIVE after buyback
        if hive_balance > 0.5 and pimp_balance > pimp_reserve * 2:
            support_price = round(TARGET_PRICE * 0.95, 8)  # 5% below target
            support_hive = min(hive_balance * 0.3, 1.0)  # Use 30% of HIVE, max 1 HIVE
            support_qty = round(support_hive / support_price, 8)
            
            if not has_open_order("buy", (support_price * 0.99, support_price * 1.01)):
                print(f"[SUPPORT] Placing support bid at {support_price}")
                print(f"[SUPPORT] {support_qty} PIMP for {support_hive:.4f} HIVE")
                place_order(account_name, token, support_price, support_qty, order_type="buy", active_key=HIVE_ACTIVE_KEY, nodes=HIVE_NODES)
                cancel_triggered = True
                time.sleep(6)
        
        # === PEK GAS PURCHASES ===
        # if cancel_triggered:
        #     pek_market = get_orderbook_top("PEK")
        #     pek_ask = pek_market["lowestAsk"] if pek_market and pek_market["lowestAsk"] > 0 else 1.0
        #     print(f"[GAS] Buying PEK for transaction fees")
        #     place_order(account_name, "PEK", pek_ask, 0.00000001, order_type="buy", active_key=HIVE_ACTIVE_KEY, nodes=HIVE_NODES)
        
        # === ORDER MANAGEMENT ===
        # Cancel orders every 3rd cycle
        if cycle_count % 3 == 0:
            try:
                print(f"[CLEANUP] Canceling old orders (Cycle {cycle_count})")
                subprocess.run(["python", "pimp_cancel.py", "--once"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Failed to execute pimp_cancel.py: {e}")
                
    except Exception as e:
        print(f"[ERROR] Exception in pimp_logic: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    while True:
        print("[INFO] Running market stabilization logic.")
        pimp_logic(HIVE_ACCOUNT, TOKEN)
        print("[INFO] Waiting for 15 minutes before the next cycle.")
        time.sleep(900)  # Wait for 15 minutes (900 seconds)
