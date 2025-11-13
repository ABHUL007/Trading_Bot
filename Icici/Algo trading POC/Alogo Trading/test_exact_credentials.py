"""
Clean ICICI Breeze Test with Exact Credentials
Test with the exact credentials provided by user
"""

import os
from dotenv import load_dotenv

# Import ICICI Breeze
try:
    from breeze_connect import BreezeConnect
    print("✅ breeze_connect imported successfully")
except ImportError:
    print("❌ breeze_connect not available")
    exit(1)

def test_exact_credentials():
    """Test with exact credentials provided by user"""
    
    print("🔍 Testing with EXACT credentials...")
    print("=" * 50)
    
    # Use exact credentials as provided
    api_key = "54~wvhNj60932151ga945769)60X7f38"
    api_secret = "4=911n152202N4kQ42%Bu09)f0Q4R92D"
    session_token = "53449572"
    
    print(f"📋 API Key: {api_key}")
    print(f"🔐 API Secret: {api_secret}")
    print(f"🎟️ Session Token: {session_token}")
    print()
    
    try:
        print("🔌 Step 1: Creating BreezeConnect...")
        breeze = BreezeConnect(api_key=api_key)
        print("✅ BreezeConnect created successfully")
        
        print("🔑 Step 2: Generating session...")
        session_response = breeze.generate_session(
            api_secret=api_secret,
            session_token=session_token
        )
        
        print(f"📡 Session Response: {session_response}")
        
        if session_response:
            print(f"📊 Response Type: {type(session_response)}")
            if isinstance(session_response, dict):
                status = session_response.get('Status')
                success = session_response.get('Success')
                error = session_response.get('Error')
                
                print(f"📊 Status: {status}")
                print(f"✅ Success: {success}")
                print(f"❌ Error: {error}")
                
                if status == 200:
                    print("🎉 SUCCESS! Session generated!")
                    
                    # Test customer details
                    print("👤 Getting customer details...")
                    customer = breeze.get_customer_details()
                    print(f"👤 Customer: {customer}")
                    
                    if customer and customer.get('Status') == 200:
                        user_data = customer.get('Success', {})
                        print(f"👤 User: {user_data.get('idirect_user_name', 'Unknown')}")
                        print(f"🆔 Client: {user_data.get('client_code', 'Unknown')}")
                        
                        # Test NIFTY quote
                        print("📊 Getting NIFTY quote...")
                        quote = breeze.get_quotes(
                            stock_code="NIFTY",
                            exchange_code="NSE",
                            product_type="cash"
                        )
                        print(f"📈 NIFTY Quote: {quote}")
                        
                        if quote and quote.get('Status') == 200:
                            quote_data = quote.get('Success', [])
                            if quote_data:
                                ltp = quote_data[0].get('ltp', 0)
                                print(f"💰 Current NIFTY: ₹{ltp:,.2f}")
                                return True, ltp
                        
                        return True, None
                else:
                    print(f"❌ Session failed - Status: {status}")
                    if error:
                        print(f"❌ Error: {error}")
                        
                        # Provide specific error solutions
                        error_lower = str(error).lower()
                        if 'session' in error_lower and 'empty' in error_lower:
                            print("\n💡 SOLUTION: Session token issue")
                            print("- Generate new session token from ICICI Direct")
                            print("- Ensure token is fresh (less than 24 hours)")
                        elif 'invalid' in error_lower or 'unauthorized' in error_lower:
                            print("\n💡 SOLUTION: Authentication issue")
                            print("- Check API key and secret")
                            print("- Verify account has API access")
                        elif 'expired' in error_lower:
                            print("\n💡 SOLUTION: Token expired")
                            print("- Generate fresh session token")
            else:
                print(f"❌ Unexpected response: {session_response}")
        else:
            print("❌ No response from server")
            print("💡 Possible causes:")
            print("- Network connectivity issues")
            print("- ICICI servers down")
            print("- Invalid credentials")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        print(f"📋 Exception type: {type(e)}")
        
        # Provide specific solutions based on error
        error_str = str(e).lower()
        if 'timeout' in error_str:
            print("\n💡 TIMEOUT SOLUTION:")
            print("- Check internet connection")
            print("- Try again in a few minutes")
        elif 'ssl' in error_str:
            print("\n💡 SSL SOLUTION:")
            print("- Update certificates: pip install --upgrade certifi")
        elif 'connection' in error_str:
            print("\n💡 CONNECTION SOLUTION:")
            print("- Check firewall settings")
            print("- Verify internet connectivity")
    
    return False, None

if __name__ == "__main__":
    print("🔴 ICICI Breeze Exact Credentials Test")
    print("Testing with user-provided exact credentials...\n")
    
    success, nifty_price = test_exact_credentials()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ CONNECTION SUCCESSFUL!")
        if nifty_price:
            print(f"📊 Live NIFTY Price: ₹{nifty_price:,.2f}")
        print("🚀 Ready to start live WebSocket feed!")
    else:
        print("❌ CONNECTION FAILED!")
        print("\n🔧 Next Steps:")
        print("1. 🔄 Get fresh session token from ICICI Direct")
        print("2. 🌐 Check internet connection")
        print("3. 📞 Contact ICICI support if issues persist")
        print("\n📝 How to get fresh session token:")
        print("   - Login to ICICI Direct website")
        print("   - Go to API section/Apps")
        print("   - Generate new session token")
        print("   - Token should be 8-10 digit number")