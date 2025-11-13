#!/usr/bin/env python3
"""
ICICI Breeze Setup and Configuration Script
"""

import os
import sys
import webbrowser
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import Config
from src.utils.logger import setup_logging


def print_banner():
    """Print setup banner."""
    print("=" * 60)
    print("🚀 ICICI Direct Breeze Trading Platform Setup")
    print("=" * 60)
    print()


def check_requirements():
    """Check if required packages are installed."""
    required_packages = [
        'breeze_connect',
        'pandas',
        'numpy',
        'python_dotenv',
        'pyyaml'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nPlease install them using:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True


def setup_api_credentials():
    """Help user set up API credentials."""
    print("\n📋 ICICI Direct API Credentials Setup")
    print("-" * 40)
    
    # Check if .env file exists
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print("Creating .env file from template...")
        example_env = project_root / "config" / "example.env"
        if example_env.exists():
            env_file.write_text(example_env.read_text())
            print(f"✅ Created .env file at: {env_file}")
        else:
            print("❌ Example .env file not found!")
            return False
    
    # Load existing environment
    load_dotenv(env_file)
    
    api_key = os.getenv('ICICI_API_KEY', '')
    api_secret = os.getenv('ICICI_API_SECRET', '')
    
    print("\n📝 API Credentials Configuration:")
    print("1. Register at ICICI Direct API Portal")
    print("2. Create an app and get API Key & Secret")
    print("3. Generate session token for trading")
    
    # Get API Key
    if not api_key or api_key == 'your_api_key_here':
        print("\n🔑 API Key Setup:")
        api_key = input("Enter your ICICI API Key: ").strip()
        
        if api_key:
            update_env_file(env_file, 'ICICI_API_KEY', api_key)
    else:
        print(f"✅ API Key found: {api_key[:8]}...")
    
    # Get API Secret
    if not api_secret or api_secret == 'your_secret_key_here':
        print("\n🔐 API Secret Setup:")
        api_secret = input("Enter your ICICI API Secret: ").strip()
        
        if api_secret:
            update_env_file(env_file, 'ICICI_API_SECRET', api_secret)
    else:
        print(f"✅ API Secret configured")
    
    # Generate session URL
    if api_key and api_key != 'your_api_key_here':
        print("\n🌐 Session Token Generation:")
        encoded_api_key = urllib.parse.quote_plus(api_key)
        login_url = f"https://api.icicidirect.com/apiuser/login?api_key={encoded_api_key}"
        
        print(f"Open this URL to get your session token:")
        print(f"🔗 {login_url}")
        
        if input("\nOpen URL in browser? (y/n): ").lower() == 'y':
            webbrowser.open(login_url)
        
        print("\nAfter login, copy the session token from the URL and enter below:")
        session_token = input("Enter session token: ").strip()
        
        if session_token:
            update_env_file(env_file, 'ICICI_SESSION_TOKEN', session_token)
            print("✅ Session token saved")
    
    return True


def update_env_file(env_file: Path, key: str, value: str):
    """Update environment file with new key-value pair."""
    lines = []
    key_found = False
    
    if env_file.exists():
        lines = env_file.read_text().splitlines()
    
    # Update existing key or add new one
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            key_found = True
            break
    
    if not key_found:
        lines.append(f"{key}={value}")
    
    env_file.write_text('\n'.join(lines) + '\n')


def test_connection():
    """Test connection to ICICI Breeze API."""
    print("\n🧪 Testing API Connection")
    print("-" * 30)
    
    try:
        from breeze_connect import BreezeConnect
        
        # Load environment
        load_dotenv()
        
        api_key = os.getenv('ICICI_API_KEY')
        api_secret = os.getenv('ICICI_API_SECRET')
        session_token = os.getenv('ICICI_SESSION_TOKEN')
        
        if not all([api_key, api_secret, session_token]):
            print("❌ Missing credentials. Please complete setup first.")
            return False
        
        # Test connection
        breeze = BreezeConnect(api_key=api_key)
        
        print("🔄 Generating session...")
        response = breeze.generate_session(
            api_secret=api_secret,
            session_token=session_token
        )
        
        if response.get('Status') == 200:
            print("✅ Session generated successfully")
            
            # Test getting customer details
            print("🔄 Getting customer details...")
            customer_details = breeze.get_customer_details(api_session=session_token)
            
            if customer_details.get('Status') == 200:
                user_name = customer_details['Success'].get('idirect_user_name', 'Unknown')
                print(f"✅ Connection successful! Welcome {user_name}")
                return True
            else:
                print(f"❌ Failed to get customer details: {customer_details}")
                return False
        else:
            print(f"❌ Session generation failed: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def setup_directories():
    """Create necessary directories."""
    print("\n📁 Setting up directories...")
    
    directories = [
        "logs",
        "data",
        "reports",
        "config"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)
        print(f"✅ Created: {directory}/")


def display_next_steps():
    """Display next steps for the user."""
    print("\n🎉 Setup Complete!")
    print("=" * 50)
    print("\n📋 Next Steps:")
    print("1. Review configuration in config/icici_breeze.yaml")
    print("2. Adjust risk parameters and strategy settings")
    print("3. Test with paper trading first (PAPER_TRADING=true)")
    print("4. Run a backtest: python main.py backtest -s moving_average")
    print("5. Start paper trading: python main.py live-trade -s moving_average --paper")
    
    print("\n⚠️  Important Notes:")
    print("- Always test with paper trading first")
    print("- Review risk management settings carefully")
    print("- Monitor your positions and P&L regularly")
    print("- Keep your API credentials secure")
    
    print("\n📚 Documentation:")
    print("- ICICI Breeze API: https://api.icicidirect.com/breezeapi/documents/")
    print("- Project README: README.md")


def main():
    """Main setup function."""
    print_banner()
    
    # Check requirements
    if not check_requirements():
        return
    
    # Setup directories
    setup_directories()
    
    # Setup logging
    setup_logging(level=logging.INFO, console_logging=True)
    
    # Setup API credentials
    if not setup_api_credentials():
        print("❌ Failed to setup API credentials")
        return
    
    # Test connection
    if test_connection():
        display_next_steps()
    else:
        print("\n❌ Setup completed but connection test failed.")
        print("Please check your credentials and try again.")


if __name__ == "__main__":
    import logging
    main()