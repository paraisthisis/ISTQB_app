#!/usr/bin/env python3
"""
tests/static_server.py
Simulates GitHub Pages for Playwright tests: serves frontend/ under the
/ISTQB_app/ sub-path with no backend (so /api/* returns 404, as on Pages).

Usage: python3 tests/static_server.py [port]   (default port 5051)
"""

import functools
import http.server
import os
import sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
PREFIX       = "/ISTQB_app/"


class PagesLikeHandler(http.server.SimpleHTTPRequestHandler):
    def _rewrite(self) -> bool:
        if self.path == PREFIX.rstrip("/"):
            self.send_response(301)
            self.send_header("Location", PREFIX)
            self.end_headers()
            return False
        if not self.path.startswith(PREFIX):
            self.send_error(404, "Not Found")
            return False
        self.path = "/" + self.path[len(PREFIX):]
        return True

    def do_GET(self):
        if self._rewrite():
            super().do_GET()

    def do_HEAD(self):
        if self._rewrite():
            super().do_HEAD()

    def log_message(self, *args):
        pass  # keep test output quiet


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5051
    handler = functools.partial(PagesLikeHandler, directory=FRONTEND_DIR)
    print(f"Serving {FRONTEND_DIR} at http://localhost:{port}{PREFIX}")
    http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
