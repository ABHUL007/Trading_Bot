#!/usr/bin/env python3
"""
Test script for ICICI Breeze integration
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.brokers.icici_breeze_broker import ICICIBreezeBroker
from src.utils.logger import setup_logging


async def test_icici_broker():
    """Test ICICI Breeze broker functionality."""
    print("🧪 Testing ICICI Breeze Broker Integration")
    print("=" * 50)
    
    # Setup logging
    setup_logging(console_logging=True)
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    api_key = os.getenv('ICICI_API_KEY')
    api_secret = os.getenv('ICICI_API_SECRET')
    session_token = os.getenv('ICICI_SESSION_TOKEN')
    
    if not all([api_key, api_secret, session_token]):
        print("❌ Missing credentials. Please run setup_icici.py first.")
        return
    
    # Initialize broker
    broker = ICICIBreezeBroker(paper_trading=True)
    
    try:
        print("\n1. 🔌 Testing broker connection...")
        
        config = {
            'api_key': api_key,
            'api_secret': api_secret,
            'session_token': session_token
        }
        
        await broker.connect(config)
        print("✅ Broker connected successfully")
        
        print("\n2. 📋 Getting account information...")
        account_info = await broker.get_account_info()
        
        if account_info:
            customer_details = account_info.get('customer_details', {})
            funds = account_info.get('funds', {})
            
            print(f"✅ Account: {customer_details.get('idirect_user_name', 'Unknown')}")
            print(f"✅ User ID: {customer_details.get('idirect_userid', 'Unknown')}")
            
            if funds:
                print(f"✅ Available Balance: ₹{funds.get('unallocated_balance', 0):,}")
        
        print("\n3. 📊 Getting market data...")
        symbols = ['NIFTY', 'BANKNIFTY', 'RELIANCE']
        market_data = await broker.get_market_data(symbols)
        
        if market_data:
            print("✅ Market data retrieved:")
            for symbol, data in market_data.items():
                price = data.get('ltp', data.get('last', 'N/A'))
                print(f"   {symbol}: ₹{price}")
        
        print("\n4. 📋 Getting current positions...")
        positions = await broker.get_positions()
        print(f"✅ Found {len(positions)} positions")
        
        print("\n5. 📋 Getting today's orders...")
        orders = await broker.get_orders()
        print(f"✅ Found {len(orders)} orders")
        
        print("\n6. 🧪 Testing paper order submission...")
        test_order = {
            'symbol': 'NSE.NIFTY',
            'side': 'buy',
            'qty': 75,
            'type': 'market',
            'product_type': 'futures',
            'time_in_force': 'day'
        }
        
        order_id = await broker.submit_order(test_order)
        if order_id:
            print(f"✅ Paper order submitted: {order_id}")
        
        print("\n7. 🔌 Testing disconnection...")
        await broker.disconnect()
        print("✅ Broker disconnected successfully")
        
        print("\n🎉 All tests passed! ICICI Breeze integration is working.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if broker.is_connected:
            await broker.disconnect()


async def test_market_data_stream():
    """Test real-time market data streaming."""
    print("\n🔴 Testing Real-time Market Data Stream")
    print("=" * 50)
    
    load_dotenv()
    
    api_key = os.getenv('ICICI_API_KEY')
    api_secret = os.getenv('ICICI_API_SECRET')
    session_token = os.getenv('ICICI_SESSION_TOKEN')
    
    if not all([api_key, api_secret, session_token]):
        print("❌ Missing credentials.")
        return
    
    broker = ICICIBreezeBroker(paper_trading=True)
    
    try:
        config = {
            'api_key': api_key,
            'api_secret': api_secret,
            'session_token': session_token
        }
        
        await broker.connect(config)
        print("✅ Connected to broker")
        
        # Callback for market data
        tick_count = 0
        
        async def on_market_data(data):
            nonlocal tick_count
            tick_count += 1
            
            symbol = data.get('symbol', 'Unknown')
            price = data.get('last_price', 0)
            volume = data.get('volume', 0)
            
            print(f"📊 Tick #{tick_count} - {symbol}: ₹{price} (Vol: {volume})")
            
            # Stop after 10 ticks for demo
            if tick_count >= 10:
                print("✅ Received 10 ticks, stopping stream...")
                await broker.stop_market_data_stream()
        
        print("🔄 Starting market data stream for NIFTY...")
        symbols = ['NIFTY']
        
        await broker.start_market_data_stream(symbols, on_market_data)
        
        # Wait for some data
        await asyncio.sleep(30)  # Wait 30 seconds
        
        await broker.stop_market_data_stream()
        await broker.disconnect()
        
        print(f"✅ Stream test completed. Received {tick_count} ticks.")
        
    except Exception as e:
        print(f"❌ Stream test failed: {e}")
        if broker.is_connected:
            await broker.disconnect()


def main():
    """Run all tests."""
    print("🚀 ICICI Breeze Integration Test Suite")
    print("=" * 60)
    
    # Check if breeze_connect is available
    try:
        import breeze_connect
        print("✅ breeze_connect library is available")
    except ImportError:
        print("❌ breeze_connect library not found. Please install:")
        print("   pip install breeze-connect")
        return
    
    # Run basic tests
    asyncio.run(test_icici_broker())
    
    # Ask if user wants to test streaming
    response = input("\n🔴 Test real-time market data streaming? (y/n): ")
    if response.lower() == 'y':
        print("\n⚠️  This will test live market data streaming.")
        print("Make sure markets are open for best results.")
        input("Press Enter to continue...")
        
        asyncio.run(test_market_data_stream())
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    main()