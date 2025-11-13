"""
Quick ICICI Breeze Connection Status Check
Test with fresh session token
"""

import os
from dotenv import load_dotenv

# Import ICICI Breeze
try:
    from breeze_connect import BreezeConnect
    print("✅ breeze_connect available")
except ImportError:
    print("❌ breeze_connect not available")
    exit(1)

def quick_connection_test():
    """Quick test with current credentials"""
    
    # Load current .env
    load_dotenv()
    
    api_key = os.getenv('ICICI_API_KEY')
    api_secret = os.getenv('ICICI_API_SECRET') 
    session_token = os.getenv('ICICI_SESSION_TOKEN')
    
    print(f"🔑 Current Session Token: {session_token}")
    print("🔄 Testing connection...")
    
    try:
        breeze = BreezeConnect(api_key=api_key)
        response = breeze.generate_session(
            api_secret=api_secret,
            session_token=session_token
        )
        
        if response and response.get('Status') == 200:
            print("✅ CONNECTION SUCCESS!")
            return True
        else:
            print(f"❌ Connection failed: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔴 Quick ICICI Breeze Connection Test")
    print("=" * 40)
    
    if quick_connection_test():
        print("🚀 Ready to start live WebSocket!")
    else:
        print("⚠️ Need fresh session token")
        print("📝 Please provide your new session token")