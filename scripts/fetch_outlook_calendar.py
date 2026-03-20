import requests
import os
import sys

try:
    import msal
except ImportError:
    print("msal package not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "msal"])
    import msal

# Set these with your Azure app registration details
CLIENT_ID = os.getenv('MS_CLIENT_ID') or 'YOUR_CLIENT_ID_HERE'
TENANT_ID = os.getenv('MS_TENANT_ID') or 'common'  # or your tenant id
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["Calendars.Read"]

GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0/me/events"

def get_token():
    token = os.getenv('MS_GRAPH_TOKEN')
    if token:
        print("Using token from environment variable.")
        return token
    # Device code flow
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
    flow = app.initiate_device_flow(scopes=SCOPE)
    if 'user_code' not in flow:
        raise Exception("Failed to create device flow. Check your client ID and tenant ID.")
    print(f"To sign in, use a web browser to open {flow['verification_uri']} and enter the code: {flow['user_code']}")
    sys.stdout.flush()
    result = app.acquire_token_by_device_flow(flow)
    if 'access_token' in result:
        print("Successfully obtained access token.")
        return result['access_token']
    else:
        print(f"Failed to obtain token: {result}")
        return None

def get_outlook_calendar_events(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    print("Requesting calendar events...")
    response = requests.get(GRAPH_API_ENDPOINT, headers=headers)
    print(f"HTTP status: {response.status_code}")
    if response.status_code == 200:
        print("Successfully fetched events.")
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def main():
    token = get_token()
    if not token:
        print("No access token available. Exiting.")
        return
    events = get_outlook_calendar_events(token)
    if events:
        print("Fetched events:")
        for event in events.get('value', []):
            print(f"Subject: {event.get('subject')}")
            print(f"Start: {event.get('start', {}).get('dateTime')}")
            print(f"End: {event.get('end', {}).get('dateTime')}")
            print("-")
    else:
        print("No events found or error occurred.")

if __name__ == "__main__":
    main()
