"""Serve this checkout locally, including byte ranges for BGM seek testing.

Run from any directory: python3 /workspace/ern/_build/serve.py --port 8767
GitHub Pages serves production; this standard-library server is for local QA.
"""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent


def byte_range(value, size):
    """Return inclusive bounds for one satisfiable bytes range, or None."""
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", value.strip(), re.IGNORECASE)
    if not match or size == 0:
        return None
    first, last = match.groups()
    try:
        if not first:
            suffix = int(last)
            return (max(0, size - suffix), size - 1) if suffix > 0 else None
        start = int(first)
        end = min(int(last), size - 1) if last else size - 1
    except ValueError:
        return None
    return (start, end) if 0 <= start <= end < size else None


class RangeRequestHandler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".mp3": "audio/mpeg"}
    protocol_version = "HTTP/1.1"

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def send_head(self):
        self._remaining = None
        path = Path(self.translate_path(self.path))
        # SimpleHTTPRequestHandler normalizes traversal; also reject symlinks
        # that lead outside the served checkout.
        try:
            checked = path
            if path.is_dir():
                for name in ("index.html", "index.htm"):
                    if (path / name).is_file():
                        checked = path / name
                        break
            if not checked.resolve().is_relative_to(Path(self.directory).resolve()):
                self.send_error(403, "Path outside the served directory")
                return None
        except (OSError, RuntimeError):
            self.send_error(404, "File not found")
            return None

        requested = self.headers.get("Range")
        if requested is None or not path.is_file():
            return super().send_head()

        try:
            source = path.open("rb")
        except OSError:
            self.send_error(404, "File not found")
            return None

        try:
            stat = os.fstat(source.fileno())
            bounds = byte_range(requested, stat.st_size)
            if bounds is None:
                source.close()
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{stat.st_size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return None

            start, end = bounds
            self._remaining = end - start + 1
            source.seek(start)
            self.send_response(206)
            self.send_header("Content-Type", self.guess_type(str(path)))
            self.send_header("Content-Range", f"bytes {start}-{end}/{stat.st_size}")
            self.send_header("Content-Length", str(self._remaining))
            self.send_header("Last-Modified", self.date_time_string(stat.st_mtime))
            self.end_headers()
            return source
        except Exception:
            source.close()
            raise

    def copyfile(self, source, outputfile):
        try:
            if self._remaining is None:
                return super().copyfile(source, outputfile)
            while self._remaining:
                chunk = source.read(min(64 * 1024, self._remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                self._remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            # Browsers cancel an in-flight media request when seeking.
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--bind", default="0.0.0.0")
    args = parser.parse_args()
    handler = partial(RangeRequestHandler, directory=str(ROOT))
    with ThreadingHTTPServer((args.bind, args.port), handler) as server:
        print(f"Serving {ROOT} on {args.bind}:{args.port} with byte ranges", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
