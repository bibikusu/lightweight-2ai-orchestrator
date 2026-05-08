from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

_STATIC_DIR = Path(__file__).parent / "static"

_CONTENT_TYPES: dict = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}


class PCCHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/api/state":
            self._handle_api_state()
        elif self.path == "/" or self.path == "/index.html":
            self._serve_file(_STATIC_DIR / "index.html")
        elif self.path.startswith("/static/"):
            rel = self.path[len("/static/"):]
            self._serve_static(rel)
        else:
            self._send_404()

    def _handle_api_state(self) -> None:
        from backend.pcc.pcc_v0 import aggregate_projects

        data = aggregate_projects()
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, rel: str) -> None:
        resolved = (_STATIC_DIR / rel).resolve()
        if not str(resolved).startswith(str(_STATIC_DIR.resolve())):
            self._send_404()
            return
        self._serve_file(resolved)

    def _serve_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self._send_404()
            return
        body = path.read_bytes()
        ct = _CONTENT_TYPES.get(path.suffix, "text/plain; charset=utf-8")
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_404(self) -> None:
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        pass


def run(port: int = 8765) -> None:
    server = HTTPServer(("127.0.0.1", port), PCCHandler)
    print(f"PCC v0 running at http://127.0.0.1:{port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    run(port)
