import json
import threading
import time
import random
import requests
from websocket import WebSocketApp

# Configure proxies to support SOCKS5
def configure_proxy(proxy):
    if proxy and proxy.startswith("socks5"):
        return {
            "http": proxy,
            "https": proxy
        }
    return None

def read_tokens_and_proxies(token_file="token.txt", proxy_file="proxylist.txt"):
    try:
        with open(token_file, "r") as tf, open(proxy_file, "r") as pf:
            tokens = [line.strip() for line in tf if line.strip()]
            proxies = [line.strip() for line in pf if line.strip()]
            if len(tokens) > len(proxies):
                print("Warning: More tokens than proxies. Some tokens will not use a proxy.")
            return tokens, proxies
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return [], []

def get_websocket_url(token):
    return f"wss://apitn.openledger.xyz/ws/v1/orch?authToken={token}"

def read_address(file_path="address.txt"):
    try:
        with open(file_path, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return ""

def daily_check_in(token, proxy=None):
    headers = {"Authorization": f"Bearer {token}"}
    proxies = configure_proxy(proxy)

    claim_details_url = "https://rewardstn.openledger.xyz/api/v1/claim_details"
    try:
        response = requests.get(claim_details_url, headers=headers, proxies=proxies)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "SUCCESS" and not data["data"].get("claimed"):
            claim_reward_url = "https://rewardstn.openledger.xyz/api/v1/claim_reward"
            claim_response = requests.get(claim_reward_url, headers=headers, proxies=proxies)
            if claim_response.status_code == 200:
                print("--- Daily Check-In ---")
                print("Daily reward claimed successfully!")
            else:
                print("Failed to claim daily reward or already claimed.")
        else:
            print("Daily reward already claimed.")
    except requests.RequestException as e:
        print(f"Error during daily check-in: {e}")

def fetch_identity(token, proxy=None):
    url = "https://apitn.openledger.xyz/api/v1/users/workers"
    headers = {"Authorization": f"Bearer {token}"}
    proxies = configure_proxy(proxy)
    try:
        response = requests.get(url, headers=headers, proxies=proxies)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == 200 and data.get("data"):
            return data["data"][0]["identity"]
        else:
            print("Failed to fetch Identity.")
            return None
    except requests.RequestException as e:
        print(f"Error fetching Identity: {e}")
        return None

def fetch_total_heartbeats(token, proxy=None):
    url = "https://rewardstn.openledger.xyz/api/v1/reward_realtime"
    headers = {"Authorization": f"Bearer {token}"}
    proxies = configure_proxy(proxy)
    try:
        response = requests.get(url, headers=headers, proxies=proxies)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "SUCCESS" and data.get("data"):
            return int(data["data"][0]["total_heartbeats"])
        else:
            print("Failed to fetch total heartbeats.")
            return 0
    except requests.RequestException as e:
        print(f"Error fetching total heartbeats: {e}")
        return 0

def fetch_reward_info(token, proxy=None):
    url = "https://rewardstn.openledger.xyz/api/v1/reward"
    headers = {"Authorization": f"Bearer {token}"}
    proxies = configure_proxy(proxy)
    try:
        response = requests.get(url, headers=headers, proxies=proxies)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "SUCCESS" and data.get("data"):
            reward_data = data["data"]
            print("--- Reward Information ---")
            print(f"Total Points: {reward_data.get('totalPoint')}, Current Points: {reward_data.get('point')}, Name: {reward_data.get('name')}, End Date: {reward_data.get('endDate')}")
            return float(reward_data.get("point", 0)), float(reward_data.get("totalPoint", 0))
        else:
            print("Failed to fetch reward info.")
            return 0, 0
    except requests.RequestException as e:
        print(f"Error fetching reward info: {e}")
        return 0, 0

def create_heartbeat_payload(identity, owner_address):
    return {
        "message": {
            "Worker": {
                "Identity": identity,
                "ownerAddress": owner_address,
                "type": "LWEXT",
                "Host": "chrome-extension://ekbbplmjjgoobhdlffmgeokalelnmjjc"
            },
            "Capacity": {
                "AvailableMemory": round(random.uniform(8, 32), 2),
                "AvailableStorage": f"{round(random.uniform(50, 500), 2)}",
                "AvailableGPU": "",
                "AvailableModels": []
            }
        },
        "msgType": "HEARTBEAT",
        "workerType": "LWEXT",
        "workerID": identity
    }

def on_open(ws, token, proxy):
    print("Connected to WebSocket.")

    def send_heartbeat():
        identity = fetch_identity(token, proxy)
        owner_address = read_address()
        if not identity or not owner_address:
            print("Missing identity or owner address. Cannot send heartbeat.")
            ws.close()
            return

        current_points, _ = fetch_reward_info(token, proxy)

        while True:
            try:
                payload = create_heartbeat_payload(identity, owner_address)
                ws.send(json.dumps(payload))
                print("Sent heartbeat:", payload)

                total_heartbeats = fetch_total_heartbeats(token, proxy)
                combined_points = current_points + total_heartbeats
                print(f"Current Points: {current_points} + Total Heartbeats: {total_heartbeats} = Total Points: {combined_points}")

                time.sleep(30)
            except Exception as e:
                print(f"Error during heartbeat process: {e}")
                ws.close()
                break

    threading.Thread(target=send_heartbeat, daemon=True).start()

def on_message(ws, message):
    print("Received message:", message)

def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed. Code:", close_status_code, "Message:", close_msg)

def start_worker(token, proxy):
    daily_check_in(token, proxy)
    websocket_url = get_websocket_url(token)
    ws = WebSocketApp(
        websocket_url,
        on_open=lambda ws: on_open(ws, token, proxy),
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

def main():
    tokens, proxies = read_tokens_and_proxies()
    threads = []

    for i, token in enumerate(tokens):
        proxy = proxies[i] if i < len(proxies) else None
        thread = threading.Thread(target=start_worker, args=(token, proxy), daemon=True)
        threads.append(thread)
        thread.start()
        time.sleep(20)  # Delay between starting WebSocket connections

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
