import requests
import time

def send_pek(username, amount):
    print(f"Sending {amount} PEK to {username}")

def main():
    rewarded_txids = set()
    while True:
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
        r = requests.post("https://api.hive-engine.com/rpc/contracts", json=payload)
        data = r.json()
        for t in data.get("result", []):
            txid = t.get("transactionId")
            to_user = t.get("to")
            pimp_amt = float(t.get("quantity", 0))
            pek_amt = int(pimp_amt // 100) * 0.00000001
            if pek_amt > 0 and txid not in rewarded_txids:
                send_pek(to_user, pek_amt)
                rewarded_txids.add(txid)
        time.sleep(60)

if __name__ == "__main__":
    main()