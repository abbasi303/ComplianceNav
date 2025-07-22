#!/usr/bin/env python3
"""
Demo: Advanced Agentic Regulatory Discovery
Showcases cutting-edge techniques for finding real regulatory links
"""

import asyncio
import json
from datetime import datetime
from loguru import logger

# Import our advanced agents
from agents.web_discovery_agent import web_discovery_agent
from agents.api_integration_agent import api_integration_agent
from agents.link_validation_agent import link_validation_agent
from agents.realtime_monitoring_agent import realtime_monitoring_agent


async def demo_web_discovery():
    """Demo web discovery capabilities"""
    print("\n" + "="*60)
    print("🌐 WEB DISCOVERY AGENT DEMO")
    print("="*60)
    
    try:
        # Discover regulatory sources for Pakistan robotics
        print("🔍 Discovering regulatory sources for Pakistan robotics industry...")
        
        discovered_docs = await web_discovery_agent.discover_regulatory_sources(
            country="Pakistan",
            industry="robotics",
            business_activities=["manufacturing", "automation", "AI systems"]
        )
        
        print(f"✅ Discovered {len(discovered_docs)} regulatory sources")
        
        for i, doc in enumerate(discovered_docs[:3], 1):
            print(f"\n📄 Source {i}:")
            print(f"   Title: {doc.title}")
            print(f"   Authority: {doc.authority}")
            print(f"   URL: {doc.url or 'No direct link'}")
            print(f"   Relevance: {doc.relevance_score:.2f}")
            print(f"   Discovery Method: {getattr(doc, 'discovery_method', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ Web discovery demo failed: {e}")


async def demo_api_integration():
    """Demo API integration capabilities"""
    print("\n" + "="*60)
    print("🔌 API INTEGRATION AGENT DEMO")
    print("="*60)
    
    try:
        # Discover and integrate APIs
        print("🔍 Discovering regulatory APIs...")
        
        api_docs = await api_integration_agent.discover_and_integrate_apis(
            country="Germany",
            industry="financial services",
            business_activities=["banking", "payment processing"]
        )
        
        print(f"✅ Retrieved {len(api_docs)} documents from APIs")
        
        for i, doc in enumerate(api_docs[:3], 1):
            print(f"\n📄 API Document {i}:")
            print(f"   Title: {doc.title}")
            print(f"   Source: {doc.source}")
            print(f"   URL: {doc.url or 'No direct link'}")
            print(f"   Regulation Type: {doc.regulation_type}")
            
    except Exception as e:
        print(f"❌ API integration demo failed: {e}")


async def demo_link_validation():
    """Demo link validation capabilities"""
    print("\n" + "="*60)
    print("✅ LINK VALIDATION AGENT DEMO")
    print("="*60)
    
    try:
        # Create test documents
        from core.data_models import RegulatoryDocument
        
        test_docs = [
            RegulatoryDocument(
                title="Test EU Regulation",
                content="Test content for EU regulation",
                source="European Commission",
                country="EU",
                regulation_type="regulation",
                url="https://eur-lex.europa.eu/eli/reg/2016/679/oj",
                authority="European Commission",
                relevance_score=0.8
            ),
            RegulatoryDocument(
                title="Test German Law",
                content="Test content for German law",
                source="German Government",
                country="Germany",
                regulation_type="law",
                url="https://www.gesetze-im-internet.de/bdsg_2018/",
                authority="German Government",
                relevance_score=0.7
            )
        ]
        
        print("🔍 Validating regulatory links...")
        
        validated_docs = await link_validation_agent.validate_regulatory_links(test_docs)
        
        print(f"✅ Validated {len(validated_docs)} documents")
        
        for i, doc in enumerate(validated_docs, 1):
            validation_data = getattr(doc, 'validation_metadata', {})
            print(f"\n📄 Validated Document {i}:")
            print(f"   Title: {doc.title}")
            print(f"   URL: {doc.url}")
            print(f"   Is Valid: {validation_data.get('is_valid', 'Unknown')}")
            print(f"   Authority Verified: {validation_data.get('authority_verified', 'Unknown')}")
            print(f"   Accessibility Score: {validation_data.get('accessibility_score', 'Unknown')}")
            print(f"   Content Freshness: {validation_data.get('content_freshness', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ Link validation demo failed: {e}")


