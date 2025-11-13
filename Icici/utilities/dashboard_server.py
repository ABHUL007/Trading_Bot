#!/usr/bin/env python3
"""
Live Dashboard Data Server
Provides real-time trading data via HTTP API for the dashboard
"""

import sqlite3
import json
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import threading
import time

class DashboardDataHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests for dashboard data"""
        
        # Enable CORS
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            if self.path == '/api/bot-status':
                data = self.get_bot_status()
            elif self.path == '/api/market-data':
                data = self.get_market_data()
            elif self.path == '/api/breakouts':
                data = self.get_breakouts()
            elif self.path == '/api/trades':
                data = self.get_trades()
            elif self.path == '/api/options':
                data = self.get_options_data()
            elif self.path == '/api/all':
                data = {
                    'bot_status': self.get_bot_status(),
                    'market_data': self.get_market_data(),
                    'breakouts': self.get_breakouts(),
                    'trades': self.get_trades(),
                    'options': self.get_options_data(),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                data = {'error': 'Unknown endpoint'}
                
        except Exception as e:
            data = {'error': str(e)}
        
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def get_bot_status(self):
        """Get current bot status and statistics"""
        try:
            # Check if bot is running by looking at recent API activity
            conn = sqlite3.connect('options_data.db')
            cursor = conn.cursor()
            
            # Get recent options data to determine if bot is active
            cursor.execute("""
                SELECT COUNT(*), MAX(timestamp) 
                FROM options_data 
                WHERE timestamp > datetime('now', '-5 minutes')
            """)
            recent_activity = cursor.fetchone()
            
            conn.close()
            
            is_active = recent_activity[0] > 0 if recent_activity else False
            last_activity = recent_activity[1] if recent_activity else None
            
            return {
                'status': 'ACTIVE' if is_active else 'IDLE',
                'last_activity': last_activity,
                'api_usage': '25/95',  # Simulated for now
                'api_percentage': 26.3,
                'iteration': 24,
                'last_action': 'Monitoring positions...' if is_active else 'Waiting for signals...'
            }
            
        except Exception as e:
            return {'error': f'Bot status error: {e}'}
    
    def get_market_data(self):
        """Get current market data"""
        try:
            # Get latest NIFTY data
            conn = sqlite3.connect('NIFTY_5min_data.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT close, high, low, datetime
                FROM data_5min 
                ORDER BY datetime DESC 
                LIMIT 2
            """)
            results = cursor.fetchall()
            conn.close()
            
            if results:
                current = results[0]
                previous = results[1] if len(results) > 1 else current
                
                current_price = current[0]
                previous_price = previous[0]
                change = current_price - previous_price
                change_pct = (change / previous_price * 100) if previous_price else 0
                
                return {
                    'nifty_price': current_price,
                    'change': change,
                    'change_percent': change_pct,
                    'high': current[1],
                    'low': current[2],
                    'timestamp': current[3],
                    'atr': 142.18,  # Could calculate from historical data
                    'volatility': 'Low' if abs(change_pct) < 0.5 else 'Medium' if abs(change_pct) < 1.0 else 'High',
                    'market_phase': 'PHASE_3'
                }
            
            return {'error': 'No market data available'}
            
        except Exception as e:
            return {'error': f'Market data error: {e}'}
    
    def get_breakouts(self):
        """Get current breakout information"""
        try:
            # This would integrate with the FixedPranniMonitor
            # For now, return simulated breakout data
            breakouts = [
                {
                    'type': 'Opening Range High',
                    'level': 25438.50,
                    'probability': 85,
                    'status': 'BROKEN',
                    'timestamp': '11:45:23'
                },
                {
                    'type': 'Previous Day Low',
                    'level': 25491.75,
                    'probability': 70,
                    'status': 'BROKEN',
                    'timestamp': '11:54:52'
                },
                {
                    'type': 'EMA 50 Approach',
                    'level': 25323.43,
                    'probability': 90,
                    'status': 'APPROACHING',
                    'timestamp': 'Current'
                }
            ]
            
            return {'breakouts': breakouts}
            
        except Exception as e:
            return {'error': f'Breakouts error: {e}'}
    
    def get_trades(self):
        """Get recent trades and P&L"""
        try:
            conn = sqlite3.connect('paper_trades.db')
            cursor = conn.cursor()
            
            # Get today's trades
            cursor.execute("""
                SELECT * FROM paper_trades 
                WHERE timestamp LIKE '2025-11-07%'
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            trades = cursor.fetchall()
            
            # Calculate P&L (simplified)
            total_pl = 0
            trade_list = []
            
            for trade in trades:
                # Simulate current P&L based on live prices
                current_pl = 390  # Simulated profit
                total_pl += current_pl
                
                trade_list.append({
                    'id': trade[0],
                    'timestamp': trade[1],
                    'type': trade[2],
                    'strike': trade[4],
                    'entry_price': trade[5],
                    'lots': trade[7],
                    'status': trade[11],
                    'current_pl': current_pl
                })
            
            conn.close()
            
            return {
                'trades': trade_list,
                'total_pl': total_pl,
                'today_count': len(trades),
                'active_positions': len([t for t in trade_list if t['status'] == 'ACTIVE']),
                'total_risk': sum([1920 for t in trade_list if t['status'] == 'ACTIVE'])  # Simulated
            }
            
        except Exception as e:
            return {'error': f'Trades error: {e}'}
    
    def get_options_data(self):
        """Get live options prices"""
        try:
            conn = sqlite3.connect('options_data.db')
            cursor = conn.cursor()
            
            # Get latest options data for key strikes
            strikes = [25300, 25400, 25500]
            options = []
            
            for strike in strikes:
                for option_type in ['CALL', 'PUT']:
                    symbol = f"NIFTY{strike}{option_type}"
                    
                    cursor.execute("""
                        SELECT ltp, volume, timestamp, bid, ask
                        FROM options_data 
                        WHERE symbol = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """, (symbol,))
                    
                    result = cursor.fetchone()
                    if result:
                        ltp, volume, timestamp, bid, ask = result
                        options.append({
                            'strike': strike,
                            'type': option_type,
                            'ltp': float(ltp),
                            'volume': volume,
                            'bid': float(bid) if bid else float(ltp) - 0.25,
                            'ask': float(ask) if ask else float(ltp) + 0.25,
                            'timestamp': timestamp
                        })
            
            conn.close()
            return {'options': options}
            
        except Exception as e:
            return {'error': f'Options error: {e}'}
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        return

def start_dashboard_server(port=8000):
    """Start the dashboard data server"""
    server = HTTPServer(('localhost', port), DashboardDataHandler)
    print(f"🌐 Dashboard data server running on http://localhost:{port}")
    print(f"📊 API endpoints available:")
    print(f"   http://localhost:{port}/api/all")
    print(f"   http://localhost:{port}/api/bot-status")
    print(f"   http://localhost:{port}/api/market-data")
    print(f"   http://localhost:{port}/api/breakouts")
    print(f"   http://localhost:{port}/api/trades")
    print(f"   http://localhost:{port}/api/options")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Dashboard server stopped")
        server.server_close()

if __name__ == "__main__":
    start_dashboard_server()