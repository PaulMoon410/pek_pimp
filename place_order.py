import requests
from beem import Hive
from beem.account import Account

def place_order(account_name, token, price, quantity, order_type="buy", active_key=None, nodes=None):
    hive = Hive(keys=[active_key], node=nodes or ["https://api.hive.blog"])
    contract_payload = {
        "contractName": "market",
        "contractAction": "buy" if order_type == "buy" else "sell",
        "contractPayload": {
            "symbol": token,
            "quantity": str(quantity),
            "price": str(price)
        }
    }
    try:
        tx = hive.custom_json(
            id="ssc-mainnet-hive",
            json_data=contract_payload,
            required_auths=[account_name],
            required_posting_auths=[]
        )
        print(f"[DEBUG] Placed {order_type.upper()} order: {quantity} {token} at {price}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to place order: {e}")
        return False

def get_open_orders(account_name, token=None, nodes=None):
    """
    Fetch open orders for a specific account from BOTH buy and sell order books.
    The buyBook and sellBook contain all market orders, filtered by account.
    """
    url = "https://api.hive-engine.com/rpc/contracts"
    all_orders = []
    
    # Fetch both buy and sell orders by filtering the order books by account
    for table in ["buyBook", "sellBook"]:
        offset = 0
        page_size = 1000
        while True:
            query = {"account": account_name}
            if token:
                query["symbol"] = token
            
            payload = {
                "jsonrpc": "2.0",
                "method": "find",
                "params": {
                    "contract": "market",
                    "table": table,
                    "query": query,
                    "limit": page_size,
                    "offset": offset
                },
                "id": 1
            }
            try:
                resp = requests.post(url, json=payload, timeout=10)
                if resp.status_code != 200:
                    print(f"[ERROR] Failed to fetch {table} orders (status {resp.status_code})")
                    break
                data = resp.json()
                orders = data.get('result', [])
                
                # Add order type to each order
                for order in orders:
                    order['type'] = 'buy' if table == 'buyBook' else 'sell'
                
                all_orders.extend(orders)
                if len(orders) < page_size:
                    break
                offset += page_size
            except Exception as e:
                print(f"[ERROR] Exception while fetching {table} orders: {e}")
                break
    
    buy_count = sum(1 for o in all_orders if o.get('type') == 'buy')
    sell_count = sum(1 for o in all_orders if o.get('type') == 'sell')
    print(f"[DEBUG] Retrieved {len(all_orders)} open orders ({buy_count} buys, {sell_count} sells)")
    return all_orders

def get_balance(account_name, token):
    url = "https://api.hive-engine.com/rpc/contracts"
    payload = {
        "jsonrpc": "2.0",
        "method": "findOne",
        "params": {
            "contract": "tokens",
            "table": "balances",
            "query": {"account": account_name, "symbol": token}
        },
        "id": 1
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            result = data.get("result")
            if result and "balance" in result:
                balance = float(result["balance"])
                print(f"[DEBUG] Balance for {token}: {balance}")
                return balance
    except Exception as e:
        print(f"[ERROR] Failed to fetch balance: {e}")
    return 0.0

def cancel_order(account_name, order_id, active_key=None, nodes=None):
    """
    Cancels an order on the Hive Engine blockchain.
    """
    hive = Hive(keys=[active_key], node=nodes or ["https://api.hive.blog"])
    contract_payload = [
        {
            "contractName": "market",
            "contractAction": "cancel",
            "contractPayload": {
                "type": "sell",
                "id": str(order_id)
            }
        }
    ]
    try:
        tx = hive.custom_json(
            id="ssc-mainnet-hive",
            json_data=contract_payload,
            required_auths=[account_name],
            required_posting_auths=[]
        )
        print(f"[DEBUG] Canceled order {order_id} for account {account_name}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to cancel order {order_id}: {e}")
        return False
