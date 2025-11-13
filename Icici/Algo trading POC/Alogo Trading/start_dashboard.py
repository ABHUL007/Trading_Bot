"""
Startup script for ICICI Breeze Live Trading Dashboard
Runs all necessary components and opens dashboard in browser
"""

import os
import sys
import time
import webbrowser
import subprocess
from pathlib import Path

def main():
    print("=" * 80)
    print("🚀 ICICI Breeze Live Trading Dashboard Startup")
    print("=" * 80)
    
    # Get project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("📁 Project Directory:", project_dir)
    print("🔧 Checking environment...")
    
    # Check if virtual environment exists
    venv_path = project_dir / ".venv"
    if not venv_path.exists():
        print("⚠️  Virtual environment not found. Creating one...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"])
        print("✓ Virtual environment created")
    
    # Activate virtual environment and install requirements
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    if not python_exe.exists():
        print("❌ Failed to create virtual environment")
        return
    
    print("📦 Installing/updating requirements...")
    subprocess.run([str(pip_exe), "install", "-r", "requirements.txt"], 
                  capture_output=True, text=True)
    print("✓ Requirements installed")
    
    # Check if session token is configured
    env_file = project_dir / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
        if "SESSION_TOKEN=53448258" in env_content:
            print("✓ Session token configured")
        else:
            print("⚠️  Please update your API credentials in .env file")
    else:
        print("⚠️  .env file not found. Please create one with your API credentials")
    
    print("\n🎯 Starting components...")
    
    # Start the Flask server
    print("🌐 Starting Flask-SocketIO server...")
    
    try:
        # Run the Flask app
        subprocess.Popen([str(python_exe), "app.py"], 
                        cwd=project_dir)
        
        print("✓ Server starting...")
        print("⏳ Waiting for server to initialize...")
        time.sleep(5)
        
        # Open dashboard in browser
        dashboard_url = "http://localhost:5000"
        print(f"🌐 Opening dashboard: {dashboard_url}")
        webbrowser.open(dashboard_url)
        
        print("\n" + "=" * 80)
        print("✅ DASHBOARD LAUNCHED SUCCESSFULLY!")
        print("=" * 80)
        print("📊 Dashboard URL: http://localhost:5000")
        print("🔑 Configure your API credentials in the dashboard")
        print("📱 Session Token: 53448258 (already configured)")
        print("🎯 Features Available:")
        print("   • Real-time NIFTY price streaming")
        print("   • ML-powered breakout/breakdown predictions")
        print("   • Cross-timeframe resistance/support analysis")
        print("   • Live trading alerts and notifications")
        print("   • Order placement (paper trading mode)")
        print("=" * 80)
        print("💡 Tips:")
        print("   • Update API_KEY and API_SECRET in .env file")
        print("   • Click 'Update Session' in dashboard to connect")
        print("   • Monitor console for ML predictions and alerts")
        print("=" * 80)
        
        # Keep script running
        input("Press Enter to stop the dashboard...")
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        print("💡 Try running 'python app.py' manually for more details")

if __name__ == "__main__":
    main()