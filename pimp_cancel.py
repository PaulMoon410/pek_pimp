import time
from place_order import cancel_order, get_open_orders
from fetch_market import get_orderbook_top

def cancel_one_order(account_name, active_key, nodes=None):
    """
    Cancel one open order for the given account using the TX ID.
    """
    try:
        sell_orders = get_open_orders(account_name)
        if sell_orders:
            tx_id = sell_orders[0].get('txId')  # Get the TX ID of the first order in the list
            if tx_id:
                print(f"[INFO] Cancelling order with TX ID: {tx_id}")
                cancel_order(account_name, tx_id, active_key=active_key, nodes=nodes)
                print(f"[INFO] Order with TX ID {tx_id} cancelled successfully.")
            else:
                print("[INFO] No valid TX ID found to cancel.")
        else:
            print("[INFO] No open orders to cancel.")
    except Exception as e:
        print(f"[ERROR] Failed to cancel order: {e}")

def read_bot_info(file_path):
    """
    Reads the bot credentials (account name and active key) from a file.
    The file should have two lines:
    - First line: Hive account name
    - Second line: Hive active key
    """
    try:
        with open(file_path, "r") as file:
            lines = file.read().splitlines()
            if len(lines) >= 2:
                return lines[0], lines[1]  # Return account name and active key
            else:
                print(f"[ERROR] Invalid bot_info.txt format. Expected 2 lines, got {len(lines)}.")
    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
    except Exception as e:
        print(f"[ERROR] Failed to read bot info: {e}")
    return None, None

if __name__ == "__main__":
    import sys
    # Read credentials from bot_info.txt
    HIVE_ACCOUNT, HIVE_ACTIVE_KEY = read_bot_info("bot_info.txt")
    HIVE_NODES = ["https://api.hive.blog", "https://anyx.io"]

    if not HIVE_ACCOUNT or not HIVE_ACTIVE_KEY:
        print("[ERROR] Missing Hive account credentials. Please check bot_info.txt.")
    else:
        # Check if called with --once argument (from pek_pimp.py)
        if len(sys.argv) > 1 and sys.argv[1] == "--once":
            print(f"[INFO] Checking for open orders to cancel for account: {HIVE_ACCOUNT}")
            cancel_one_order(HIVE_ACCOUNT, HIVE_ACTIVE_KEY, nodes=HIVE_NODES)
        else:
            # Normal standalone mode - run continuously
            while True:
                print(f"[INFO] Checking for open orders to cancel for account: {HIVE_ACCOUNT}")
                cancel_one_order(HIVE_ACCOUNT, HIVE_ACTIVE_KEY, nodes=HIVE_NODES)
                print("[INFO] Waiting for 5 minutes before the next cycle.")
                time.sleep(300)  # Wait for 5 minutes