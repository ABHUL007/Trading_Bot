#!/usr/bin/env python3
"""
Unified Trading System Launcher
- Starts websocket data collector (populates NIFTY databases)
- Starts real trader bot (executes trades based on Super Pranni signals)
- Both run simultaneously with proper monitoring
"""

import asyncio
import subprocess
import sys
import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import signal

# Setup logging
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.stream.reconfigure(encoding='utf-8')
logger.addHandler(console_handler)

file_handler = RotatingFileHandler('trading_system.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

logger.propagate = False


class TradingSystemLauncher:
    """Manages both websocket collector and trading bot"""
    
    def __init__(self):
        self.data_collector_process = None
        self.trader_process = None
        self.running = True
        
        # Get Python executable path
        self.python_exe = sys.executable
        
        logger.info("=" * 80)
        logger.info("🚀 UNIFIED TRADING SYSTEM LAUNCHER")
        logger.info("=" * 80)
        logger.info(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🐍 Python: {self.python_exe}")
        logger.info("=" * 80)
    
    def start_data_collector(self):
        """Start the websocket data collector process"""
        try:
            logger.info("\n" + "=" * 80)
            logger.info("📊 STARTING WEBSOCKET DATA COLLECTOR")
            logger.info("=" * 80)
            
            # Start data collector as subprocess
            self.data_collector_process = subprocess.Popen(
                [self.python_exe, 'websocket_data_collector.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace'
            )
            
            logger.info(f"✅ Data Collector started (PID: {self.data_collector_process.pid})")
            logger.info("   - Populates: NIFTY_5min_data.db")
            logger.info("   - Populates: NIFTY_15min_data.db")
            logger.info("   - Check logs: websocket_data_collector.log")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start data collector: {e}")
            return False
    
    def start_trader(self):
        """Start the real trader bot process"""
        try:
            logger.info("\n" + "=" * 80)
            logger.info("🤖 STARTING REAL TRADER BOT")
            logger.info("=" * 80)
            
            # Start trader as subprocess
            self.trader_process = subprocess.Popen(
                [self.python_exe, 'real_trader.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace'
            )
            
            logger.info(f"✅ Real Trader started (PID: {self.trader_process.pid})")
            logger.info("   - Reads Super Pranni signals from databases")
            logger.info("   - Executes trades via Breeze API")
            logger.info("   - Monitors positions with ₹10 target & level-based SL")
            logger.info("   - Check logs: real_trader.log")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start trader: {e}")
            return False
    
    def monitor_processes(self):
        """Monitor both processes and restart if needed"""
        logger.info("\n" + "=" * 80)
        logger.info("👁️  MONITORING BOTH PROCESSES")
        logger.info("=" * 80)
        logger.info("Press Ctrl+C to stop both processes gracefully")
        logger.info("=" * 80)
        
        try:
            while self.running:
                # Check data collector
                if self.data_collector_process:
                    dc_status = self.data_collector_process.poll()
                    if dc_status is not None:
                        logger.error(f"⚠️ Data Collector stopped unexpectedly (exit code: {dc_status})")
                        logger.info("🔄 Restarting Data Collector...")
                        self.start_data_collector()
                
                # Check trader
                if self.trader_process:
                    trader_status = self.trader_process.poll()
                    if trader_status is not None:
                        logger.error(f"⚠️ Real Trader stopped unexpectedly (exit code: {trader_status})")
                        logger.info("🔄 Restarting Real Trader...")
                        self.start_trader()
                
                # Sleep for 5 seconds before next check
                import time
                time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Keyboard interrupt received - shutting down gracefully...")
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown both processes"""
        logger.info("\n" + "=" * 80)
        logger.info("🛑 SHUTTING DOWN TRADING SYSTEM")
        logger.info("=" * 80)
        
        self.running = False
        
        # Stop trader first
        if self.trader_process and self.trader_process.poll() is None:
            logger.info("⏹️  Stopping Real Trader...")
            try:
                self.trader_process.terminate()
                self.trader_process.wait(timeout=10)
                logger.info("✅ Real Trader stopped")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Real Trader didn't stop gracefully, forcing...")
                self.trader_process.kill()
                logger.info("✅ Real Trader killed")
        
        # Stop data collector
        if self.data_collector_process and self.data_collector_process.poll() is None:
            logger.info("⏹️  Stopping Data Collector...")
            try:
                self.data_collector_process.terminate()
                self.data_collector_process.wait(timeout=10)
                logger.info("✅ Data Collector stopped")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Data Collector didn't stop gracefully, forcing...")
                self.data_collector_process.kill()
                logger.info("✅ Data Collector killed")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ TRADING SYSTEM SHUTDOWN COMPLETE")
        logger.info("=" * 80)
        logger.info(f"📅 Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
    
    def run(self):
        """Main run method"""
        try:
            # Start data collector first (trader needs the databases)
            if not self.start_data_collector():
                logger.error("❌ Cannot start without data collector!")
                return
            
            # Wait 5 seconds for data collector to initialize
            logger.info("\n⏳ Waiting 5 seconds for data collector to initialize...")
            import time
            time.sleep(5)
            
            # Start trader
            if not self.start_trader():
                logger.error("❌ Cannot start trader!")
                self.shutdown()
                return
            
            # Wait 3 seconds for trader to initialize
            logger.info("\n⏳ Waiting 3 seconds for trader to initialize...")
            time.sleep(3)
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ BOTH SYSTEMS RUNNING!")
            logger.info("=" * 80)
            logger.info("📊 Data Collector: Updating NIFTY databases")
            logger.info("🤖 Real Trader: Monitoring for Super Pranni signals")
            logger.info("=" * 80)
            
            # Monitor both processes
            self.monitor_processes()
            
        except Exception as e:
            logger.error(f"❌ Critical error: {e}")
            self.shutdown()
        
        finally:
            self.shutdown()


def main():
    """Entry point"""
    # Setup signal handlers for graceful shutdown
    launcher = TradingSystemLauncher()
    
    def signal_handler(sig, frame):
        logger.info("\n\n🛑 Shutdown signal received...")
        launcher.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the system
    launcher.run()


if __name__ == "__main__":
    main()
