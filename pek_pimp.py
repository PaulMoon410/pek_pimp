import requests
import time
import os
from nectar import Hive 

hive = Hive()

def send_pek(username, amount):
    # Replace these with your Hive account and private active key
    HIVE_ACCOUNT = "your_hive_account"
    ACTIVE_KEY = "your_private_active_key"  # NEVER share or hardcode in public code!

    # Prepare the custom_json payload for Hive Engine token transfer
    json_data = [
        "transfer",
        {
            "symbol": "PEK",
            "to": username,
            "quantity": f"{amount:.8f}",
            "memo": "PIMP reward"
        }
    ]
    try:
        tx = hive.broadcast_custom_json(
            username=HIVE_ACCOUNT,
            key=ACTIVE_KEY,
            id="ssc-mainnet-hive",
            json_data=json_data,
            required_posting_auths=[],
            required_active_auths=[HIVE_ACCOUNT]
        )
        print(f"Sent {amount} PEK to {username}. TX: {tx}")
    except Exception as e:
        print(f"Failed to send PEK to {username}: {e}")

REWARDED_TXIDS_FILE = "rewarded_txids.txt"

def load_rewarded_txids():
    if not os.path.exists(REWARDED_TXIDS_FILE):
        return set()
    with open(REWARDED_TXIDS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_rewarded_txid(txid):
    with open(REWARDED_TXIDS_FILE, "a") as f:
        f.write(txid + "\n")

def main():
    rewarded_txids = load_rewarded_txids()
    while True:
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "find",
                "params": {
                    "contract": "tokens",
                    "table": "transfers",
                    "query": {"symbol": "PIMP"},
                    "limit": 100,
                    "sort": "desc"
                }
            }
            r = requests.post("https://api.hive-engine.com/rpc/contracts", json=payload, timeout=10)
            data = r.json()
            for t in data.get("result", []):
                txid = t.get("transactionId")
                to_user = t.get("to")
                pimp_amt = float(t.get("quantity", 0))
                # Integer division: every 100 PIMP, reward 0.00000001 PEK
                pek_amt = int(pimp_amt // 100) * 0.00000001
                if pek_amt > 0 and txid not in rewarded_txids:
                    send_pek(to_user, pek_amt)
                    rewarded_txids.add(txid)
                    save_rewarded_txid(txid)
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(60)  # Run every minute

if __name__ == "__main__":
    main()
