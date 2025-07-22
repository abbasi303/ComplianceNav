"""
ComplianceNavigator - Main Application Entry Point
"""
import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from loguru import logger
from config.settings import settings

def setup_logging():
    """Configure logging for the application"""
    logger.remove()  # Remove default handler
    
    # Console logging
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # File logging
    logger.add(
        settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days"
    )
    
    logger.info("ComplianceNavigator logging configured")

def check_dependencies():
    """Check if all required dependencies are available"""
    try:
        # Check Gemini API key
        if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
            logger.error("Gemini API key not configured. Please set GEMINI_API_KEY in your .env file")
            return False
        
        # Test imports
        from integrations.gemini_client import gemini_client
        from core.vector_store import vector_store
        from core.orchestrator import orchestrator
        
        logger.info("All dependencies available")
        return True
        
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return False
    except Exception as e:
        logger.error(f"Dependency check failed: {e}")
        return False

async def test_workflow():
    """Test the workflow with a sample query"""
    logger.info("Testing ComplianceNavigator workflow...")
    
    try:
        from core.orchestrator import orchestrator
        
        sample_query = """
        I'm launching a telemedicine platform in Germany that allows patients to consult 
        with doctors via video calls. We'll be handling personal health data, processing 
        payments, and storing medical records. Our target market includes both individual 
        patients and healthcare providers.
        """
        
        logger.info("Running sample compliance analysis...")
        results = await orchestrator.process_compliance_request(
            user_query=sample_query,
            user_id="test_user"
        )
        
        if results.get('status') == 'completed':
            logger.success("✅ Workflow test completed successfully!")
            logger.info(f"Found {results.get('compliance_analysis', {}).get('gaps_found', 0)} compliance gaps")
            logger.info(f"Generated {results.get('implementation_plan', {}).get('total_action_items', 0)} action items")
            return True
        else:
            logger.error("❌ Workflow test failed")
            logger.error(f"Results: {results}")
            return False
            
    except Exception as e:
        logger.error(f"Workflow test error: {e}")
        return False

def run_streamlit_app():
    """Launch the Streamlit application"""
    logger.info("Starting Streamlit application...")
    
    try:
        import subprocess
        import sys
        
        # Run streamlit
        cmd = [
            sys.executable, 
            "-m", "streamlit", "run", 
            "ui/streamlit_app.py",
            "--server.port", str(settings.streamlit_port),
            "--server.address", "localhost"
        ]
        
        logger.info(f"Launching Streamlit on port {settings.streamlit_port}")
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Failed to start Streamlit app: {e}")

def run_cli_mode():
    """Run in command-line interface mode"""
    logger.info("Running ComplianceNavigator in CLI mode")
    
    print("🏛️  ComplianceNavigator - Regulatory Compliance Analysis")
    print("=" * 60)
    
    try:
        from core.orchestrator import orchestrator
        
        # Get user input
        print("\n📝 Describe your startup (press Enter twice when finished):")
        lines = []
        while True:
            line = input()
            if line == "" and lines:
                break
            lines.append(line)
        
        user_query = "\n".join(lines)
        
        if not user_query.strip():
            print("❌ No startup description provided. Exiting.")
            return
        
        print("\n🔄 Analyzing compliance requirements...")
        
        # Run analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        results = loop.run_until_complete(
            orchestrator.process_compliance_request(
                user_query=user_query,
                user_id="cli_user"
            )
        )
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 COMPLIANCE ANALYSIS RESULTS")
        print("=" * 60)
        
        if results.get('status') == 'completed':
            startup_info = results.get('startup_info', {})
            print(f"\n🏢 Industry: {startup_info.get('industry', 'N/A')}")
            print(f"🌍 Target Countries: {', '.join(startup_info.get('target_countries', []))}")
            
            compliance_analysis = results.get('compliance_analysis', {})
            gaps_found = compliance_analysis.get('gaps_found', 0)
            risk_level = compliance_analysis.get('overall_risk_level', 'unknown')
            
            print(f"\n⚠️  Compliance Gaps Found: {gaps_found}")
            print(f"📈 Overall Risk Level: {risk_level.upper()}")
            
            # Show recommendations
            recommendations = compliance_analysis.get('recommendations_summary', '')
            if recommendations:
                print(f"\n💡 Key Recommendations:")
                print(recommendations)
            
            # Show action plan
            implementation_plan = results.get('implementation_plan', {})
            if implementation_plan:
                action_items = implementation_plan.get('total_action_items', 0)
                cost = implementation_plan.get('total_estimated_cost', 'N/A')
                print(f"\n📅 Implementation Plan: {action_items} action items")
                print(f"💰 Estimated Cost: {cost}")
            
            print(f"\n✅ Analysis completed successfully!")
            print(f"📡 Monitoring has been set up for ongoing regulatory updates.")
        
        else:
            print(f"❌ Analysis failed: {results.get('error', 'Unknown error')}")
    
    except KeyboardInterrupt:
        print("\n👋 Analysis cancelled by user")
    except Exception as e:
        logger.error(f"CLI mode error: {e}")
        print(f"❌ Error: {e}")

def main():
    """Main application entry point"""
    setup_logging()
    
    logger.info("🏛️  Starting ComplianceNavigator")
    
    # Check dependencies
    if not check_dependencies():
        logger.error("❌ Dependency check failed. Please check your configuration.")
        sys.exit(1)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            # Test mode
            logger.info("Running in test mode...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(test_workflow())
            sys.exit(0 if success else 1)
        
        elif command == "cli":
            # CLI mode
            run_cli_mode()
            
        elif command == "web":
            # Web mode (Streamlit)
            run_streamlit_app()
            
        else:
            print("Usage: python main.py [test|cli|web]")
            print("  test - Run workflow test")
            print("  cli  - Run in command-line mode")
            print("  web  - Launch web interface (default)")
            sys.exit(1)
    
    else:
        # Default: run Streamlit app
        run_streamlit_app()

if __name__ == "__main__":
    main() 