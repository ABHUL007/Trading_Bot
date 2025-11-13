"""
Detailed ICICI Breeze Connection Debugging
Test different approaches to connect to ICICI Breeze API
"""

import os
import traceback
from dotenv import load_dotenv

# Import ICICI Breeze
try:
    from breeze_connect import BreezeConnect
    print("✅ breeze_connect imported successfully")
except ImportError:
    print("❌ breeze_connect not available")
    exit(1)

# Load environment variables
load_dotenv()

def debug_icici_connection():
    """Debug ICICI Breeze connection with detailed error handling"""
    
    print("🔍 DETAILED ICICI Breeze Connection Debug...")
    print("=" * 60)
    
    # Get credentials
    api_key = os.getenv('ICICI_API_KEY')
    api_secret = os.getenv('ICICI_API_SECRET')
    session_token = os.getenv('ICICI_SESSION_TOKEN')
    
    print(f"📋 API Key: {api_key}")
    print(f"🔐 API Secret: {api_secret}")
    print(f"🎟️ Session Token: {session_token}")
    print()
    
    try:
        print("🔌 Step 1: Creating BreezeConnect instance...")
        breeze = BreezeConnect(api_key=api_key)
        print(f"✅ BreezeConnect created: {type(breeze)}")
        
        print("🔑 Step 2: Attempting session generation...")
        print(f"Using API Secret: {api_secret[:10]}...")
        print(f"Using Session Token: {session_token}")
        
        try:
            session_response = breeze.generate_session(
                api_secret=api_secret,
                session_token=session_token
            )
            
            print(f"📡 Raw Session Response: {session_response}")
            print(f"📡 Response Type: {type(session_response)}")
            
            if session_response:
                print(f"📋 Response Keys: {session_response.keys() if isinstance(session_response, dict) else 'Not a dict'}")
                
                if isinstance(session_response, dict):
                    status = session_response.get('Status')
                    success = session_response.get('Success')
                    error = session_response.get('Error')
                    
                    print(f"📊 Status: {status}")
                    print(f"✅ Success: {success}")
                    print(f"❌ Error: {error}")
                    
                    if status == 200:
                        print("✅ Session generated successfully!")
                        
                        # Test customer details
                        try:
                            print("👤 Testing customer details...")
                            customer_response = breeze.get_customer_details()
                            print(f"👤 Customer Response: {customer_response}")
                            
                            if customer_response and customer_response.get('Status') == 200:
                                success_data = customer_response.get('Success', {})
                                print(f"👤 User: {success_data.get('idirect_user_name', 'Unknown')}")
                                print(f"🆔 Client: {success_data.get('client_code', 'Unknown')}")
                                return True
                            else:
                                print(f"❌ Customer details failed: {customer_response}")
                                
                        except Exception as e:
                            print(f"❌ Customer details error: {e}")
                            traceback.print_exc()
                    else:
                        print(f"❌ Session failed with status: {status}")
                        if error:
                            print(f"❌ Error message: {error}")
                else:
                    print(f"❌ Unexpected response format: {session_response}")
            else:
                print("❌ Session response is None or empty")
                print("💡 This usually means:")
                print("   - Session token has expired")
                print("   - API credentials are incorrect")
                print("   - Network connectivity issues")
                print("   - ICICI server is down")
                
        except Exception as session_error:
            print(f"❌ Session generation exception: {session_error}")
            print(f"❌ Exception type: {type(session_error)}")
            traceback.print_exc()
            
            # Check specific error types
            error_str = str(session_error).lower()
            if 'timeout' in error_str:
                print("\n💡 TIMEOUT ERROR:")
                print("- Check internet connection")
                print("- ICICI servers might be slow")
                print("- Try again in a few minutes")
            elif 'ssl' in error_str or 'certificate' in error_str:
                print("\n💡 SSL/CERTIFICATE ERROR:")
                print("- Update certificates: pip install --upgrade certifi")
                print("- Check system time")
            elif 'auth' in error_str or 'invalid' in error_str:
                print("\n💡 AUTHENTICATION ERROR:")
                print("- Verify API key and secret")
                print("- Generate new session token")
                print("- Check account permissions")
            
    except Exception as e:
        print(f"❌ General connection error: {e}")
        print(f"❌ Exception type: {type(e)}")
        traceback.print_exc()
        
    return False

def test_alternative_approach():
    """Test alternative connection approaches"""
    
    print("\n🔧 Testing Alternative Approaches...")
    print("=" * 50)
    
    api_key = os.getenv('ICICI_API_KEY')
    api_secret = os.getenv('ICICI_API_SECRET')
    session_token = os.getenv('ICICI_SESSION_TOKEN')
    
    try:
        # Try with explicit parameters
        print("🔄 Approach 1: Direct parameter passing...")
        breeze = BreezeConnect(api_key=api_key)
        
        result = breeze.generate_session(
            api_secret=api_secret,
            session_token=session_token
        )
        
        print(f"🔄 Result 1: {result}")
        
    except Exception as e:
        print(f"❌ Approach 1 failed: {e}")
    
    try:
        # Try different initialization
        print("🔄 Approach 2: Alternative initialization...")
        breeze2 = BreezeConnect(api_key=api_key)
        
        # Set attributes directly (if supported)
        print(f"🔄 Breeze object methods: {[m for m in dir(breeze2) if not m.startswith('_')]}")
        
    except Exception as e:
        print(f"❌ Approach 2 failed: {e}")

if __name__ == "__main__":
    print("🔴 DETAILED ICICI Breeze Connection Debug")
    print("Comprehensive testing of API connection...\n")
    
    success = debug_icici_connection()
    
    if not success:
        test_alternative_approach()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ CONNECTION SUCCESSFUL!")
        print("🚀 Ready for live trading")
    else:
        print("❌ CONNECTION STILL FAILED!")
        print("\n🔧 TROUBLESHOOTING STEPS:")
        print("1. 🔄 Generate a fresh session token from ICICI Direct")
        print("2. 🕐 Ensure session token is less than 24 hours old")
        print("3. 🌐 Check internet connectivity")
        print("4. 📞 Contact ICICI Direct API support")
        print("5. 🔍 Verify account has API access enabled")
        print("\n📧 ICICI Direct Support:")
        print("   - Email: support@icicidirect.com")
        print("   - Phone: 1800-1200-111")