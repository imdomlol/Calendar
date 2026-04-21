import requests
import os
import sys
import json
import base64
import time

try:
    import msal
except ImportError:
    print("msal package not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "msal"])
    import msal

# Set these with your Azure app registration details
CLIENT_ID = os.getenv('MS_CLIENT_ID') or 'YOUR_CLIENT_ID_HERE'
TENANT_ID = os.getenv('MS_TENANT_ID') or 'common'  # use 'common' unless you need a fixed tenant
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
# Request Graph-scoped delegated permission so the token audience is Microsoft Graph.
SCOPE = ["https://graph.microsoft.com/Calendars.Read"]

GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0/me/events"
VERBOSE = os.getenv('MS_GRAPH_VERBOSE', '').strip().lower() in {'1', 'true', 'yes'}


def _print_graph_response(name, response):
    print(f"[{name}] status: {response.status_code}")
    print(f"[{name}] url: {response.url}")
    request_id = response.headers.get('request-id')
    client_request_id = response.headers.get('client-request-id')
    trace_id = response.headers.get('x-ms-ags-diagnostic')
    if request_id:
        print(f"[{name}] request-id: {request_id}")
    if client_request_id:
        print(f"[{name}] client-request-id: {client_request_id}")
    if trace_id:
        print(f"[{name}] x-ms-ags-diagnostic: {trace_id}")

    text = (response.text or '').strip()
    if text:
        print(f"[{name}] body: {text[:1200]}")
    else:
        print(f"[{name}] body: <empty>")


def _response_json_or_none(response):
    try:
        return response.json()
    except ValueError:
        return None


def decode_jwt_claims(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload = parts[1]
        padding = '=' * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload + padding)
        return json.loads(decoded.decode('utf-8'))
    except Exception:
        return None


def check_for_federated_identity(token):
    """Detect if this token is from a federated identity (e.g., GitHub, external IDP)."""
    claims = decode_jwt_claims(token)
    if not claims:
        return False
    
    # Federated identities often have an 'idp' claim indicating federation
    idp = claims.get('idp')
    
    # Check for GitHub federation patterns or any external IDP
    is_federated = idp is not None
    
    return is_federated


def print_token_diagnostics(token):
    claims = decode_jwt_claims(token)
    if not claims:
        print("Unable to decode token claims for diagnostics.")
        return

    print("Token diagnostics:")
    print(f"  aud: {claims.get('aud')}")
    print(f"  tid: {claims.get('tid')}")
    print(f"  scp: {claims.get('scp')}")
    print(f"  appid: {claims.get('appid')}")
    
    # Warn if federated identity detected
    if check_for_federated_identity(token):
        print("\n⚠️  WARNING: This account appears to be authenticated via federation.")
        print("   Federated identities may have incomplete mailbox provisioning in Graph.")
        print("   If calendar access fails, try signing in with your normal Microsoft account credentials instead.\n")

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

    interval = int(flow.get('interval', 5))
    expires_at = int(flow.get('expires_at', int(time.time()) + 900))

    pending_count = 0
    while True:
        # MSAL/urllib3 does not allow timeout <= 0.
        # Use a small positive timeout so each poll remains responsive.
        result = app.acquire_token_by_device_flow(flow, timeout=max(1, interval))
        if 'access_token' in result:
            print("Successfully obtained access token.")
            return result['access_token']

        error = result.get('error')
        if error == 'authorization_pending':
            remaining = max(0, expires_at - int(time.time()))
            print(f"Waiting for sign-in completion... ({remaining}s remaining)")
            pending_count += 1
            if pending_count == 6:
                print("Still waiting. In the browser, make sure you completed account selection and approved requested permissions.")
                print("If you only landed on an account home page, restart and use the direct link printed above.")
            time.sleep(interval)
            continue

        if error == 'slow_down':
            interval += 2
            print(f"Microsoft requested slower polling. New interval: {interval}s")
            time.sleep(interval)
            continue

        if error in {'expired_token', 'authorization_declined', 'bad_verification_code'}:
            print(f"Failed to obtain token: {error}")
            print(f"Details: {result.get('error_description')}")
            print("Start over by running the script again to get a fresh device code.")
            return None

        if int(time.time()) >= expires_at:
            print("Failed to obtain token: device code expired.")
            print("Run the script again and complete the browser flow immediately.")
            return None

        print(f"Failed to obtain token: {error}")
        print(f"Details: {result.get('error_description')}")
        return None

def get_outlook_calendar_events(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    print("Requesting calendar events...")
    params = {
        '$top': 5,
        '$select': 'id,subject,bodyPreview,start,end,organizer'
    }
    response = requests.get(GRAPH_API_ENDPOINT, headers=headers, params=params, timeout=30)
    print(f"HTTP status: {response.status_code}")
    if response.status_code == 200:
        print("Successfully fetched events.")
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        if response.status_code == 401:
            print("WWW-Authenticate:", response.headers.get('WWW-Authenticate', 'missing'))
        _print_graph_response('me/events', response)
        return None


def probe_graph_identity_and_calendar(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }

    probes = [
        ('me', 'https://graph.microsoft.com/v1.0/me'),
        ('me/calendars', 'https://graph.microsoft.com/v1.0/me/calendars'),
        ('me/calendar/events', 'https://graph.microsoft.com/v1.0/me/calendar/events'),
    ]

    print("Running Graph probes...")
    probe_results = {}
    for name, url in probes:
        try:
            response = requests.get(url, headers=headers, timeout=30)
            _print_graph_response(name, response)
            probe_results[name] = {
                'status': response.status_code,
                'json': _response_json_or_none(response),
            }
        except requests.RequestException as exc:
            print(f"[{name}] request failed: {exc}")
            probe_results[name] = {
                'status': None,
                'json': None,
            }

    return probe_results


def explain_and_detect_mailbox_issue(probe_results):
    me_result = probe_results.get('me', {})
    me_status = me_result.get('status')
    me_json = me_result.get('json') or {}

    calendars_status = probe_results.get('me/calendars', {}).get('status')
    calendar_events_status = probe_results.get('me/calendar/events', {}).get('status')

    # If identity works but every calendar endpoint is unauthorized, auth is fine and mailbox context is the issue.
    if me_status == 200 and calendars_status == 401 and calendar_events_status == 401:
        upn = (me_json.get('userPrincipalName') or '').upper()
        mail = me_json.get('mail')
        is_guest = '#EXT#' in upn

        print("Detected likely mailbox access issue:")
        print("  Graph token is valid for /me, but calendar endpoints are unauthorized.")

        if is_guest or not mail:
            print("  Signed-in user appears to be a guest or has no Exchange mailbox in this tenant.")
            print("  Fix: sign in with a tenant user that has an Exchange Online mailbox license,")
            print("  or provision/mail-enable the target user in this tenant.")
        else:
            print("  Signed-in user may not have an Exchange Online mailbox provisioned/licensed.")

        return True

    return False


def print_readiness_summary(probe_results):
    me_result = probe_results.get('me', {})
    me_status = me_result.get('status')
    me_json = me_result.get('json') or {}

    calendars_status = probe_results.get('me/calendars', {}).get('status')
    calendar_events_status = probe_results.get('me/calendar/events', {}).get('status')

    upn = me_json.get('userPrincipalName')
    display_name = me_json.get('displayName')
    mail = me_json.get('mail')
    is_guest = isinstance(upn, str) and '#EXT#' in upn.upper()

    print("\nReadiness summary:")
    print(f"  /me: {me_status}")
    print(f"  /me/calendars: {calendars_status}")
    print(f"  /me/calendar/events: {calendar_events_status}")

    if me_status == 200:
        print("  Identity check: PASS")
        print(f"  Signed-in user: {display_name} ({upn})")
    elif me_status == 403:
        print("  Identity check: WARN (403 Forbidden)")
        print("  Note: /me endpoint is blocked, but calendar endpoints may still work.")
    else:
        print("  Identity check: FAIL")
        print("  Result: API is not ready. Fix app registration/auth configuration first.")
        return {
            'api_ready': False,
            'calendar_ready_for_this_user': False,
            'reason': 'identity_failed',
        }

    if calendars_status == 200 or calendar_events_status == 200:
        print("  Calendar check: PASS")
        print("  Result: API is ready for implementation with delegated user sign-in.")
        return {
            'api_ready': True,
            'calendar_ready_for_this_user': True,
            'reason': 'calendar_access_ok',
        }

    # If identity check failed but calendar worked, still consider API ready.
    if me_status == 403 and (calendars_status == 200 or calendar_events_status == 200):
        print("  Calendar check: PASS (despite /me 403)")
        print("  Result: API is ready for implementation. Calendar access confirmed.")
        return {
            'api_ready': True,
            'calendar_ready_for_this_user': True,
            'reason': 'calendar_access_ok_despite_me_403',
        }

    if calendars_status == 401 and calendar_events_status == 401:
        print("  Calendar check: FAIL for this signed-in account")
        if is_guest or not mail:
            print("  Cause: account appears guest/no-mailbox in this tenant context.")
            print("  Interpretation: integration design is still valid; test with a mailbox-enabled account.")
            return {
                'api_ready': True,
                'calendar_ready_for_this_user': False,
                'reason': 'guest_or_no_mailbox',
            }

        print("  Cause: likely mailbox provisioning/licensing issue for this account.")
        return {
            'api_ready': True,
            'calendar_ready_for_this_user': False,
            'reason': 'mailbox_unavailable',
        }

    print("  Calendar check: INCONCLUSIVE")
    print("  Result: API partially reachable; inspect probe diagnostics above.")
    return {
        'api_ready': True,
        'calendar_ready_for_this_user': False,
        'reason': 'inconclusive',
    }

def main():
    token = get_token()
    if not token:
        print("No access token available. Exiting.")
        return
    if VERBOSE:
        print_token_diagnostics(token)
        probe_results = probe_graph_identity_and_calendar(token)
        summary = print_readiness_summary(probe_results)
        if not summary.get('calendar_ready_for_this_user'):
            print("Skipping /me/events fetch because calendar access is not available for this account.")
            return

    events = get_outlook_calendar_events(token)
    if events:
        print("Fetched events:")
        for event in events.get('value', []):
            print(f"Title: {event.get('subject')}")
            print(f"Description: {event.get('bodyPreview')}")
            print(f"Start: {event.get('start', {}).get('dateTime')}")
            print(f"End: {event.get('end', {}).get('dateTime')}")
            print("-")
    else:
        print("No events found or error occurred.")

if __name__ == "__main__":
    main()
