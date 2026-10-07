"""Serve tests/fixture_site on a random local port for the crawler tests and the evals.

    python tests/fixture_server.py        prints the URL and serves until Ctrl+C

Adds what a static server cannot: /moved.html answers 301 to /pricing.html, /truncated.html
announces more bytes than it sends, and robots.txt and sitemap.xml have {HOST} replaced with
the request's Host header so the Sitemap line and the <loc> entries are absolute.
"""
from __future__ import annotations

import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SITE = Path(__file__).resolve().parent / "fixture_site"
TEMPLATED = {"/robots.txt": "text/plain", "/sitemap.xml": "application/xml"}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE), **kwargs)

    def log_message(self, *args):  # keep test output clean
        pass

    def _redirect(self):
        self.send_response(301)
        self.send_header("Location", "/pricing.html")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _templated(self, send_body: bool):
        host = self.headers.get("Host", "localhost")
        body = (SITE / self.path.lstrip("/")).read_text(encoding="utf-8").replace("{HOST}", host)
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", TEMPLATED[self.path])
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if send_body:
            self.wfile.write(data)

    def _truncated(self):
        """Announces 1000 bytes and sends 10: the client sees http.client.IncompleteRead."""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", "1000")
        self.end_headers()
        self.wfile.write(b"<html>cut")
        self.wfile.flush()
        self.close_connection = True

    def do_GET(self):
        if self.path == "/truncated.html":
            return self._truncated()
        if self.path == "/moved.html":
            return self._redirect()
        if self.path in TEMPLATED:
            return self._templated(send_body=True)
        return super().do_GET()

    def do_HEAD(self):
        if self.path == "/moved.html":
            return self._redirect()
        if self.path in TEMPLATED:
            return self._templated(send_body=False)
        return super().do_HEAD()


class FixtureServer:
    """Context manager: `with FixtureServer() as s: crawl(s.url)`."""

    def __enter__(self):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/"
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()


if __name__ == "__main__":
    with FixtureServer() as server:
        print(f"Fixture site at {server.url}  (Ctrl+C to stop)")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
