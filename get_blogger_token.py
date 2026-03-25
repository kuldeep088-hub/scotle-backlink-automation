"""
get_blogger_token.py
====================
One-time script to get a Blogger OAuth refresh token.
Opens browser, catches the callback on localhost:8080, saves the token.

Run: python get_blogger_token.py
"""

import json
import threading
import webbrowser
import urllib.parse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

CLIENT_ID     = "327240008337-180q6dek8mmv41gsqddkk4lp4s76t05c.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URI  = "http://localhost:8080"
SCOPE         = "https://www.googleapis.com/auth/blogger"

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        auth_code = params.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        if auth_code:
            self.wfile.write(b"<h2>Authorization successful!</h2><p>You can close this tab now.</p>")
        else:
            self.wfile.write(b"<h2>No code received. Try again.</h2>")

    def log_message(self, format, *args):
        pass  # suppress server logs


def exchange_code(code):
    data = urllib.parse.urlencode({
        "code":          code,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri":  REDIRECT_URI,
        "grant_type":    "authorization_code",
    }).encode()

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    # Build auth URL with localhost redirect
    params = urllib.parse.urlencode({
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         SCOPE,
        "access_type":   "offline",
        "prompt":        "consent",
    })
    auth_url = "https://accounts.google.com/o/oauth2/auth?" + params

    # Start local server
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.timeout = 120

    print("=" * 55)
    print("  BLOGGER TOKEN SETUP")
    print("=" * 55)
    print()
    print("Opening browser... Sign in with enquiry@scotlehighschool.com")
    print("(If browser doesn't open, copy this URL manually)")
    print()
    print(auth_url)
    print()

    webbrowser.open(auth_url)

    print("Waiting for authorization...")
    server.handle_request()

    if not auth_code:
        print("ERROR: No auth code received. Try again.")
        return

    print("Got auth code. Exchanging for refresh token...")

    try:
        tokens = exchange_code(auth_code)
    except Exception as e:
        print(f"ERROR exchanging code: {e}")
        return

    refresh_token = tokens.get("refresh_token", "")
    if not refresh_token:
        print("ERROR: No refresh_token in response.")
        print("Response:", tokens)
        return

    print()
    print("=" * 55)
    print("  SUCCESS!")
    print("=" * 55)
    print()
    print("Refresh token:")
    print(refresh_token)
    print()
    print("Copy this token and paste it into blog_config.py:")
    print('  BLOGGER_CONFIG["refresh_token"] = "<paste here>"')


if __name__ == "__main__":
    main()
