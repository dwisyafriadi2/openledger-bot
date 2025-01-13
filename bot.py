import json
import threading
import time
import random
import requests
from websocket import WebSocketApp

# Load token from file
def read_token(file_path="token.txt"):
    try:
        with open(file_path, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None

# Load proxy from file
def read_proxy(file_path="proxylist.txt"):
    try:
        with open(file_path, "r") as file:
            proxy = file.read().strip()
        return proxy if proxy else None
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None

# Define the WebSocket URL dynamically using the token
def get_websocket_url():
    token = read_token()
    if not token:
        print("Token not found. Exiting.")
        exit(1)
    return f"wss://apitn.openledger.xyz/ws/v1/orch?authToken={token}"

# Load address from file
def read_address(file_path="address.txt"):
    try:
        with open(file_path, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return ""

# Daily check-in logic
def daily_check_in():
    token = read_token()
    proxy = read_proxy()
    if not token:
        print("Token not found. Cannot perform daily check-in.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    proxies = {"http": proxy, "https": proxy} if proxy else None

    # Check claim details
    claim_details_url = "https://rewardstn.openledger.xyz/api/v1/claim_details"
    try:
        response = requests.get(claim_details_url, headers=headers, proxies=proxies)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "SUCCESS" and not data["data"].get("claimed"):
            # Attempt to claim the reward
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

# Fetch Identity from workers API
def fetch_identity():
    token = read_token()
    proxy = read_proxy()
    if not token:
        print("Token not found. Cannot fetch identity.")
        return None

    url = "https://apitn.openledger.xyz/api/v1/users/workers"
    headers = {"Authorization": f"Bearer {token}"}
    proxies = {"http": proxy, "https": proxy} if proxy else None
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

# Define the heartbeat payload
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

# Fetch total heartbeats from the reward API
def fetch_total_heartbeats():
    token = read_token()
    proxy = read_proxy()
    if not token:
        print("Token not found. Cannot fetch total heartbeats.")
        return 0

    url = "https://rewardstn.openledger.xyz/api/v1/reward_realtime"
    headers = {"Authorization": f"Bearer {token}"}
    proxies = {"http": proxy, "https": proxy} if proxy else None
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

# Fetch reward information from the reward API
def fetch_reward_info():
    token = read_token()
    proxy = read_proxy()
    if not token:
        print("Token not found. Cannot fetch reward info.")
        return 0, 0

    url = "https://rewardstn.openledger.xyz/api/v1/reward"
    headers = {"Authorization": f"Bearer {token}"}
    proxies = {"http": proxy, "https": proxy} if proxy else None
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

# Define WebSocket callbacks
def on_open(ws):
    print("Connected to WebSocket.")

    def send_heartbeat():
        identity = fetch_identity()
        owner_address = read_address()
        if not identity or not owner_address:
            print("Missing identity or owner address. Cannot send heartbeat.")
            ws.close()
            return

        current_points, _ = fetch_reward_info()

        while True:
            try:
                payload = create_heartbeat_payload(identity, owner_address)
                ws.send(json.dumps(payload))
                print("Sent heartbeat:", payload)

                # Fetch total heartbeats after sending a heartbeat
                total_heartbeats = fetch_total_heartbeats()
                combined_points = current_points + total_heartbeats
                print(f"Current Points: {current_points} + Total Heartbeats: {total_heartbeats} = Total Points: {combined_points}")

                time.sleep(30)  # Send heartbeat every 30 seconds
            except Exception as e:
                print(f"Error during heartbeat process: {e}")
                ws.close()
                break

    # Start a thread to send heartbeats periodically
    threading.Thread(target=send_heartbeat, daemon=True).start()

def on_message(ws, message):
    print("Received message:", message)

def on_error(ws, error):
    print("WebSocket error:", error)
    print("Attempting to reconnect...")
    time.sleep(5)
    main()  # Reconnect WebSocket

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed. Code:", close_status_code, "Message:", close_msg)
    print("Attempting to reconnect...")
    time.sleep(5)
    main()  # Reconnect WebSocket

# Main function to connect to the WebSocket
def main():
    daily_check_in()  # Perform daily check-in before starting WebSocket

    websocket_url = get_websocket_url()
    ws = WebSocketApp(
        websocket_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    # Run WebSocket connection
    ws.run_forever()

if __name__ == "__main__":
    main()
