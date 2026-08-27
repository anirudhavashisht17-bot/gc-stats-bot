import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is Running 24/7!")

    def log_message(self, format, *args):
        pass

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

if __name__ == "__main__":
    # Start web server thread for Render health check
    web_thread = threading.Thread(target=run_http_server, daemon=True)
    web_thread.start()
    
    # Run Telegram Bot
    subprocess.run([sys.executable, "gc_stats_bot.py"])
