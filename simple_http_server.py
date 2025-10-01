#!/usr/bin/env python3
"""
Simple HTTP server to serve the WebSocket test page
"""

import http.server
import socketserver
import os

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

def main():
    PORT = 8080
    
    # Change to the directory containing our files
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🌐 HTTP server started on http://localhost:{PORT}")
        print(f"📄 Test page: http://localhost:{PORT}/test_websocket.html")
        print("🔄 Server running... Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 HTTP server stopped by user")

if __name__ == "__main__":
    main()
