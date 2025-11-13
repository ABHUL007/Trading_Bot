"""
Simple HTTP server to serve the standalone ML dashboard
No Flask, no apps - just pure HTML with live data simulation
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

# Change to the directory containing the HTML file
html_dir = Path(__file__).parent
os.chdir(html_dir)

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/standalone_ml_dashboard.html'
        return super().do_GET()

def start_dashboard():
    print("=" * 80)
    print("🚀 NIFTY ML Dashboard - Standalone Version")
    print("=" * 80)
    print("📊 Features:")
    print("  • Live price simulation with realistic movements")
    print("  • ML-identified resistance & support levels")
    print("  • Real-time breakout/breakdown alerts")
    print("  • Interactive charts and visualizations")
    print("  • No apps, no Flask - pure dashboard")
    print("=" * 80)
    print(f"🌐 Starting dashboard at http://localhost:{PORT}")
    print("💡 Dashboard will open automatically in your browser")
    print("=" * 80)
    
    # Start the server
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"✅ Server running at http://localhost:{PORT}")
        
        # Open browser
        webbrowser.open(f'http://localhost:{PORT}')
        
        print("📱 Dashboard opened! Press Ctrl+C to stop")
        print("=" * 80)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Dashboard stopped")
            httpd.shutdown()

if __name__ == "__main__":
    start_dashboard()