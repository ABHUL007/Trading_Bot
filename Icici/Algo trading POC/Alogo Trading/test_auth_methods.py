"""Test different authentication approaches for ICICI Breeze"""
import os
from dotenv import load_dotenv
from breeze_connect import BreezeConnect
import json

print("=" * 70)
print("ICICI Breeze - Alternative Authentication Test")
print("=" * 70)

load_dotenv()
api_key = os.getenv('ICICI_API_KEY')
api_secret = os.getenv('ICICI_API_SECRET')
session_token = os.getenv('ICICI_SESSION_TOKEN')

print(f"\nCredentials:")
print(f"API Key: {api_key}")
print(f"API Secret: {api_secret}")
print(f"Session Token: {session_token}")

try:
    print("\n" + "=" * 70)
    print("Method 1: Standard generate_session")
    print("=" * 70)
    
    breeze = BreezeConnect(api_key=api_key)
    
    # Try with session_token directly
    print("\nCalling generate_session...")
    response = breeze.generate_session(
        api_secret=api_secret,
        session_token=session_token
    )
    
    print(f"Response: {response}")
    print(f"Response type: {type(response)}")
    
    # Check if breeze object has session info
    print(f"\nBreeze object attributes:")
    print(f"Has 'session_token': {hasattr(breeze, 'session_token')}")
    print(f"Has 'user_id': {hasattr(breeze, 'user_id')}")
    
    # Try to make an API call regardless
    print("\n" + "=" * 70)
    print("Method 2: Direct API call with session_token")
    print("=" * 70)
    
    try:
        # Try get_customer_details with api_session parameter
        print("\nTrying get_customer_details with api_session...")
        customer = breeze.get_customer_details(api_session=session_token)
        print(f"Customer details response: {customer}")
        
        if customer:
            print("\n✓ SUCCESS! API call worked")
            print(json.dumps(customer, indent=2))
    except Exception as api_error:
        print(f"API call error: {api_error}")
        
        # Try without api_session parameter
        print("\nTrying get_customer_details without api_session...")
        try:
            customer2 = breeze.get_customer_details()
            print(f"Response: {customer2}")
        except Exception as e2:
            print(f"Also failed: {e2}")
    
    print("\n" + "=" * 70)
    print("Method 3: Check funds")
    print("=" * 70)
    
    try:
        funds = breeze.get_funds()
        print(f"Funds: {funds}")
    except Exception as funds_error:
        print(f"Funds error: {funds_error}")
        
except Exception as e:
    print(f"\nMain error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Testing Complete")
print("=" * 70)
