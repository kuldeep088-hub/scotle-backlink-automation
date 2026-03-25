"""
blogger_auth.py
===============
One-time script to get a Blogger OAuth2 refresh_token.
Run: python blogger_auth.py
Browser will open automatically, login and allow access.
refresh_token will be printed — paste it into blog_config.py.
"""

import sys
import socket
import threading
import webbrowser
import requests
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

CLIENT_ID = "43038046964-laemll1tl5p05ftqpbg67irco57rc1u8.apps.googleusercontent.com"
CLIENT_SECRET = "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"

SCOPE = "https://www.googleapis.com/auth/blogger"
REDIRECT_URI = "http://localhost:8080"
AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Authorization successful! You can close this tab.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h2>Error: no code received.</h2>")

    def log_message(self, format, *args):
        pass  # suppress server logs


def main():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)

    print("\n" + "="*60)
    print("  BLOGGER OAUTH2 SETUP")
    print("="*60)
    print("\nOpening browser... Login with enquiry@scotlehighschool.com and click Allow.")
    print("Waiting for authorization...\n")

    # Start local server to catch the redirect
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.timeout = 300

    print(f"\nIf browser does not open, copy this URL manually:\n{url}\n")
    webbrowser.open(url)

    # Wait for callback
    server.handle_request()
    server.server_close()

    if not auth_code:
        print("[ERROR] No authorization code received. Try again.")
        sys.exit(1)

    # Exchange code for tokens
    resp = requests.post(TOKEN_URL, data={
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    })

    data = resp.json()

    if resp.status_code == 200 and "refresh_token" in data:
        print("="*60)
        print("  SUCCESS!")
        print("="*60)
        print(f"\nrefresh_token = {data['refresh_token']}")
        print("\nCopy this into blog_config.py -> BLOGGER_CONFIG -> refresh_token")
        print("Then set enabled: True\n")
    else:
        print(f"\n[ERROR] {data}\n")


if __name__ == "__main__":
    main()
