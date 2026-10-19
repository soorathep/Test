"""Local read-only media preview with byte ranges for browser seeking."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import re


class Handler(SimpleHTTPRequestHandler):
    def send_head(self):
        self.byte_range = None
        path = Path(self.translate_path(self.path))
        value = self.headers.get('Range')
        if not value or not path.is_file():
            return super().send_head()
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', value)
        size = path.stat().st_size
        if not match or not any(match.groups()) or not size:
            self.send_error(416)
            return None
        a, b = match.groups()
        start = int(a) if a else max(0, size - int(b))
        end = min(int(b), size - 1) if a and b else size - 1
        if start >= size or start > end:
            self.send_response(416)
            self.send_header('Content-Range', f'bytes */{size}')
            self.end_headers()
            return None
        source = path.open('rb')
        source.seek(start)
        self.byte_range = (start, end)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(str(path)))
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Accept-Ranges', 'bytes')
        self.end_headers()
        return source

    def end_headers(self):
        if not self.byte_range:
            self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()

    def copyfile(self, source, destination):
        if self.byte_range is None:
            return super().copyfile(source, destination)
        left = self.byte_range[1] - self.byte_range[0] + 1
        try:
            while left:
                block = source.read(min(left, 64 * 1024))
                if not block:
                    break
                destination.write(block)
                left -= len(block)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('--port', type=int, default=8812)
    args = parser.parse_args()
    os.chdir(args.directory)
    print(f'Preview PID {os.getpid()}, http://127.0.0.1:{args.port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
