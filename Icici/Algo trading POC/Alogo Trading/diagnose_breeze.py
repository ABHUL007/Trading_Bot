"""Diagnostic test for ICICI Breeze API"""
import os
from dotenv import load_dotenv
from breeze_connect import BreezeConnect

print("=" * 70)
print("ICICI Breeze API Diagnostic Test")
print("=" * 70)

# Load credentials
load_dotenv()
api_key = os.getenv('ICICI_API_KEY')
api_secret = os.getenv('ICICI_API_SECRET')
session_token = os.getenv('ICICI_SESSION_TOKEN')

print(f"\n1. Credentials Check:")
print(f"   API Key: {api_key[:15]}... (length: {len(api_key)})" if api_key else "   ✗ Not found")
print(f"   API Secret: {api_secret[:15]}... (length: {len(api_secret)})" if api_secret else "   ✗ Not found")
print(f"   Session Token: {session_token[:15]}... (length: {len(session_token)})" if session_token else "   ✗ Not found")

if not all([api_key, api_secret, session_token]):
    print("\n✗ ERROR: Missing credentials")
    exit(1)

print("\n2. Testing Breeze Connection:")
print("-" * 70)

try:
    # Initialize Breeze
    print("   Creating BreezeConnect instance...")
    breeze = BreezeConnect(api_key=api_key)
    print("   ✓ BreezeConnect initialized")
    
    # Try to generate session
    print("\n   Attempting to generate session...")
    print(f"   Using:")
    print(f"   - API Secret: {api_secret[:10]}...")
    print(f"   - Session Token: {session_token[:10]}...")
    
    response = breeze.generate_session(
        api_secret=api_secret,
        session_token=session_token
    )
    
    print(f"\n   Raw Response:")
    print(f"   Type: {type(response)}")
    print(f"   Value: {response}")
    
    if response is None:
        print("\n   ✗ Response is None!")
        print("\n   Possible Issues:")
        print("   1. Session token may be expired (tokens usually expire after 24 hours)")
        print("   2. API credentials may be incorrect")
        print("   3. Network connectivity issues")
        print("   4. ICICI API server issues")
        print("\n   To get a new session token:")
        print(f"   Visit: https://api.icicidirect.com/apiuser/login?api_key={api_key}")
        print("   After login, copy the session token from the redirect URL")
    else:
        print(f"\n   ✓ Session generated successfully!")
        
        # Try to get customer details
        print("\n3. Testing API Call - Customer Details:")
        print("-" * 70)
        
        try:
            customer = breeze.get_customer_details(api_session=session_token)
            print(f"   Response Type: {type(customer)}")
            print(f"   Response: {customer}")
            
            if customer and isinstance(customer, dict):
                if customer.get('Status') == 200:
                    print(f"\n   ✓ Customer Details Retrieved:")
                    success_data = customer.get('Success', {})
                    print(f"   - User: {success_data.get('idirect_user_name', 'N/A')}")
                    print(f"   - Email: {success_data.get('email_address', 'N/A')}")
                else:
                    print(f"\n   ✗ API Error: {customer}")
        except Exception as cust_error:
            print(f"\n   ✗ Customer details error: {cust_error}")
        
        print("\n" + "=" * 70)
        print("✓ DIAGNOSTIC COMPLETE")
        print("=" * 70)
        
except Exception as e:
    print(f"\n   ✗ ERROR: {e}")
    print(f"\n   Error Type: {type(e).__name__}")
    import traceback
    print("\n   Full Traceback:")
    print(traceback.format_exc())
    
    print("\n" + "=" * 70)
    print("TROUBLESHOOTING STEPS:")
    print("=" * 70)
    print("\n1. Generate a fresh session token:")
    print(f"   https://api.icicidirect.com/apiuser/login?api_key={api_key}")
    print("\n2. After login, the URL will redirect with session_token parameter")
    print("   Example: https://redirect_url?session_token=XXXXX")
    print("\n3. Copy the session_token value and update your .env file")
    print("\n4. Session tokens typically expire after 24 hours")
    print("=" * 70)