async def demo_realtime_monitoring():
    """Demo real-time monitoring capabilities"""
    print("\n" + "="*60)
    print("📡 REAL-TIME MONITORING AGENT DEMO")
    print("="*60)
    
    try:
        # Test URLs for monitoring
        test_urls = [
            "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
            "https://www.gesetze-im-internet.de/bdsg_2018/"
        ]
        
        # Mock startup info
        class MockStartupInfo:
            industry = "technology"
            business_activities = ["software development", "data processing"]
        
        startup_info = MockStartupInfo()
        
        print("🔍 Starting real-time monitoring...")
        
        monitoring_results = await realtime_monitoring_agent.start_monitoring(
            test_urls, startup_info
        )
        
        print(f"✅ Monitored {len(monitoring_results)} URLs")
        
        for i, result in enumerate(monitoring_results, 1):
            print(f"\n📡 Monitoring Result {i}:")
            print(f"   URL: {result.url}")
            print(f"   Has Changes: {result.has_changes}")
            print(f"   Change Type: {result.change_type}")
            print(f"   Confidence: {result.monitoring_confidence:.2f}")
            print(f"   Last Check: {result.last_check}")
            
        # Get monitoring summary
        summary = await realtime_monitoring_agent.get_monitoring_summary()
        print(f"\n📊 Monitoring Summary:")
        print(f"   Total URLs Monitored: {summary['total_urls_monitored']}")
        print(f"   URLs with Changes: {summary['urls_with_changes']}")
        print(f"   Recent Alerts: {len(summary['recent_alerts'])}")
            
    except Exception as e:
        print(f"❌ Real-time monitoring demo failed: {e}")


async def demo_integrated_workflow():
    """Demo integrated workflow with all agents"""
    print("\n" + "="*60)
    print("🚀 INTEGRATED AGENTIC WORKFLOW DEMO")
    print("="*60)
    
    try:
        print("🔄 Running integrated agentic workflow...")
        
        # Step 1: Web Discovery
        print("\n1️⃣ Web Discovery Phase...")
        web_docs = await web_discovery_agent.discover_regulatory_sources(
            country="Pakistan",
            industry="robotics",
            business_activities=["manufacturing", "automation"]
        )
        print(f"   ✅ Found {len(web_docs)} documents via web discovery")
        
        # Step 2: API Integration
        print("\n2️⃣ API Integration Phase...")
        api_docs = await api_integration_agent.discover_and_integrate_apis(
            country="Pakistan",
            industry="robotics",
            business_activities=["manufacturing", "automation"]
        )
        print(f"   ✅ Found {len(api_docs)} documents via API integration")
        
        # Step 3: Link Validation
        print("\n3️⃣ Link Validation Phase...")
        all_docs = web_docs + api_docs
        validated_docs = await link_validation_agent.validate_regulatory_links(all_docs)
        print(f"   ✅ Validated {len(validated_docs)} documents")
        
        # Step 4: Real-time Monitoring Setup
        print("\n4️⃣ Real-time Monitoring Setup...")
        urls_to_monitor = [doc.url for doc in validated_docs if doc.url]
        if urls_to_monitor:
            class MockStartupInfo:
                industry = "robotics"
                business_activities = ["manufacturing", "automation"]
            
            monitoring_results = await realtime_monitoring_agent.start_monitoring(
                urls_to_monitor[:3], MockStartupInfo()  # Monitor top 3 URLs
            )
            print(f"   ✅ Set up monitoring for {len(monitoring_results)} URLs")
        
        # Summary
        print(f"\n🎯 INTEGRATED WORKFLOW SUMMARY:")
        print(f"   Web Discovery: {len(web_docs)} documents")
        print(f"   API Integration: {len(api_docs)} documents")
        print(f"   Validated: {len(validated_docs)} documents")
        print(f"   Monitoring: {len(urls_to_monitor)} URLs")
        
        # Show top results
        print(f"\n🏆 TOP DISCOVERED REGULATIONS:")
        for i, doc in enumerate(validated_docs[:5], 1):
            print(f"   {i}. {doc.title}")
            print(f"      Authority: {doc.authority}")
            print(f"      URL: {doc.url or 'No direct link'}")
            print(f"      Relevance: {doc.relevance_score:.2f}")
            
    except Exception as e:
        print(f"❌ Integrated workflow demo failed: {e}")


async def main():
    """Run all demos"""
    print("🤖 ADVANCED AGENTIC REGULATORY DISCOVERY DEMO")
    print("="*60)
    print("This demo showcases cutting-edge techniques for finding real regulatory links")
    print("="*60)
    
    # Run individual demos
    await demo_web_discovery()
    await demo_api_integration()
    await demo_link_validation()
    await demo_realtime_monitoring()
    
    # Run integrated workflow
    await demo_integrated_workflow()
    
    print("\n" + "="*60)
    print("🎉 DEMO COMPLETED!")
    print("="*60)
    print("Key Features Demonstrated:")
    print("✅ Live web crawling and discovery")
    print("✅ Dynamic API integration")
    print("✅ AI-powered link validation")
    print("✅ Real-time monitoring")
    print("✅ Integrated agentic workflow")
    print("="*60)


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level="INFO")
    
    # Run the demo
    asyncio.run(main()) 