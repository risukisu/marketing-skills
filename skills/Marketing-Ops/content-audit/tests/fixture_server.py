"""Serve tests/fixture_site on a random local port for the tests and the evals.

    python tests/fixture_server.py        prints the URL and serves until Ctrl+C

robots.txt and sitemap.xml have {HOST} replaced with the request's Host header so the Sitemap
line and the <loc> entries are absolute. The site is fictional ("Quillbridge").
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

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path in TEMPLATED:
            host = self.headers.get("Host", "localhost")
            data = (SITE / self.path.lstrip("/")).read_text(encoding="utf-8").replace("{HOST}", host).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", TEMPLATED[self.path])
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return None
        return super().do_GET()


class FixtureServer:
    def __init__(self, port: int = 0):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/"

    def __enter__(self):
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
    with FixtureServer(port) as s:
        print(f"Serving {SITE} at {s.url}index.html (Ctrl+C to stop)")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
