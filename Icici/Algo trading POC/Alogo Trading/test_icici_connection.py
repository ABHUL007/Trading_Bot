"""
ICICI Breeze Connection Test
Test your API credentials and get a fresh session
"""

import os
from dotenv import load_dotenv

# Import ICICI Breeze
try:
    from breeze_connect import BreezeConnect
    print("✅ breeze_connect imported successfully")
except ImportError:
    print("❌ breeze_connect not available - install with: pip install breeze-connect")
    exit(1)

# Load environment variables
load_dotenv()

def test_icici_connection():
    """Test ICICI Breeze connection step by step"""
    
    print("🔍 Testing ICICI Breeze Connection...")
    print("=" * 50)
    
    # Get credentials
    api_key = os.getenv('ICICI_API_KEY')
    api_secret = os.getenv('ICICI_API_SECRET')
    session_token = os.getenv('ICICI_SESSION_TOKEN')
    
    print(f"📋 API Key: {api_key[:10] if api_key else 'NOT FOUND'}...")
    print(f"🔐 API Secret: {api_secret[:10] if api_secret else 'NOT FOUND'}...")
    print(f"🎟️ Session Token: {session_token if session_token else 'NOT FOUND'}")
    print()
    
    if not all([api_key, api_secret, session_token]):
        print("❌ Missing credentials in .env file")
        print("Required: ICICI_API_KEY, ICICI_API_SECRET, ICICI_SESSION_TOKEN")
        return False
    
    try:
        print("🔌 Step 1: Initializing BreezeConnect...")
        breeze = BreezeConnect(api_key=api_key)
        print("✅ BreezeConnect initialized")
        
        print("🔑 Step 2: Generating session...")
        session_response = breeze.generate_session(
            api_secret=api_secret,
            session_token=session_token
        )
        
        print(f"📡 Session Response: {session_response}")
        
        if session_response and session_response.get('Status') == 200:
            print("✅ Session generated successfully!")
            
            print("👤 Step 3: Getting customer details...")
            customer_details = breeze.get_customer_details()
            print(f"📋 Customer Details: {customer_details}")
            
            if customer_details and customer_details.get('Status') == 200:
                success_data = customer_details.get('Success', {})
                user_name = success_data.get('idirect_user_name', 'Unknown')
                client_code = success_data.get('client_code', 'Unknown')
                print(f"✅ Connected successfully!")
                print(f"👤 User: {user_name}")
                print(f"🆔 Client Code: {client_code}")
                
                print("📊 Step 4: Testing NIFTY quote...")
                try:
                    quote_response = breeze.get_quotes(
                        stock_code="NIFTY",
                        exchange_code="NSE",
                        product_type="cash"
                    )
                    print(f"📈 NIFTY Quote Response: {quote_response}")
                    
                    if quote_response and quote_response.get('Status') == 200:
                        success_data = quote_response.get('Success', [])
                        if success_data:
                            ltp = success_data[0].get('ltp', 0)
                            print(f"📊 Current NIFTY Price: ₹{ltp:,.2f}")
                            return True
                    else:
                        print("⚠️ Could not get NIFTY quote, but connection is working")
                        return True
                        
                except Exception as e:
                    print(f"⚠️ Quote error (but connection works): {e}")
                    return True
                    
            else:
                print(f"❌ Customer details failed: {customer_details}")
                return False
        else:
            print(f"❌ Session generation failed: {session_response}")
            
            # Check if it's a session token issue
            if session_response and 'session' in str(session_response).lower():
                print("\n💡 SOLUTION: You need a fresh session token!")
                print("🔗 Steps to get new session token:")
                print("1. Login to ICICI Direct website")
                print("2. Go to API section")
                print("3. Generate new session token")
                print("4. Update ICICI_SESSION_TOKEN in .env file")
            
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        
        # Provide helpful error solutions
        error_str = str(e).lower()
        if 'ssl' in error_str or 'certificate' in error_str:
            print("\n💡 SSL Error Solution:")
            print("Try: pip install --upgrade certifi")
        elif 'timeout' in error_str or 'network' in error_str:
            print("\n💡 Network Error Solution:")
            print("Check your internet connection and try again")
        elif 'api' in error_str or 'auth' in error_str:
            print("\n💡 API Error Solution:")
            print("Check your API credentials and session token")
        
        return False

if __name__ == "__main__":
    print("🔴 ICICI Breeze Connection Test")
    print("Testing connection with your credentials...\n")
    
    success = test_icici_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ CONNECTION SUCCESSFUL!")
        print("🚀 Ready to start live WebSocket feed")
    else:
        print("❌ CONNECTION FAILED!")
        print("🔧 Please fix the issues above and try again")
        print("\n📞 If issues persist:")
        print("- Contact ICICI Direct support")
        print("- Check API subscription status")
        print("- Verify account permissions")