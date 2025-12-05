import requests
def get_orders_table_orders(account_name):
    url = "https://api.hive-engine.com/rpc/contracts"
    all_orders = []
    offset = 0
    page_size = 1000
    # Try with account filter
    while True:
        query = {"account": account_name}
        payload = {
            "jsonrpc": "2.0",
            "method": "find",
            "params": {
                "contract": "market",
                "table": "orders",
                "query": query,
                "limit": page_size,
                "offset": offset
            },
            "id": 1
        }
        print(f"[DEBUG] Querying orders table with payload: {payload}")
        resp = requests.post(url, json=payload, timeout=10)
        print(f"[DEBUG] Raw orders table response: {resp.text}")
        if resp.status_code != 200:
            print(f"[ERROR] Failed to fetch orders table for {account_name} (status {resp.status_code})")
            break
        data = resp.json()
        orders = data.get('result')
        if not isinstance(orders, list):
            orders = []
        all_orders.extend(orders)
        if len(orders) < page_size:
            break
        offset += page_size
    # Try with account and symbol filter if no results
    if not all_orders:
        offset = 0
        while True:
            query = {"account": account_name, "symbol": "PIMP"}
            payload = {
                "jsonrpc": "2.0",
                "method": "find",
                "params": {
                    "contract": "market",
                    "table": "orders",
                    "query": query,
                    "limit": page_size,
                    "offset": offset
                },
                "id": 2
            }
            print(f"[DEBUG] Querying orders table with payload: {payload}")
            resp = requests.post(url, json=payload, timeout=10)
            print(f"[DEBUG] Raw orders table response: {resp.text}")
            if resp.status_code != 200:
                print(f"[ERROR] Failed to fetch orders table for {account_name} (status {resp.status_code})")
                break
            data = resp.json()
            orders = data.get('result')
            if not isinstance(orders, list):
                orders = []
            all_orders.extend(orders)
            if len(orders) < page_size:
                break
            offset += page_size
    return all_orders
