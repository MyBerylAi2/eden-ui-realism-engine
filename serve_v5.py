#!/usr/bin/env python3
"""
EDEN Realism Engine V5 Server
=============================
Serves the V5 frontend with Agentic Teams
"""

import http.server
import socketserver
import os
import webbrowser
import sys

PORT = 3007
FRONTEND_DIR = "frontend_v5"

def main():
    # Check if frontend_v5 exists
    if not os.path.exists(FRONTEND_DIR):
        print(f"❌ Error: {FRONTEND_DIR} directory not found!")
        print("Please ensure frontend_v5/index.html exists")
        sys.exit(1)
    
    os.chdir(FRONTEND_DIR)
    
    class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # Add CORS headers for API calls
            self.send_header('Access-Control-Allow-Origin', '*')
            super().end_headers()
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"""
╔════════════════════════════════════════════════════════════╗
║        🎬 EDEN REALISM ENGINE V5 - AGENTIC TEAMS           ║
╠════════════════════════════════════════════════════════════╣
║  Frontend: http://localhost:{PORT}                           ║
║  Backend:  http://localhost:8000                           ║
╠════════════════════════════════════════════════════════════╣
║  🚀 NEW IN V5:                                             ║
║  • Toast notifications for errors                          ║
║  • GPU scaling modal (click SCALE GPU)                     ║
║  • Agentic Teams panel (Kling Expert, Error Handler)       ║
║  • Auto-retry on failures                                  ║
║  • Better error logging                                    ║
╚════════════════════════════════════════════════════════════╝
        """)
        
        # Open browser
        webbrowser.open(f"http://localhost:{PORT}")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
