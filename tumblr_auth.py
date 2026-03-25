"""
tumblr_auth.py
==============
One-time script to get Tumblr OAuth token and secret.
Run: python tumblr_auth.py
Browser will open, login and allow access.
oauth_token and oauth_secret will be printed.
"""

import sys
import webbrowser
import requests
from requests_oauthlib import OAuth1
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

CONSUMER_KEY = "gWb3QNfX3g0De8ffPp8bpHKyDmFIELUvetYPy0HMzfFoBFf6x8"
CONSUMER_SECRET = "HGrIgflZXISd2IFpGZug3R74l8snNZaS3cqUEYVU9HeQG8Sjp6"

REQUEST_TOKEN_URL = "https://www.tumblr.com/oauth/request_token"
AUTHORIZE_URL = "https://www.tumblr.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://www.tumblr.com/oauth/access_token"
CALLBACK_URL = "http://localhost:8080"

oauth_verifier = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global oauth_verifier
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "oauth_verifier" in params:
            oauth_verifier = params["oauth_verifier"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Tumblr Authorization successful! You can close this tab.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h2>Error: no verifier received.</h2>")

    def log_message(self, format, *args):
        pass


def main():
    print("\n" + "="*60)
    print("  TUMBLR OAUTH2 SETUP")
    print("="*60)

    # Step 1: Get request token
    oauth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, callback_uri=CALLBACK_URL)
    resp = requests.post(REQUEST_TOKEN_URL, auth=oauth)
    if resp.status_code != 200:
        print(f"[ERROR] Could not get request token: {resp.text}")
        sys.exit(1)

    creds = urllib.parse.parse_qs(resp.text)
    resource_owner_key = creds["oauth_token"][0]
    resource_owner_secret = creds["oauth_token_secret"][0]

    # Step 2: Open browser for authorization
    auth_url = f"{AUTHORIZE_URL}?oauth_token={resource_owner_key}"
    print(f"\nOpening browser... Login with your Tumblr account and click Allow.")
    print(f"\nIf browser does not open, copy this URL:\n{auth_url}\n")
    webbrowser.open(auth_url)

    # Step 3: Start local server to catch callback
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.timeout = 300
    server.handle_request()
    server.server_close()

    if not oauth_verifier:
        print("[ERROR] No verifier received. Try again.")
        sys.exit(1)

    # Step 4: Exchange for access token
    oauth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, resource_owner_key, resource_owner_secret, verifier=oauth_verifier)
    resp = requests.post(ACCESS_TOKEN_URL, auth=oauth)
    if resp.status_code != 200:
        print(f"[ERROR] Could not get access token: {resp.text}")
        sys.exit(1)

    creds = urllib.parse.parse_qs(resp.text)
    oauth_token = creds["oauth_token"][0]
    oauth_secret = creds["oauth_token_secret"][0]

    print("="*60)
    print("  SUCCESS!")
    print("="*60)
    print(f"\noauth_token  = {oauth_token}")
    print(f"oauth_secret = {oauth_secret}")
    print("\nCopy these into blog_config.py -> TUMBLR_CONFIG")


if __name__ == "__main__":
    main()
