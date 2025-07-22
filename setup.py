#!/usr/bin/env python3
"""
ComplianceNavigator Setup Script
Automated setup and configuration for the compliance analysis system
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Print the setup banner"""
    print("🏛️" + "=" * 60 + "🏛️")
    print("     ComplianceNavigator Setup & Configuration")
    print("     AI-Powered Regulatory Compliance Analysis")
    print("🏛️" + "=" * 60 + "🏛️")
    print()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 10):
        print("❌ Error: Python 3.10+ is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python version: {sys.version.split()[0]}")

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("   Please run: pip install -r requirements.txt")
        sys.exit(1)

def setup_environment():
    """Set up environment configuration"""
    print("\n⚙️  Setting up environment...")
    
    env_template_path = Path(".env_template")
    env_path = Path(".env")
    
    if not env_template_path.exists():
        print("❌ .env_template file not found")
        sys.exit(1)
    
    if env_path.exists():
        overwrite = input("   .env file already exists. Overwrite? (y/N): ").lower()
        if overwrite != 'y':
            print("   Keeping existing .env file")
            return
    
    # Copy template to .env
    shutil.copy(env_template_path, env_path)
    print("✅ Environment file created")
    
    # Prompt for Gemini API key
    print("\n🔑 API Key Configuration")
    print("   You need a Google Gemini API key to use this application.")
    print("   Get one at: https://makersuite.google.com/app/apikey")
    
    api_key = input("\n   Enter your Gemini API key (or press Enter to configure later): ").strip()
    
    if api_key:
        # Update the .env file with the API key
        with open(env_path, 'r') as f:
            content = f.read()
        
        content = content.replace('GEMINI_API_KEY=your_gemini_api_key_here', f'GEMINI_API_KEY={api_key}')
        
        with open(env_path, 'w') as f:
            f.write(content)
        
        print("✅ API key configured successfully")
    else:
        print("⚠️  Remember to add your API key to the .env file before running the application")

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "data",
        "data/regulations", 
        "data/chroma_db",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")

def test_installation():
    """Test the installation"""
    print("\n🧪 Testing installation...")
    
    try:
        # Test imports
        sys.path.insert(0, '.')
        from config.settings import settings
        from integrations.gemini_client import gemini_client
        from core.vector_store import vector_store
        
        print("✅ Core modules imported successfully")
        
        # Test Gemini API key (if configured)
        if settings.gemini_api_key != "your_gemini_api_key_here":
            print("✅ Gemini API key configured")
        else:
            print("⚠️  Gemini API key not configured - you'll need to add it to .env")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def show_next_steps():
    """Show next steps after setup"""
    print("\n🚀 Setup Complete!")
    print("\nNext steps:")
    print("1. If you haven't already, add your Gemini API key to the .env file")
    print("2. Run the application:")
    print("   • Web interface: python main.py")
    print("   • Command line: python main.py cli")
    print("   • Test mode: python main.py test")
    print("\n3. Visit http://localhost:8501 for the web interface")
    print("\n📚 Documentation: See README.md for detailed usage instructions")
    print("🐛 Issues: Report bugs at https://github.com/your-username/compliance-navigator/issues")

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Set up environment
    setup_environment()
    
    # Create directories
    create_directories()
    
    # Test installation
    if test_installation():
        show_next_steps()
    else:
        print("\n❌ Setup completed with errors. Please check the messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 