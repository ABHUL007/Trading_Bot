"""Quick ICICI Breeze connection test"""
import asyncio
import os
from dotenv import load_dotenv
from src.brokers.icici_breeze_broker import ICICIBreezeBroker

async def test_connection():
    print("=" * 60)
    print("ICICI Breeze Connection Test")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    api_key = os.getenv('ICICI_API_KEY')
    api_secret = os.getenv('ICICI_API_SECRET')
    session_token = os.getenv('ICICI_SESSION_TOKEN')
    paper_trading = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
    
    print(f"\n✓ Environment variables loaded")
    print(f"✓ API Key: {api_key[:10]}..." if api_key else "✗ API Key not found")
    print(f"✓ API Secret: {api_secret[:10]}..." if api_secret else "✗ API Secret not found")
    print(f"✓ Session Token: {session_token[:10]}..." if session_token else "✗ Session Token not found")
    print(f"✓ Paper Trading: {paper_trading}")
    
    if not all([api_key, api_secret, session_token]):
        print("\n✗ ERROR: Missing credentials in .env file")
        return
    
    print("\n" + "-" * 60)
    print("Connecting to ICICI Breeze...")
    print("-" * 60)
    
    try:
        # Create broker instance
        broker = ICICIBreezeBroker(paper_trading=paper_trading)
        
        # Connect
        config = {
            'api_key': api_key,
            'api_secret': api_secret,
            'session_token': session_token
        }
        
        await broker.connect(config)
        print("✓ Successfully connected to ICICI Breeze!")
        
        # Test account info
        print("\n" + "-" * 60)
        print("Fetching Account Information...")
        print("-" * 60)
        
        account_info = await broker.get_account_info()
        
        if account_info:
            print("\n✓ Account Information Retrieved:")
            print(f"  Account ID: {account_info.get('account_id', 'N/A')}")
            print(f"  Balance: ₹{account_info.get('balance', 0):,.2f}")
            print(f"  Available Margin: ₹{account_info.get('available_margin', 0):,.2f}")
            print(f"  Used Margin: ₹{account_info.get('used_margin', 0):,.2f}")
        
        # Test positions
        print("\n" + "-" * 60)
        print("Fetching Positions...")
        print("-" * 60)
        
        positions = await broker.get_positions()
        print(f"✓ Found {len(positions)} open positions")
        
        if positions:
            for pos in positions[:3]:  # Show first 3
                print(f"  - {pos.get('symbol')}: {pos.get('quantity')} @ ₹{pos.get('average_price')}")
        
        # Disconnect
        await broker.disconnect()
        print("\n✓ Disconnected successfully")
        
        print("\n" + "=" * 60)
        print("✓ CONNECTION TEST PASSED!")
        print("=" * 60)
        print("\nYour ICICI Breeze integration is working correctly.")
        print("You can now run:")
        print("  python main.py live-trade -s icici_nifty_strategy --paper")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check if your session token is still valid")
        print("2. Verify API key and secret are correct")
        print("3. Ensure you have an active ICICI Direct account")
        print("4. Check if markets are open (for live data)")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_connection())
