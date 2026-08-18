import time
import random
import string
import requests

API_URL = "https://api.mail.tm"

def random_string(length=10):
    """Generates a random string for usernames and passwords."""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def get_domain():
    """Fetches the first available domain from Mail.tm."""
    response = requests.get(f"{API_URL}/domains")
    if response.status_code == 200 and response.json().get('hydra:member'):
        return response.json()['hydra:member'][0]['domain']
    raise Exception("Failed to fetch available domains.")

def create_account(email, password):
    """Creates a temporary account on Mail.tm."""
    payload = {"address": email, "password": password}
    response = requests.post(f"{API_URL}/accounts", json=payload)
    if response.status_code == 201:
        return True
    raise Exception(f"Failed to create account: {response.text}")

def get_token(email, password):
    """Logs into the account and returns a Bearer JWT Token."""
    payload = {"address": email, "password": password}
    response = requests.post(f"{API_URL}/token", json=payload)
    if response.status_code == 200:
        return response.json().get("token")
    raise Exception("Failed to obtain authentication token.")

def check_inbox(token):
    """Fetches incoming messages using the Bearer token."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/messages", headers=headers)
    if response.status_code == 200:
        return response.json().get("hydra:member", [])
    return []

def fetch_message_body(token, message_id):
    """Retrieves full text/HTML content of a single email."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/messages/{message_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def main():
    try:
        # 1. Setup account credentials
        domain = get_domain()
        username = random_string(10)
        password = random_string(12)
        email_address = f"{username}@{domain}"
        
        # 2. Register account and get authorization token
        create_account(email_address, password)
        token = get_token(email_address, password)
        
        print(f"📬 Generated Temp Email: {email_address}")
        print("Waiting for incoming emails... (Press Ctrl+C to exit)\n")

        seen_ids = set()

        # 3. Continuous inbox polling loop
        while True:
            messages = check_inbox(token)
            
            for msg in messages:
                msg_id = msg.get("id")
                if msg_id not in seen_ids:
                    seen_ids.add(msg_id)
                    
                    # Fetch detailed message body
                    details = fetch_message_body(token, msg_id)
                    if details:
                        print("=" * 50)
                        print(f"📩 New Message Received!")
                        print(f"From:    {msg.get('from', {}).get('address', 'Unknown')}")
                        print(f"Subject: {msg.get('subject', '(No Subject)')}")
                        print("-" * 50)
                        # Mail.tm returns body text if available, fallback to html snippet
                        body = details.get('text') or details.get('intro', '')
                        print(f"Body:\n{body.strip()}")
                        print("=" * 50 + "\n")
            
            time.sleep(5)  # Poll every 5 seconds
            
    except KeyboardInterrupt:
        print("\n👋 Script stopped. Your temporary inbox has been abandoned.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
