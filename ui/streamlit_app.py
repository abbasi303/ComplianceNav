"""
ComplianceNavigator Streamlit Interface
Main user interface for the compliance analysis application
"""
import streamlit as st
import asyncio
from typing import Dict, Any
import json
import time
from datetime import datetime
import os
import csv
from pathlib import Path

# Import the orchestrator and other components
try:
    from core.orchestrator import orchestrator
    from core.vector_store import vector_store
    from config.settings import settings
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Export functions
def export_results_json(results: Dict[str, Any]) -> str:
    """Export complete results to JSON file"""
    try:
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        workflow_id = results.get('workflow_id', 'unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_analysis_{workflow_id}_{timestamp}.json"
        filepath = results_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)
        
        return str(filepath)
    except Exception as e:
        st.error(f"Error exporting JSON: {e}")
        return ""

def export_results_summary(results: Dict[str, Any]) -> str:
    """Export human-readable summary with source information to text file"""
    try:
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        workflow_id = results.get('workflow_id', 'unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_summary_{workflow_id}_{timestamp}.txt"
        filepath = results_dir / filename
        
        startup_info = results.get('startup_info', {})
        compliance_analysis = results.get('compliance_analysis', {})
        implementation_plan = results.get('implementation_plan', {})
        
        summary = f"""
COMPLIANCE ANALYSIS SUMMARY
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Workflow ID: {workflow_id}

STARTUP INFORMATION
Company: {startup_info.get('company_name', 'N/A')}
Industry: {startup_info.get('industry', 'N/A')}
Target Countries: {', '.join(startup_info.get('target_countries', []))}
Business Activities: {len(startup_info.get('business_activities', []))} identified
Data Handling: {', '.join(startup_info.get('data_handling', [])) or 'None specified'}

ANALYSIS RESULTS
Risk Level: {compliance_analysis.get('overall_risk_level', 'N/A').upper()}
Compliance Gaps Found: {compliance_analysis.get('gaps_found', 0)}
Compliant Areas: {compliance_analysis.get('compliant_areas', 0)}
Action Items Generated: {implementation_plan.get('total_action_items', 0)}
Estimated Total Cost: {implementation_plan.get('total_estimated_cost', 'N/A')}

KEY RECOMMENDATIONS
{compliance_analysis.get('recommendations_summary', 'No recommendations available')}

SOURCE QUALITY ASSESSMENT"""
        
        # Get compliance gaps data first
        gaps = compliance_analysis.get('compliance_gaps', [])
        
        # Calculate source statistics
        gaps_with_sources = sum(1 for gap in gaps if gap.get('primary_sources') or gap.get('supporting_sources'))
        gaps_without_sources = len(gaps) - gaps_with_sources
        source_percentage = (gaps_with_sources/len(gaps)*100) if gaps else 0
        
        summary += f"\nGaps with Sources: {gaps_with_sources}/{len(gaps)} ({source_percentage:.0f}%)"
        summary += f"\nGaps without Sources: {gaps_without_sources}"
        
        if gaps_without_sources > 0:
            summary += f"\nWARNING: Some compliance gaps lack regulatory source backing - Professional legal review strongly recommended"
        else:
            summary += f"\nAll gaps have some source backing"
        
        summary += f"""

COMPLIANCE GAPS SUMMARY
"""
        for i, gap in enumerate(gaps[:10], 1):  # Limit to top 10
            summary += f"\n{i}. {gap.get('title', 'Unknown Gap')} [{gap.get('severity', 'unknown').upper()}]"
            summary += f"\n   Country: {gap.get('country', 'N/A')}"
            summary += f"\n   Type: {gap.get('gap_type', 'N/A').replace('_', ' ').title()}"
            summary += f"\n   Actions: {len(gap.get('recommended_actions', []))} recommended"
            
            # Add source quality indicator
            primary_sources = gap.get('primary_sources', [])
            supporting_sources = gap.get('supporting_sources', [])
            
            if primary_sources:
                summary += f"\n   Sources: {len(primary_sources)} primary, {len(supporting_sources)} supporting"
            elif supporting_sources:
                summary += f"\n   Sources: {len(supporting_sources)} supporting only (no primary sources)"
            else:
                summary += f"\n   Sources: None found - requires manual verification"
            
            summary += "\n"
        
        if len(gaps) > 10:
            summary += f"\n... and {len(gaps) - 10} more gaps (see JSON export for complete list)"
        
        summary += f"""

IMPLEMENTATION TIMELINE
{implementation_plan.get('implementation_timeline', 'No timeline available')}

MONITORING
Monitoring has been set up for ongoing regulatory updates.
Next Review Date: {implementation_plan.get('next_review_date', 'N/A')}

SOURCE RELIABILITY DISCLAIMER
This analysis combines AI-powered research with available regulatory sources.
Source quality varies - gaps marked with no sources require additional verification.
For legal compliance purposes, always consult with qualified legal counsel
and verify requirements against official regulatory publications.

---
Generated by ComplianceNavigator
For complete technical details and sources, see the JSON export file.
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(summary.strip())
        
        return str(filepath)
    except Exception as e:
        st.error(f"Error exporting summary: {e}")
        return ""

def export_results_csv(results: Dict[str, Any]) -> str:
    """Export compliance gaps to CSV file"""
    try:
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        workflow_id = results.get('workflow_id', 'unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_gaps_{workflow_id}_{timestamp}.csv"
        filepath = results_dir / filename
        
        compliance_analysis = results.get('compliance_analysis', {})
        gaps = compliance_analysis.get('compliance_gaps', [])
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Gap Title', 'Severity', 'Country', 'Gap Type', 'Business Activity',
                'Description', 'Recommended Actions', 'Deadline', 'Estimated Cost'
            ])
            
            # Data rows
            for gap in gaps:
                writer.writerow([
                    gap.get('title', ''),
                    gap.get('severity', ''),
                    gap.get('country', ''),
                    gap.get('gap_type', '').replace('_', ' ').title(),
                    gap.get('business_activity', ''),
                    gap.get('description', '')[:200] + ('...' if len(gap.get('description', '')) > 200 else ''),
                    '; '.join(gap.get('recommended_actions', [])),
                    gap.get('deadline', ''),
                    gap.get('estimated_cost', '')
                ])
        
        return str(filepath)
    except Exception as e:
        st.error(f"Error exporting CSV: {e}")
        return ""

def init_session_state():
    """Initialize Streamlit session state variables"""
    if 'workflow_results' not in st.session_state:
        st.session_state.workflow_results = None
    if 'analysis_in_progress' not in st.session_state:
        st.session_state.analysis_in_progress = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = f"user_{hash(str(datetime.now())) % 10000}"
    # No longer needed with Streamlit's native dark theme
    pass

def apply_dark_mode_theme():
    """No longer needed with Streamlit's native dark theme"""
    pass

def main():
    """Main Streamlit application"""
    
    # Page configuration with dark theme
    st.set_page_config(
        page_title="ComplianceNavigator",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    
    # Set Streamlit theme to dark
    st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    init_session_state()
    
    # Streamlit's native dark theme is now used
    pass
    
    # Add the main CSS styles
    st.markdown("""
    <style>
    /* CSS Variables for theming */
    :root {
        --bg-gradient-light: linear-gradient(135deg, #f0f4ff 0%, #e0e7ff 50%, #c7d2fe 100%);
        --card-bg-light: rgba(255, 255, 255, 0.95);
        --text-primary-light: #0f172a;
        --text-secondary-light: #64748b;
        --border-light: rgba(255, 255, 255, 0.2);
        --shadow-light: rgba(0, 0, 0, 0.1);
        
        --bg-gradient-dark: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        --card-bg-dark: rgba(30, 41, 59, 0.95);
        --text-primary-dark: #f8fafc;
        --text-secondary-dark: #cbd5e1;
        --border-dark: rgba(51, 65, 85, 0.3);
        --shadow-dark: rgba(0, 0, 0, 0.3);
    }
    
    /* Elegant header with subtle depth */
    .main-header {
        text-align: center;
        background: var(--card-bg-light);
        backdrop-filter: blur(10px);
        color: var(--text-primary-light);
        padding: 4rem 2rem;
        margin-bottom: 3rem;
        border-radius: 16px;
        box-shadow: 
            0 4px 6px -1px var(--shadow-light),
            0 2px 4px -1px var(--shadow-light),
            inset 0 1px 0 rgba(255, 255, 255, 0.8);
        border: 1px solid var(--border-light);
        transition: all 0.3s ease;
    }
    
    [data-theme="dark"] .main-header {
        background: var(--card-bg-dark);
        color: var(--text-primary-dark);
        box-shadow: 
            0 4px 6px -1px var(--shadow-dark),
            0 2px 4px -1px var(--shadow-dark),
            inset 0 1px 0 rgba(51, 65, 85, 0.8);
        border: 1px solid var(--border-dark);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #3730a3 0%, #6366f1 50%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.025em;
    }
    
    .main-header p {
        margin: 1rem 0 0 0;
        font-size: 1.125rem;
        color: var(--text-secondary-light);
        font-weight: 500;
        transition: color 0.3s ease;
    }
    
    [data-theme="dark"] .main-header p {
        color: var(--text-secondary-dark);
    }
    
    /* Enhanced modern card containers */
    .card-container {
        background: var(--card-bg-light);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 2.5rem;
        margin: 1.5rem 0;
        border: 1px solid var(--border-light);
        box-shadow: 
            0 8px 25px -5px var(--shadow-light),
            0 4px 6px -2px var(--shadow-light),
            inset 0 1px 0 rgba(255, 255, 255, 0.6);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .card-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #3730a3, #6366f1, #8b5cf6);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .card-container:hover::before {
        opacity: 1;
    }
    
    .card-container:hover {
        transform: translateY(-8px) scale(1.01);
        box-shadow: 
            0 20px 40px -8px var(--shadow-light),
            0 10px 25px -5px var(--shadow-light),
            inset 0 1px 0 rgba(255, 255, 255, 0.8);
    }
    
    [data-theme="dark"] .card-container {
        background: var(--card-bg-dark) !important;
        background-color: rgba(30, 41, 59, 0.95) !important;
        border: 1px solid var(--border-dark) !important;
        box-shadow: 
            0 4px 6px -1px var(--shadow-dark),
            0 2px 4px -1px var(--shadow-dark);
    }
    
    /* Additional dark mode container targeting */
    .dark-theme .card-container,
    [data-theme="dark"] .card-container,
    body.dark-theme .card-container {
        background-color: rgba(30, 41, 59, 0.95) !important;
        border-color: rgba(71, 85, 105, 0.5) !important;
    }
    
    /* Enhanced typography */
    .card-title {
        color: var(--text-primary-light);
        font-weight: 700;
        margin-bottom: 1rem;
        font-size: 1.5rem;
        letter-spacing: -0.025em;
        transition: all 0.3s ease;
        position: relative;
        background: linear-gradient(135deg, #3730a3, #6366f1, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    [data-theme="dark"] .card-title {
        color: var(--text-primary-dark);
        text-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
    }
    
    .card-subtitle {
        color: var(--text-secondary-light);
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 500;
        transition: color 0.3s ease;
        line-height: 1.6;
        opacity: 0.8;
    }
    
    [data-theme="dark"] .card-subtitle {
        color: var(--text-secondary-dark);
        opacity: 0.9;
    }
    
    /* Enhanced button styling with micro-interactions */
    .stButton > button {
        background: linear-gradient(135deg, #3730a3 0%, #6366f1 50%, #8b5cf6 100%);
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 0.875rem 1.75rem;
        font-weight: 600;
        font-size: 0.875rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 
            0 4px 6px -1px rgba(99, 102, 241, 0.2),
            0 2px 4px -1px rgba(99, 102, 241, 0.1);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
        letter-spacing: 0.025em;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #4338ca 0%, #6366f1 50%, #a855f7 100%);
        transform: translateY(-3px) scale(1.02);
        box-shadow: 
            0 12px 20px -3px rgba(99, 102, 241, 0.4),
            0 8px 16px -4px rgba(99, 102, 241, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    .stButton > button:active {
        transform: translateY(-1px) scale(0.98);
        transition: all 0.1s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Dark mode toggle button */
    .dark-mode-toggle {
        background: linear-gradient(135deg, #374151 0%, #4B5563 50%, #6B7280 100%) !important;
        color: white !important;
        border-radius: 50% !important;
        width: 3rem !important;
        height: 3rem !important;
        font-size: 1.2rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: none !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }
    
    .dark-mode-toggle:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Enhanced metrics styling */
    .stMetric {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(248, 250, 252, 0.8)) !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        border: 1px solid rgba(99, 102, 241, 0.1) !important;
        box-shadow: 
            0 8px 25px -5px rgba(0, 0, 0, 0.1),
            0 4px 6px -2px rgba(0, 0, 0, 0.05),
            inset 0 1px 0 rgba(255, 255, 255, 0.8) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .stMetric:hover {
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 
            0 20px 40px -8px rgba(99, 102, 241, 0.15),
            0 10px 25px -5px rgba(99, 102, 241, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
    }
    
    .stMetric::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #3730a3, #6366f1, #8b5cf6);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .stMetric:hover::before {
        opacity: 1;
    }
    
    [data-theme="dark"] .stMetric {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(51, 65, 85, 0.8)) !important;
        border-color: rgba(99, 102, 241, 0.3) !important;
        box-shadow: 
            0 8px 25px -5px rgba(0, 0, 0, 0.4),
            0 4px 6px -2px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(51, 65, 85, 0.8) !important;
    }
    
    [data-theme="dark"] .stMetric:hover {
        box-shadow: 
            0 20px 40px -8px rgba(99, 102, 241, 0.3),
            0 10px 25px -5px rgba(99, 102, 241, 0.2),
            inset 0 1px 0 rgba(51, 65, 85, 0.9) !important;
    }
    
    /* Enhanced progress bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #3730a3, #6366f1, #8b5cf6) !important;
        border-radius: 8px !important;
        box-shadow: 
            0 2px 4px -1px rgba(99, 102, 241, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .stProgress > div > div > div::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    /* Enhanced expanders */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.9) !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(99, 102, 241, 0.1) !important;
        padding: 1.25rem !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 
            0 4px 6px -1px rgba(0, 0, 0, 0.1),
            0 2px 4px -1px rgba(0, 0, 0, 0.05) !important;
    }
    
    .streamlit-expanderHeader:hover {
        transform: translateY(-2px) !important;
        box-shadow: 
            0 8px 15px -3px rgba(99, 102, 241, 0.2),
            0 4px 6px -2px rgba(99, 102, 241, 0.1) !important;
        border-color: rgba(99, 102, 241, 0.3) !important;
    }
    
    [data-theme="dark"] .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.9) !important;
        border-color: rgba(99, 102, 241, 0.3) !important;
        color: #f8fafc !important;
        box-shadow: 
            0 4px 6px -1px rgba(0, 0, 0, 0.3),
            0 2px 4px -1px rgba(0, 0, 0, 0.2) !important;
    }
    
    [data-theme="dark"] .streamlit-expanderHeader:hover {
        box-shadow: 
            0 8px 15px -3px rgba(99, 102, 241, 0.4),
            0 4px 6px -2px rgba(99, 102, 241, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Clean header
    st.markdown("""
    <div class="main-header">
        <h1>ComplianceNavigator</h1>
        <p>AI-Powered Regulatory Compliance Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("System Status")
        
        # Vector store stats
        try:
            stats = vector_store.get_collection_stats()
            st.metric("Regulatory Documents", stats.get('regulations_count', 0))
            st.metric("Historical Cases", stats.get('compliance_cases_count', 0))
            
            # Show what these numbers mean
            with st.expander("What do these numbers mean?", expanded=False):
                st.write("**Regulatory Documents:** Total regulations stored in the system database")
                st.write("**Historical Cases:** Compliance gaps identified in previous analyses + regulatory alerts")
                st.caption("Note: Your current analysis results are shown separately below")
        except Exception as e:
            st.warning(f"Could not load vector store stats: {e}")
        
        
        st.header("Settings")
        
        
        # Analysis settings
        analysis_depth = st.selectbox(
            "Analysis Depth",
            ["Standard", "Comprehensive", "Quick"],
            index=0,
            help="Choose the depth of regulatory analysis"
        )
        
        include_monitoring = st.checkbox(
            "Enable Monitoring",
            value=True,
            help="Set up ongoing regulatory monitoring for your startup"
        )
        
        # User info
        st.header("User Info")
        user_name = st.text_input("Your Name (Optional)", placeholder="John Doe")
        user_email = st.text_input("Email (Optional)", placeholder="john@startup.com")
        
        if user_name:
            st.session_state.user_id = f"user_{hash(user_name) % 10000}"
    
    # Main content area with modern layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Modern card for startup description
        st.markdown("""
        <div class="card-container">
            <div class="card-title">Describe Your Startup</div>
            <div class="card-subtitle">Tell us about your business model, target markets, and compliance concerns</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Startup description input
        startup_description = st.text_area(
            "Tell us about your startup:",
            placeholder="""Example: I'm launching a telemedicine platform in Germany that allows patients to consult with doctors via video calls. We'll be handling personal health data, processing payments, and storing medical records. Our target market includes both individual patients and healthcare providers.""",
            height=150,
            help="Provide details about your industry, business model, target countries, data handling, and any specific compliance concerns."
        )
        
        # Custom Sources Section with modern card
        st.markdown("""
        <div class="card-container">
            <div class="card-title">Custom Regulation Sources</div>
            <div class="card-subtitle">Add specific regulations, documents, or links you want the system to consider</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("Add Custom Sources", expanded=False):
            custom_sources = []
            
            # Tab for different input types
            source_tab1, source_tab2, source_tab3 = st.tabs(["URLs", "Documents", "Text"])
            
            with source_tab1:
                st.markdown("**Add regulation URLs or official government links:**")
                
                num_urls = st.number_input("Number of URLs to add", min_value=0, max_value=5, value=0)
                
                for i in range(int(num_urls)):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        url = st.text_input(f"Regulation URL #{i+1}", key=f"url_{i}", 
                                          placeholder="https://eur-lex.europa.eu/eli/reg/2016/679")
                    with col2:
                        url_desc = st.text_input(f"Description", key=f"url_desc_{i}", 
                                                placeholder="GDPR Article 32")
                    
                    if url.strip():
                        custom_sources.append({
                            "source_type": "url",
                            "content": url.strip(),
                            "user_description": url_desc.strip(),
                            "source_name": url_desc.strip() or f"URL {i+1}"
                        })
            
            with source_tab2:
                st.markdown("**Upload PDF or Word documents:**")
                
                uploaded_files = st.file_uploader(
                    "Choose regulation documents", 
                    type=['pdf', 'docx', 'txt'],
                    accept_multiple_files=True,
                    help="Upload PDFs, Word docs, or text files containing regulations"
                )
                
                if uploaded_files:
                    for file in uploaded_files:
                        file_desc = st.text_input(
                            f"Description for {file.name}",
                            key=f"file_desc_{file.name}",
                            placeholder="What regulation or document is this?"
                        )
                        
                        custom_sources.append({
                            "source_type": "pdf_upload" if file.name.endswith('.pdf') else "doc_upload",
                            "content": file.getvalue(),  # File bytes
                            "user_description": file_desc.strip(),
                            "source_name": file.name
                        })
            
            with source_tab3:
                st.markdown("**Paste regulation text or requirements:**")
                
                custom_text = st.text_area(
                    "Regulation text or requirements",
                    placeholder="Paste specific regulation text, compliance requirements, or legal provisions here...",
                    height=150
                )
                
                if custom_text.strip():
                    text_desc = st.text_input(
                        "Description of this text",
                        key="text_desc",
                        placeholder="e.g., Article 25 GDPR requirements, Pakistani SBP guidelines"
                    )
                    
                    custom_sources.append({
                        "source_type": "text_input",
                        "content": custom_text.strip(),
                        "user_description": text_desc.strip(),
                        "source_name": text_desc.strip() or "User Text"
                    })
            
            # Store custom sources in session state
            if custom_sources:
                st.session_state.custom_sources = custom_sources
                st.success(f"Added {len(custom_sources)} custom source(s)")
                
                # Show summary
                for i, source in enumerate(custom_sources):
                    st.caption(f"{i+1}. **{source['source_name']}** ({source['source_type']})")
            else:
                st.session_state.custom_sources = []

        # Example buttons with modern card
        st.markdown("""
        <div class="card-container">
            <div class="card-title">Quick Examples</div>
            <div class="card-subtitle">Get started quickly with these common business scenarios</div>
        </div>
        """, unsafe_allow_html=True)
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("Telemedicine (Germany)", key="example_telemedicine"):
                st.session_state.startup_description = "I'm launching a telemedicine platform in Germany that connects patients with doctors via video calls. We handle personal health data, store medical records, and process payments for consultations."
                st.rerun()
        
        with col_b:
            if st.button("Fintech (EU)", key="example_fintech"):
                st.session_state.startup_description = "We're building a digital banking app for the European market. We'll be handling financial transactions, storing customer financial data, and offering lending services across France, Germany, and Netherlands."
                st.rerun()
        
        with col_c:
            if st.button("E-commerce (UK)", key="example_ecommerce"):
                st.session_state.startup_description = "Our e-commerce platform sells consumer electronics across the UK. We handle customer personal data, process payments, manage inventory, and deal with product warranties and returns."
                st.rerun()
                
        # Use session state for startup description
        if 'startup_description' in st.session_state:
            startup_description = st.session_state.startup_description
        
        # Analysis button with modern card
        st.markdown("""
        <div class="card-container">
            <div class="card-title">Start Analysis</div>
            <div class="card-subtitle">Begin your compliance analysis with AI-powered insights</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Analyze Compliance Requirements", type="primary", disabled=st.session_state.analysis_in_progress):
            if not startup_description.strip():
                st.error("Please describe your startup before analyzing compliance requirements.")
            else:
                # Start compliance analysis
                st.session_state.analysis_in_progress = True
                st.rerun()
    
    with col2:
        # Analysis progress with modern card
        st.markdown("""
        <div class="card-container">
            <div class="card-title">Analysis Progress</div>
            <div class="card-subtitle">Track the status of your compliance analysis</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.analysis_in_progress:
            # Show progress
            progress_container = st.container()
            run_compliance_analysis(startup_description, progress_container)
        
        elif st.session_state.workflow_results:
            # Show quick summary
            results = st.session_state.workflow_results
            
            if results.get('status') == 'completed':
                risk_level = results.get('compliance_analysis', {}).get('overall_risk_level', 'unknown')
                risk_class = f"risk-{risk_level}"
                
                st.markdown(f'**Risk Level:** <span class="{risk_class}">{risk_level.upper()}</span>', unsafe_allow_html=True)
                
                gaps_found = results.get('compliance_analysis', {}).get('gaps_found', 0)
                st.metric("Compliance Gaps", gaps_found)
                
                action_items = results.get('implementation_plan', {}).get('total_action_items', 0)
                st.metric("Action Items", action_items)
                
                total_cost = results.get('implementation_plan', {}).get('total_estimated_cost', 'N/A')
                st.metric("Estimated Cost", total_cost)
            
            else:
                st.error("Analysis failed. Please try again.")
    
    # Results display
    if st.session_state.workflow_results and not st.session_state.analysis_in_progress:
        display_analysis_results(st.session_state.workflow_results)

def run_compliance_analysis(startup_description: str, progress_container):
    """Run the compliance analysis workflow with custom sources"""
    
    with progress_container:
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        agent_status = st.empty()
        
        # Agent status tracking (include custom source processing)
        agents = ["Custom Sources", "Intake Agent", "Scout Agent", "Matcher Agent", "Planner Agent", "Monitoring Agent"]
        agent_statuses = {agent: "pending" for agent in agents}
        
        # Check if we have custom sources
        custom_sources = st.session_state.get('custom_sources', [])
        if not custom_sources:
            agents = agents[1:]  # Skip custom sources step
        
        try:
            # Update progress function
            def update_progress(step: int, message: str, current_agent: str = None):
                progress = step / len(agents)
                progress_bar.progress(progress)
                status_text.text(message)
                
                if current_agent:
                    agent_statuses[current_agent] = "running"
                    if step > 1:  # Mark previous agent as completed
                        prev_agent = agents[step - 2]
                        agent_statuses[prev_agent] = "completed"
                
                # Update agent status display
                status_html = ""
                for agent in agents:
                    status = agent_statuses[agent]
                    if status == "completed":
                        status_html += f'<div class="agent-status agent-completed">✓ {agent}: Completed</div>'
                    elif status == "running":
                        status_html += f'<div class="agent-status agent-running">→ {agent}: Running...</div>'
                    else:
                        status_html += f'<div class="agent-status">○ {agent}: Pending</div>'
                
                agent_status.markdown(status_html, unsafe_allow_html=True)
            
            # Start analysis
            step = 0
            
            # Process custom sources if provided
            if custom_sources:
                update_progress(step, "Processing custom sources...", "Custom Sources")
                st.info(f"Processing {len(custom_sources)} custom source(s)")
                time.sleep(1)
                step += 1
            
            # Run the actual workflow
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Simulate progress updates during workflow execution
            update_progress(step, "Parsing startup information...", "Intake Agent")
            time.sleep(1)
            step += 1
            
            update_progress(step, "Researching regulations...", "Scout Agent")
            if custom_sources:
                status_text.text("Researching regulations + processing custom sources...")
            time.sleep(2)
            step += 1
            
            update_progress(step, "Analyzing compliance gaps...", "Matcher Agent")
            time.sleep(1)
            step += 1
            
            update_progress(step, "Creating action plan...", "Planner Agent")
            time.sleep(1)
            step += 1
            
            update_progress(step, "Setting up monitoring...", "Monitoring Agent")
            
            # Prepare the workflow with custom sources
            workflow_params = {
                "user_query": startup_description,
                "user_id": st.session_state.user_id
            }
            
            # Add custom sources to the workflow if available
            if custom_sources:
                workflow_params["custom_sources"] = custom_sources
            
            # Execute the enhanced workflow
            results = loop.run_until_complete(
                orchestrator.process_compliance_request(**workflow_params)
            )
            
            # Mark final agent as completed
            agent_statuses["Monitoring Agent"] = "completed"
            
            # Update final status
            progress_bar.progress(1.0)
            if custom_sources:
                status_text.text(f"Analysis completed! (Included {len(custom_sources)} custom sources)")
            else:
                status_text.text("Compliance analysis completed!")
            
            # Final agent status update
            status_html = ""
            for agent in agents:
                status_html += f'<div class="agent-status agent-completed">✓ {agent}: Completed</div>'
            agent_status.markdown(status_html, unsafe_allow_html=True)
            
            # Store results
            st.session_state.workflow_results = results
            st.session_state.analysis_in_progress = False
            
            # Auto-refresh to show results
            time.sleep(2)
            st.rerun()
            
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
            st.session_state.analysis_in_progress = False
            st.rerun()

def display_analysis_results(results: Dict[str, Any]):
    """Display the complete analysis results"""
    
    if results.get('status') != 'completed':
        st.error("Analysis failed or incomplete.")
        st.json(results)
        return
    
    # Auto-export on first display (only once per session)
    export_key = f"exported_{results.get('workflow_id', 'unknown')}"
    if export_key not in st.session_state:
        # Auto-export all formats and store in session state
        try:
            # Generate file data
            json_data = json.dumps(results, indent=2, default=str, ensure_ascii=False)
            
            # Generate summary data
            summary_data = generate_summary_text(results)
            
            # Generate CSV data
            csv_data = generate_csv_data(results)
            
            # Store in session state
            st.session_state[export_key] = {
                'json_data': json_data,
                'json_filename': f"compliance_analysis_{results.get('workflow_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                'summary_data': summary_data,
                'summary_filename': f"compliance_summary_{results.get('workflow_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                'csv_data': csv_data,
                'csv_filename': f"compliance_gaps_{results.get('workflow_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
            
            st.success("Files prepared for download!")
        except Exception as e:
            st.error(f"Error preparing files: {e}")
    
    # Download options
    st.subheader("Download Options")
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.write("Choose your preferred format:")
    
    with col2:
        if export_key in st.session_state:
            export_data = st.session_state[export_key]
            st.download_button(
                label="Download JSON",
                data=export_data['json_data'],
                file_name=export_data['json_filename'],
                mime="application/json"
            )
        else:
            st.error("No JSON data available")
    
    with col3:
        if export_key in st.session_state:
            export_data = st.session_state[export_key]
            st.download_button(
                label="Download Summary",
                data=export_data['summary_data'],
                file_name=export_data['summary_filename'],
                mime="text/plain"
            )
        else:
            st.error("No summary data available")
    
    with col4:
        if export_key in st.session_state:
            export_data = st.session_state[export_key]
            st.download_button(
                label="Download CSV",
                data=export_data['csv_data'],
                file_name=export_data['csv_filename'],
                mime="text/csv"
            )
        else:
            st.error("No CSV data available")
    
    st.divider()
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Overview", 
        "Compliance Gaps", 
        "Action Plan", 
        "Monitoring", 
        "Sources",
        "Raw Data"
    ])
    
    with tab1:
        display_overview_tab(results)
    
    with tab2:
        display_compliance_gaps_tab(results)
    
    with tab3:
        display_action_plan_tab(results)
    
    with tab4:
        display_monitoring_tab(results)
    
    with tab5:
        display_sources_tab(results)
    
    with tab6:
        display_raw_data_tab(results)

def display_overview_tab(results: Dict[str, Any]):
    """Display the overview tab"""
    st.subheader("Startup Information")
    
    startup_info = results.get('startup_info', {})
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Industry:** {startup_info.get('industry', 'N/A')}")
        st.write(f"**Target Countries:** {', '.join(startup_info.get('target_countries', []))}")
        st.write(f"**Business Activities:** {len(startup_info.get('business_activities', []))} identified")
    
    with col2:
        st.write(f"**Data Handling:** {', '.join(startup_info.get('data_handling', [])) or 'None specified'}")
        st.write(f"**Customer Types:** {', '.join(startup_info.get('customer_types', [])) or 'None specified'}")
    
    st.subheader("Analysis Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        gaps_found = results.get('compliance_analysis', {}).get('gaps_found', 0)
        st.metric("Compliance Gaps", gaps_found)
    
    with col2:
        docs_found = results.get('regulatory_research', {}).get('documents_found', 0)
        st.metric("Regulations Analyzed", docs_found)
    
    with col3:
        action_items = results.get('implementation_plan', {}).get('total_action_items', 0)
        st.metric("Action Items", action_items)
    
    with col4:
        risk_level = results.get('compliance_analysis', {}).get('overall_risk_level', 'unknown')
        risk_class = f"risk-{risk_level}"
        st.markdown(f'**Risk Level**<br><span class="{risk_class}">{risk_level.upper()}</span>', unsafe_allow_html=True)
    
    # Recommendations summary
    st.subheader("Key Recommendations")
    recommendations = results.get('compliance_analysis', {}).get('recommendations_summary', '')
    if recommendations:
        st.markdown(recommendations)
    else:
        st.info("No specific recommendations available.")

def display_compliance_gaps_tab(results: Dict[str, Any]):
    """Display compliance gaps tab"""
    st.subheader("Identified Compliance Gaps")
    
    compliance_gaps = results.get('compliance_analysis', {}).get('compliance_gaps', [])
    
    # Show if custom sources were used
    if hasattr(st.session_state, 'custom_sources') and st.session_state.custom_sources:
        st.info(f"Analysis included {len(st.session_state.custom_sources)} user-provided custom source(s)")
        
        with st.expander("Custom Sources Used", expanded=False):
            for i, source in enumerate(st.session_state.custom_sources):
                st.write(f"**{i+1}. {source.get('source_name', 'Unnamed')}** ({source.get('source_type', 'unknown')})")
                if source.get('user_description'):
                    st.caption(f"Description: {source['user_description']}")
    
    if not compliance_gaps:
        st.success("No major compliance gaps identified!")
        return
    
    # Group gaps by severity
    gaps_by_severity = {
        'critical': [gap for gap in compliance_gaps if gap.get('severity') == 'critical'],
        'high': [gap for gap in compliance_gaps if gap.get('severity') == 'high'],
        'medium': [gap for gap in compliance_gaps if gap.get('severity') == 'medium'],
        'low': [gap for gap in compliance_gaps if gap.get('severity') == 'low']
    }
    
    for severity, gaps in gaps_by_severity.items():
        if gaps:
            # Create severity badge with color
            severity_colors = {
                'critical': 'red',
                'high': 'orange', 
                'medium': 'yellow',
                'low': 'green'
            }
            color = severity_colors.get(severity, 'gray')
            
            st.markdown(f"""
            <div style="background-color: {color}; color: white; padding: 8px 16px; border-radius: 4px; display: inline-block; margin-bottom: 16px;">
                <strong>{severity.upper()} Priority ({len(gaps)} gaps)</strong>
            </div>
            """, unsafe_allow_html=True)
            
            for gap in gaps:
                with st.expander(f"{gap.get('title', 'Compliance Gap')}", expanded=(severity in ['critical', 'high'])):
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Gap Type:** {gap.get('gap_type', 'N/A').replace('_', ' ').title()}")
                        st.write(f"**Description:** {gap.get('description', 'No description available')}")
                        st.write(f"**Country:** {gap.get('country', 'N/A')}")
                    
                    with col2:
                        if gap.get('deadline'):
                            st.write(f"**Deadline:** {gap.get('deadline')}")
                        if gap.get('estimated_cost'):
                            st.write(f"**Estimated Cost:** {gap.get('estimated_cost')}")
                        
                        # Source information
                        if gap.get('regulation_id'):
                            st.write(f"**Regulation:** {gap.get('regulation_id')}")
                        if gap.get('authority'):
                            st.write(f"**Authority:** {gap.get('authority')}")
                        if gap.get('source_url'):
                            st.markdown(f"**Source:** [View Regulation]({gap.get('source_url')})")
                    
                    # Recommended actions
                    st.write("**Recommended Actions:**")
                    actions = gap.get('recommended_actions', [])
                    for action in actions:
                        st.write(f"• {action}")
                    
                    # Enhanced Source Information Section
                    st.write("---")
                    st.write("**Regulatory Sources:**")
                    
                    # Primary sources
                    primary_sources = gap.get('primary_sources', [])
                    supporting_sources = gap.get('supporting_sources', [])
                    
                    if primary_sources:
                        st.write("**Primary Sources (Official Regulations):**")
                        for i, source in enumerate(primary_sources, 1):
                            if isinstance(source, dict):
                                # Handle dict format
                                source_url = source.get('url') or source.get('source_url')
                                source_title = source.get('title') or source.get('citation_format', 'Unknown Source')
                                source_authority = source.get('authority', 'Unknown Authority')
                                
                                if source_url:
                                    st.markdown(f"{i}. **{source_title}** ({source_authority}) - [View Source]({source_url})")
                                else:
                                    st.write(f"{i}. **{source_title}** ({source_authority}) - No direct link available")
                            else:
                                # Handle string format
                                st.write(f"{i}. {source}")
                    
                    # Supporting sources
                    if supporting_sources:
                        st.write("**Supporting Sources:**")
                        for i, source in enumerate(supporting_sources, 1):
                            if isinstance(source, dict):
                                source_url = source.get('url') or source.get('source_url')
                                source_title = source.get('title') or source.get('citation_format', 'Unknown Source')
                                source_authority = source.get('authority', 'Unknown Authority')
                                
                                if source_url:
                                    st.markdown(f"{i}. **{source_title}** ({source_authority}) - [View Source]({source_url})")
                                else:
                                    st.write(f"{i}. **{source_title}** ({source_authority}) - No direct link available")
                            else:
                                st.write(f"{i}. {source}")
                    
                    # Legacy source information (for backward compatibility)
                    if not primary_sources and not supporting_sources:
                        st.write("**Source Information:**")
                        if gap.get('source_url') or gap.get('regulation_id'):
                            st.write(f"• **Regulation ID:** {gap.get('regulation_id')}")
                        if gap.get('authority'):
                            st.write(f"• **Authority:** {gap.get('authority')}")
                        if gap.get('source_url'):
                            st.markdown(f"• **Source:** [View Regulation]({gap.get('source_url')})")
                        
                        # Try to find related sources from regulatory research
                        regulatory_research = results.get('regulatory_research', {})
                        documents = regulatory_research.get('documents', [])
                        
                        if documents:
                            st.write("**Related Regulatory Documents:**")
                            for i, doc in enumerate(documents[:3], 1):  # Show top 3
                                doc_url = doc.get('url') or doc.get('source_url')
                                doc_title = doc.get('title', 'Unknown Document')
                                doc_authority = doc.get('authority', 'Unknown Authority')
                                
                                if doc_url:
                                    st.markdown(f"{i}. **{doc_title}** ({doc_authority}) - [View Document]({doc_url})")
                                else:
                                    st.write(f"{i}. **{doc_title}** ({doc_authority})")
                    
                    # Source quality indicator
                    if primary_sources or supporting_sources:
                        total_sources = len(primary_sources) + len(supporting_sources)
                        primary_count = len(primary_sources)
                        
                        if primary_count > 0:
                            st.success(f"**Source Quality:** {primary_count} primary + {len(supporting_sources)} supporting sources")
                        elif supporting_sources:
                            st.warning(f"**Source Quality:** {len(supporting_sources)} supporting sources only (no primary sources)")
                        else:
                            st.error("**Source Quality:** No sources found - manual verification required")
                    else:
                        st.info("**Source Quality:** Source information not available")

def display_action_plan_tab(results: Dict[str, Any]):
    """Display action plan tab"""
    st.subheader("Implementation Action Plan")
    
    implementation_plan = results.get('implementation_plan', {})
    
    if not implementation_plan:
        st.warning("No implementation plan available.")
        return
    
    # Plan overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Action Items", implementation_plan.get('total_action_items', 0))
    
    with col2:
        st.metric("Estimated Cost", implementation_plan.get('total_estimated_cost', 'N/A'))
    
    with col3:
        st.write(f"**Next Review:** {implementation_plan.get('next_review_date', 'N/A')}")
    
    # Timeline
    st.subheader("Implementation Timeline")
    timeline = implementation_plan.get('implementation_timeline', '')
    if timeline:
        st.info(timeline)
    
    # Action items
    st.subheader("Action Items")
    
    action_items = implementation_plan.get('action_items', [])
    
    # Group by priority
    items_by_priority = {
        'critical': [item for item in action_items if item.get('priority') == 'critical'],
        'high': [item for item in action_items if item.get('priority') == 'high'],
        'medium': [item for item in action_items if item.get('priority') == 'medium'],
        'low': [item for item in action_items if item.get('priority') == 'low']
    }
    
    for priority, items in items_by_priority.items():
        if items:
            # Create priority badge with color
            priority_colors = {
                'critical': 'red',
                'high': 'orange',
                'medium': 'yellow',
                'low': 'green'
            }
            color = priority_colors.get(priority, 'gray')
            
            st.markdown(f"""
            <div style="background-color: {color}; color: white; padding: 8px 16px; border-radius: 4px; display: inline-block; margin-bottom: 16px;">
                <strong>{priority.upper()} Priority ({len(items)} items)</strong>
            </div>
            """, unsafe_allow_html=True)
            
            for item in items:
                with st.expander(f"{item.get('title', 'Action Item')}", expanded=(priority == 'critical')):
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Description:** {item.get('description', 'No description')}")
                        st.write(f"**Category:** {item.get('category', 'N/A').replace('_', ' ').title()}")
                    
                    with col2:
                        st.write(f"**Effort:** {item.get('estimated_effort', 'N/A')}")
                        if item.get('estimated_cost'):
                            st.write(f"**Cost:** {item.get('estimated_cost')}")
                        if item.get('deadline'):
                            st.write(f"**Deadline:** {item.get('deadline')}")
                    
                    # Resources needed
                    resources = item.get('resources_needed', [])
                    if resources:
                        st.write("**Resources Needed:**")
                        for resource in resources:
                            st.write(f"• {resource}")
                    
                    # Dependencies
                    dependencies = item.get('dependencies', [])
                    if dependencies:
                        st.write("**Dependencies:**")
                        for dep in dependencies:
                            st.write(f"• {dep}")

def display_monitoring_tab(results: Dict[str, Any]):
    """Display monitoring tab"""
    st.subheader("Ongoing Regulatory Monitoring")
    
    st.info("Monitoring has been set up for your startup. You'll receive alerts about new regulatory changes that may affect your business.")
    
    startup_info = results.get('startup_info', {})
    
    st.write("**Monitoring Configuration:**")
    st.write(f"• **Industry Focus:** {startup_info.get('industry', 'N/A')}")
    st.write(f"• **Countries Monitored:** {', '.join(startup_info.get('target_countries', []))}")
    st.write(f"• **Monitoring Frequency:** Weekly")
    st.write(f"• **Alert Delivery:** System notifications")
    
    # Monitoring controls (for future enhancement)
    st.subheader("Monitoring Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Pause Monitoring"):
            st.info("Monitoring paused (simulated)")
    
    with col2:
        if st.button("Check for Updates Now"):
            st.info("Manual check initiated (simulated)")
    
    with col3:
        if st.button("Update Settings"):
            st.info("Settings updated (simulated)")

def display_sources_tab(results: Dict[str, Any]):
    """Display the sources tab"""
    st.subheader("Regulatory Sources")
    
    # Collect all sources from different parts of the analysis
    all_sources = []
    
    # 1. Sources from regulatory research
    regulatory_research = results.get('regulatory_research', {})
    if regulatory_research:
        all_sources.extend(regulatory_research.get('documents', []))
        all_sources.extend(regulatory_research.get('regulations', []))
    
    # 2. Sources from compliance gaps
    compliance_gaps = results.get('compliance_analysis', {}).get('compliance_gaps', [])
    for gap in compliance_gaps:
        # Primary sources
        primary_sources = gap.get('primary_sources', [])
        for source in primary_sources:
            if isinstance(source, dict):
                source['source_type'] = 'primary'
                source['gap_title'] = gap.get('title', 'Unknown Gap')
                all_sources.append(source)
        
        # Supporting sources
        supporting_sources = gap.get('supporting_sources', [])
        for source in supporting_sources:
            if isinstance(source, dict):
                source['source_type'] = 'supporting'
                source['gap_title'] = gap.get('title', 'Unknown Gap')
                all_sources.append(source)
        
        # Legacy source information
        if gap.get('source_url') or gap.get('regulation_id'):
            legacy_source = {
                'title': gap.get('regulation_id', 'Unknown Regulation'),
                'authority': gap.get('authority', 'Unknown Authority'),
                'url': gap.get('source_url'),
                'source_type': 'legacy',
                'gap_title': gap.get('title', 'Unknown Gap')
            }
            all_sources.append(legacy_source)
    
    if not all_sources:
        st.info("No specific regulatory sources were identified in this analysis.")
        return
    
    # Remove duplicates based on URL and title
    unique_sources = []
    seen_urls = set()
    seen_titles = set()
    
    for source in all_sources:
        source_url = source.get('url') or source.get('source_url', '')
        source_title = source.get('title', '')
        
        # Create unique identifier
        identifier = f"{source_url}_{source_title}"
        
        if identifier not in seen_urls and source_title not in seen_titles:
            unique_sources.append(source)
            seen_urls.add(identifier)
            seen_titles.add(source_title)
    
    # Group sources by type
    primary_sources = [s for s in unique_sources if s.get('source_type') == 'primary']
    supporting_sources = [s for s in unique_sources if s.get('source_type') == 'supporting']
    legacy_sources = [s for s in unique_sources if s.get('source_type') == 'legacy']
    other_sources = [s for s in unique_sources if s.get('source_type') not in ['primary', 'supporting', 'legacy']]
    
    # Display sources by quality
    if primary_sources:
        st.subheader("Primary Sources (Official Regulations)")
        st.info("These are official government and regulatory sources with the highest reliability.")
        
        for i, source in enumerate(primary_sources, 1):
            with st.expander(f"{i}. {source.get('title', 'Unknown Source')}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Authority:** {source.get('authority', 'Unknown Authority')}")
                    if source.get('gap_title'):
                        st.write(f"**Related Gap:** {source.get('gap_title')}")
                    if source.get('description'):
                        st.write(f"**Description:** {source.get('description')}")
                
                with col2:
                    source_url = source.get('url') or source.get('source_url')
                    if source_url:
                        st.markdown(f"[View Source]({source_url})")
                    else:
                        st.write("No direct link available")
        
        st.write("---")
    
    if supporting_sources:
        st.subheader("Supporting Sources")
        st.info("These are additional sources that provide context and interpretation.")
        
        for i, source in enumerate(supporting_sources, 1):
            with st.expander(f"{i}. {source.get('title', 'Unknown Source')}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Authority:** {source.get('authority', 'Unknown Authority')}")
                    if source.get('gap_title'):
                        st.write(f"**Related Gap:** {source.get('gap_title')}")
                    if source.get('description'):
                        st.write(f"**Description:** {source.get('description')}")
                
                with col2:
                    source_url = source.get('url') or source.get('source_url')
                    if source_url:
                        st.markdown(f"[View Source]({source_url})")
                    else:
                        st.write("No direct link available")
        
        st.write("---")
    
    if legacy_sources:
        st.subheader("Legacy Source Information")
        st.info("Basic source information from earlier analysis versions.")
        
        for i, source in enumerate(legacy_sources, 1):
            with st.expander(f"{i}. {source.get('title', 'Unknown Source')}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Authority:** {source.get('authority', 'Unknown Authority')}")
                    if source.get('gap_title'):
                        st.write(f"**Related Gap:** {source.get('gap_title')}")
                
                with col2:
                    source_url = source.get('url') or source.get('source_url')
                    if source_url:
                        st.markdown(f"[View Source]({source_url})")
                    else:
                        st.write("No direct link available")
        
        st.write("---")
    
    if other_sources:
        st.subheader("Other Sources")
        
        for i, source in enumerate(other_sources, 1):
            with st.expander(f"{i}. {source.get('title', 'Unknown Source')}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Authority:** {source.get('authority', 'Unknown Authority')}")
                    if source.get('description'):
                        st.write(f"**Description:** {source.get('description')}")
                
                with col2:
                    source_url = source.get('url') or source.get('source_url')
                    if source_url:
                        st.markdown(f"[View Source]({source_url})")
                    else:
                        st.write("No direct link available")
    
    # Summary statistics
    st.subheader("Source Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sources", len(unique_sources))
    
    with col2:
        st.metric("Primary Sources", len(primary_sources))
    
    with col3:
        st.metric("Supporting Sources", len(supporting_sources))
    
    with col4:
        sources_with_links = len([s for s in unique_sources if s.get('url') or s.get('source_url')])
        st.metric("With Direct Links", sources_with_links)

def display_raw_data_tab(results: Dict[str, Any]):
    """Display raw data tab"""
    st.subheader("Complete Analysis Data")
    
    st.info("This tab shows the complete raw data from the analysis. Use this for detailed review or debugging.")
    
    # JSON display with syntax highlighting
    st.json(results)

def generate_summary_text(results: Dict[str, Any]) -> str:
    """Generate summary text for download"""
    workflow_id = results.get('workflow_id', 'unknown')
    startup_info = results.get('startup_info', {})
    compliance_analysis = results.get('compliance_analysis', {})
    implementation_plan = results.get('implementation_plan', {})
    
    summary = f"""
COMPLIANCE ANALYSIS SUMMARY
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Workflow ID: {workflow_id}

STARTUP INFORMATION
Company: {startup_info.get('company_name', 'N/A')}
Industry: {startup_info.get('industry', 'N/A')}
Target Countries: {', '.join(startup_info.get('target_countries', []))}
Business Activities: {len(startup_info.get('business_activities', []))} identified
Data Handling: {', '.join(startup_info.get('data_handling', [])) or 'None specified'}

ANALYSIS RESULTS
Risk Level: {compliance_analysis.get('overall_risk_level', 'N/A').upper()}
Compliance Gaps Found: {compliance_analysis.get('gaps_found', 0)}
Compliant Areas: {compliance_analysis.get('compliant_areas', 0)}
Action Items Generated: {implementation_plan.get('total_action_items', 0)}
Estimated Total Cost: {implementation_plan.get('total_estimated_cost', 'N/A')}

KEY RECOMMENDATIONS
{compliance_analysis.get('recommendations_summary', 'No recommendations available')}

SOURCE QUALITY ASSESSMENT"""
    
    # Get compliance gaps data first
    gaps = compliance_analysis.get('compliance_gaps', [])
    
    # Calculate source statistics
    gaps_with_sources = sum(1 for gap in gaps if gap.get('primary_sources') or gap.get('supporting_sources'))
    gaps_without_sources = len(gaps) - gaps_with_sources
    source_percentage = (gaps_with_sources/len(gaps)*100) if gaps else 0
    
    summary += f"\nGaps with Sources: {gaps_with_sources}/{len(gaps)} ({source_percentage:.0f}%)"
    summary += f"\nGaps without Sources: {gaps_without_sources}"
    
    if gaps_without_sources > 0:
        summary += f"\nWARNING: Some compliance gaps lack regulatory source backing - Professional legal review strongly recommended"
    else:
        summary += f"\nAll gaps have some source backing"
    
    summary += f"""

COMPLIANCE GAPS SUMMARY
"""
    for i, gap in enumerate(gaps[:10], 1):  # Limit to top 10
        summary += f"\n{i}. {gap.get('title', 'Unknown Gap')} [{gap.get('severity', 'unknown').upper()}]"
        summary += f"\n   Country: {gap.get('country', 'N/A')}"
        summary += f"\n   Type: {gap.get('gap_type', 'N/A').replace('_', ' ').title()}"
        summary += f"\n   Actions: {len(gap.get('recommended_actions', []))} recommended"
        
        # Add source quality indicator
        primary_sources = gap.get('primary_sources', [])
        supporting_sources = gap.get('supporting_sources', [])
        
        if primary_sources:
            summary += f"\n   Sources: {len(primary_sources)} primary, {len(supporting_sources)} supporting"
        elif supporting_sources:
            summary += f"\n   Sources: {len(supporting_sources)} supporting only (no primary sources)"
        else:
            summary += f"\n   Sources: None found - requires manual verification"
        
        summary += "\n"
    
    if len(gaps) > 10:
        summary += f"\n... and {len(gaps) - 10} more gaps (see JSON export for complete list)"
    
    summary += f"""

IMPLEMENTATION TIMELINE
{implementation_plan.get('implementation_timeline', 'No timeline available')}

MONITORING
Monitoring has been set up for ongoing regulatory updates.
Next Review Date: {implementation_plan.get('next_review_date', 'N/A')}

SOURCE RELIABILITY DISCLAIMER
This analysis combines AI-powered research with available regulatory sources.
Source quality varies - gaps marked with no sources require additional verification.
For legal compliance purposes, always consult with qualified legal counsel
and verify requirements against official regulatory publications.

---
Generated by ComplianceNavigator
For complete technical details and sources, see the JSON export file.
"""
    
    return summary.strip()

def generate_csv_data(results: Dict[str, Any]) -> str:
    """Generate CSV data for download"""
    import io
    import csv
    
    compliance_analysis = results.get('compliance_analysis', {})
    gaps = compliance_analysis.get('compliance_gaps', [])
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Gap Title', 'Severity', 'Country', 'Gap Type', 'Business Activity',
        'Description', 'Recommended Actions', 'Deadline', 'Estimated Cost'
    ])
    
    # Data rows
    for gap in gaps:
        writer.writerow([
            gap.get('title', ''),
            gap.get('severity', ''),
            gap.get('country', ''),
            gap.get('gap_type', '').replace('_', ' ').title(),
            gap.get('business_activity', ''),
            gap.get('description', '')[:200] + ('...' if len(gap.get('description', '')) > 200 else ''),
            '; '.join(gap.get('recommended_actions', [])),
            gap.get('deadline', ''),
            gap.get('estimated_cost', '')
        ])
    
    return output.getvalue()

if __name__ == "__main__":
    main() 








    