import requests
import time
import os

def read_token(file_path="token.txt"):
    """Reads the authorization token from the specified file."""
    try:
        with open(file_path, "r") as file:
            token = file.read().strip()
        return token
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None

def read_proxy(file_path="proxylist.txt"):
    """Reads a proxy from the specified file. If empty, return None."""
    try:
        with open(file_path, "r") as file:
            proxy = file.read().strip()
        return proxy if proxy else None
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None

def make_request(url, token, proxy=None):
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Bearer {token}",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
    proxies = {"http": proxy, "https": proxy} if proxy else None

    try:
        response = requests.get(url, headers=headers, proxies=proxies)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")  # Debugging line
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 420:
            print("Already collected. Moving to the next process...")
            return None
        else:
            print(f"Request failed. HTTP Status Code: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def check_referrer(token, proxy):
    """Checks if the referrer_id is null."""
    url = "https://apitn.openledger.xyz/api/v1/users/workers"
    data = make_request(url, token, proxy)
    if data and data.get("status") == 200:
        workers = data.get("data", [])
        if workers:
            referrer_id = workers[0].get("Capacity", {}).get("user", {}).get("referrer_id")
            if referrer_id is None:
                print("Referrer ID is valid (null).")
                return True
            else:
                print("Referrer ID is invalid. Please re-register with the link:")
                print("https://testnet.openledger.xyz/?referral_code=qfbrbfykvu")
                return False
        else:
            print("No workers found.")
            return False
    else:
        print("Failed to fetch referrer information.")
        return False

def claim_reward(token, proxy):
    """Claims the reward node."""
    url = "https://rewardstn.openledger.xyz/api/v1/claim_reward"
    data = make_request(url, token, proxy)
    if data and data.get("status") == "SUCCESS":
        print("--- Claim Reward ---")
        print("Reward claimed successfully!")
        print("Next claim available at:", data["data"].get("nextClaim"))
        return True
    else:
        print("Failed to claim reward or already collected.")
        return False

def claim_details(token, proxy):
    """Fetches claim details and determines the next action."""
    url = "https://rewardstn.openledger.xyz/api/v1/claim_details"
    data = make_request(url, token, proxy)
    if data and data.get("status") == "SUCCESS":
        claim_data = data.get("data", {})
        if claim_data.get("claimed"):
            print("Already claimed. Next claim available at:", claim_data.get("nextClaim"))
        else:
            print("--- Claim Details ---")
            print(f"Tier: {claim_data.get('tier')}")
            print(f"Image: {claim_data.get('image')}")
            print(f"Daily Points: {claim_data.get('dailyPoint')}")
            print(f"Next Claim: {claim_data.get('nextClaim')}")
        return claim_data.get("claimed")
    else:
        print("Failed to fetch claim details.")
        return False

def reward_realtime(token, proxy):
    """Fetches real-time reward data."""
    url = "https://rewardstn.openledger.xyz/api/v1/reward_realtime"
    while True:
        data = make_request(url, token, proxy)
        if data and data.get("status") == "SUCCESS":
            print("--- Real-time Reward Data ---")
            for entry in data.get("data", []):
                print(f"Date: {entry.get('date')}, Total Heartbeats: {entry.get('total_heartbeats')}, Total Scraps: {entry.get('total_scraps')}, Total Prompts: {entry.get('total_prompts')}")
            break
        else:
            print("Failed to fetch real-time reward data. Retrying...")
            time.sleep(5)

def reward_history(token, proxy):
    """Fetches reward history data."""
    url = "https://rewardstn.openledger.xyz/api/v1/reward_history"
    while True:
        data = make_request(url, token, proxy)
        if data and data.get("status") == "SUCCESS":
            print("--- Reward History ---")
            for entry in data.get("data", []):
                print(f"Date: {entry.get('date')}, Total Points: {entry.get('total_points')}")
                for detail in entry.get("details", []):
                    print(f"  Claim Type: {detail.get('claim_type')}, Points: {detail.get('points')}")
            break
        else:
            print("Failed to fetch reward history. Retrying...")
            time.sleep(5)

def reward_info(token, proxy):
    """Fetches reward info."""
    url = "https://rewardstn.openledger.xyz/api/v1/reward"
    while True:
        data = make_request(url, token, proxy)
        if data and data.get("status") == "SUCCESS":
            reward_data = data.get("data", {})
            print("--- Reward Information ---")
            print(f"Total Points: {reward_data.get('totalPoint')}, Current Points: {reward_data.get('point')}, Name: {reward_data.get('name')}, End Date: {reward_data.get('endDate')}")
            break
        else:
            print("Failed to fetch reward information. Retrying...")
            time.sleep(5)

def main():
    token_file = "token.txt"
    proxy_file = "proxylist.txt"

    token = read_token(token_file)
    proxy = read_proxy(proxy_file)

    if token:
        print("\n--- Checking Referrer ID ---")
        if not check_referrer(token, proxy):
            return

        print("\n--- Claiming Reward Node ---")
        claim_reward(token, proxy)

        print("\n--- Fetching Claim Details ---")
        claimed = claim_details(token, proxy)

        try:
            while True:
                print("\n--- Fetching Real-time Reward Data ---")
                reward_realtime(token, proxy)
                print("\n--- Fetching Reward History ---")
                reward_history(token, proxy)
                print("\n--- Fetching Reward Info ---")
                reward_info(token, proxy)
                print("Looping processes... Press Ctrl + C to exit.")
                time.sleep(10)  # Add a short delay between loops
        except KeyboardInterrupt:
            print("\nExiting loop. Goodbye!")
    else:
        print("Authorization token is missing. Please check your token file.")

if __name__ == "__main__":
    main()
