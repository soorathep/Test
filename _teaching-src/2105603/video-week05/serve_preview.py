"""Serve a local website checkout for browser and PDF review only."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import argparse
import os
import re

parser=argparse.ArgumentParser()
parser.add_argument('--site',required=True)
parser.add_argument('--port',type=int,default=8846)
args=parser.parse_args()

class PreviewServer(ThreadingHTTPServer):
    request_queue_size=128
    daemon_threads=True

class RangeHandler(SimpleHTTPRequestHandler):
    """Support byte ranges so the browser can seek within the local MP4."""
    def end_headers(self):
        self.send_header('Accept-Ranges','bytes')
        super().end_headers()

    def send_head(self):
        self.partial_bytes=None
        value=self.headers.get('Range')
        filename=self.translate_path(self.path)
        if not value or not os.path.isfile(filename):
            return super().send_head()
        match=re.fullmatch(r'bytes=(\d*)-(\d*)',value.strip())
        if not match or not any(match.groups()):
            self.send_error(416,'Unsupported byte range');return None
        stream=open(filename,'rb');size=os.fstat(stream.fileno()).st_size
        a,b=match.groups()
        if a:
            start=int(a);end=min(int(b),size-1) if b else size-1
        else:
            start=max(0,size-int(b));end=size-1
        if start>end or start>=size:
            stream.close();self.send_response(416)
            self.send_header('Content-Range',f'bytes */{size}')
            self.send_header('Content-Length','0');self.end_headers();return None
        self.send_response(206)
        self.send_header('Content-Type',self.guess_type(filename))
        self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length',str(end-start+1))
        self.end_headers();stream.seek(start);self.partial_bytes=end-start+1
        return stream

    def copyfile(self,source,outputfile):
        if self.partial_bytes is None:return super().copyfile(source,outputfile)
        remaining=self.partial_bytes
        while remaining:
            chunk=source.read(min(65536,remaining))
            if not chunk:break
            outputfile.write(chunk);remaining-=len(chunk)

handler=partial(RangeHandler,directory=args.site)
with PreviewServer(('127.0.0.1',args.port),handler) as server:
    print(f'Local review server: http://127.0.0.1:{args.port}',flush=True)
    server.serve_forever()
