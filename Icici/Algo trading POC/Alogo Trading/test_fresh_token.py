"""
Direct test with fresh session token 53449710
"""

from breeze_connect import BreezeConnect

def test_fresh_token():
    """Test with the exact fresh token"""
    
    api_key = "54~wvhNj60932151ga945769)60X7f38"
    api_secret = "4=911n152202N4kQ42%Bu09)f0Q4R92D"
    session_token = "53449710"  # Fresh token
    
    print(f"🔑 Testing with fresh token: {session_token}")
    
    try:
        breeze = BreezeConnect(api_key=api_key)
        response = breeze.generate_session(
            api_secret=api_secret,
            session_token=session_token
        )
        
        print(f"📡 Response: {response}")
        
        if response and response.get('Status') == 200:
            print("🎉 SUCCESS! ICICI Connected!")
            
            # Test customer details
            customer = breeze.get_customer_details()
            print(f"👤 Customer: {customer}")
            
            # Test NIFTY quote
            quote = breeze.get_quotes(
                stock_code="NIFTY",
                exchange_code="NSE",
                product_type="cash"
            )
            print(f"📊 NIFTY Quote: {quote}")
            
            if quote and quote.get('Status') == 200:
                quote_data = quote.get('Success', [])
                if quote_data:
                    ltp = quote_data[0].get('ltp', 0)
                    print(f"💰 LIVE NIFTY: ₹{ltp:,.2f}")
                    return True, ltp
            
            return True, None
        else:
            print(f"❌ Failed: {response}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False, None

if __name__ == "__main__":
    print("🔴 Testing Fresh Session Token 53449710")
    success, price = test_fresh_token()
    
    if success:
        print("✅ READY FOR LIVE WEBSOCKET!")
        if price:
            print(f"📊 Current NIFTY: ₹{price:,.2f}")
    else:
        print("❌ Still not working - may need even fresher token")