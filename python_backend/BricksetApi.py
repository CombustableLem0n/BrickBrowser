import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("API_KEY")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Sample LEGO set numbers to add (replace or extend this list)
set_numbers = ["10258", "75192", "21318"]

def get_user_hash(api_key, username, password):
    url = "https://brickset.com/api/v3.asmx/login"
    payload = {
        "apiKey": api_key,
        "username": username,
        "password": password
    }
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
    result = response.json()
    return result.get("hash")

def find_set_id(api_key, user_hash, set_number):
    url = "https://brickset.com/api/v3.asmx/getSets"
    payload = {
        "apiKey": api_key,
        "userHash": user_hash,
        "setNumber": set_number
    }
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
    result = response.json()
    sets = result.get("sets")
    if sets:
        return sets[0]["setID"]
    return None

def add_set_to_collection(api_key, user_hash, set_id):
    url = "https://brickset.com/api/v3.asmx/setCollection"
    payload = {
        "apiKey": api_key,
        "userHash": user_hash,
        "setID": set_id,
        "owned": True,
        "wanted": False,
        "qtyOwned": 1
    }
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
    print(f"Set ID {set_id}: {response.json().get('status')}")

def main():
    if not all([API_KEY, USERNAME, PASSWORD]):
        print("❌ Missing environment variables. Make sure your .env file is set up correctly.")
        return

    user_hash = get_user_hash(API_KEY, USERNAME, PASSWORD)
    if not user_hash:
        print("❌ Failed to authenticate. Check your API key and credentials.")
        return

    for set_number in set_numbers:
        set_id = find_set_id(API_KEY, user_hash, set_number)
        if set_id:
            add_set_to_collection(API_KEY, user_hash, set_id)
        else:
            print(f"⚠️ Set number {set_number} not found.")

if __name__ == "__main__":
    main()
