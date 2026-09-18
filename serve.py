#!/usr/bin/env python3
"""Static host for the trailer, with byte-range support.

Python's stdlib http.server ignores Range headers and always returns 200 with
the whole file. Browsers (Safari and iOS in particular) refuse to stream an
mp4 that way, so the video plays on desktop Chrome but not on an iPhone. This
handler answers a Range request with 206 and the exact byte slice, which is
what a media element needs.
"""
from __future__ import annotations

import os
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


class RangeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        rng = self.headers.get("Range")
        if not rng:
            return super().send_head()

        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().send_head()

        m = RANGE_RE.fullmatch(rng.strip())
        if not m:
            return super().send_head()

        size = os.path.getsize(path)
        start_s, end_s = m.group(1), m.group(2)
        if start_s == "":
            # suffix range: last N bytes
            length = int(end_s)
            start = max(0, size - length)
            end = size - 1
        else:
            start = int(start_s)
            end = int(end_s) if end_s else size - 1
            end = min(end, size - 1)

        if start > end or start >= size:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return None

        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        ctype = self.guess_type(path)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        self._range = (f, end - start + 1)
        return f

    def copyfile(self, source, outputfile):
        rng = getattr(self, "_range", None)
        if not rng:
            return super().copyfile(source, outputfile)
        f, remaining = rng
        self._range = None
        try:
            while remaining > 0:
                chunk = f.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        finally:
            f.close()

    def end_headers(self):
        if "Accept-Ranges" not in self._headers_buffer_bytes():
            self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def _headers_buffer_bytes(self) -> str:
        try:
            return b"".join(self._headers_buffer).decode("latin-1")
        except Exception:
            return ""


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    ThreadingHTTPServer(("0.0.0.0", port), RangeHandler).serve_forever()
