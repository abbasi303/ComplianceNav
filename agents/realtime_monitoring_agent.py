"""
Real-Time Monitoring Agent
Continuously monitors regulatory changes and updates using cutting-edge techniques
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from loguru import logger
import hashlib
import time
from urllib.parse import urlparse
import re

from integrations.gemini_client import gemini_client
from agents.scout_agent import RegulatoryDocument


@dataclass
class MonitoringResult:
    """Result from real-time monitoring"""
    url: str
    last_check: datetime
    has_changes: bool
    change_type: str
    change_summary: str
    new_content_hash: str
    previous_content_hash: str
    monitoring_confidence: float


class RealtimeMonitoringAgent:
    """
    Real-time regulatory monitoring using cutting-edge techniques:
    - Continuous content monitoring
    - Change detection algorithms
    - AI-powered change analysis
    - Alert generation
    - Trend analysis
    """
    
    def __init__(self):
        self.agent_name = "RealtimeMonitoringAgent"
        self.session_pool = None
        self.monitoring_cache = {}
        self.change_history = {}
        self.alert_thresholds = self._load_alert_thresholds()
        
        # Monitoring settings
        self.check_interval = 3600  # 1 hour
        self.max_concurrent_checks = 10
        self.timeout = 30
        self.content_similarity_threshold = 0.85
        
        logger.info(f"{self.agent_name} initialized with real-time monitoring capabilities")
    
    def _load_alert_thresholds(self) -> Dict[str, float]:
        """Load alert thresholds for different types of changes"""
        return {
            "critical": 0.9,      # Major regulatory changes
            "high": 0.7,          # Significant updates
            "medium": 0.5,        # Minor changes
            "low": 0.3            # Cosmetic changes
        }
    
    async def start_monitoring(
        self, 
        regulatory_urls: List[str], 
        startup_info: Any
    ) -> List[MonitoringResult]:
        """
        Start real-time monitoring of regulatory URLs
        """
        logger.info(f"{self.agent_name}: Starting monitoring for {len(regulatory_urls)} URLs")
        
        # Initialize session pool
        self.session_pool = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'User-Agent': 'ComplianceNavigator-Monitor/1.0'}
        )
        
        try:
            # Step 1: Initial baseline check
            baseline_results = await self._establish_baseline(regulatory_urls)
            
            # Step 2: Continuous monitoring
            monitoring_results = await self._continuous_monitoring(baseline_results, startup_info)
            
            # Step 3: Change analysis and alerting
            analyzed_results = await self._analyze_changes(monitoring_results, startup_info)
            
            logger.info(f"{self.agent_name}: Monitoring completed with {len(analyzed_results)} results")
            return analyzed_results
            
        finally:
            if self.session_pool:
                await self.session_pool.close()
    
    async def _establish_baseline(self, urls: List[str]) -> List[MonitoringResult]:
        """Establish baseline content for monitoring"""
        
        baseline_results = []
        
        # Process URLs in parallel
        tasks = []
        for url in urls:
            task = self._check_single_url(url, is_baseline=True)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, MonitoringResult):
                baseline_results.append(result)
                # Store baseline hash
                cache_key = hashlib.md5(urls[i].encode()).hexdigest()
                self.monitoring_cache[cache_key] = {
                    'baseline_hash': result.new_content_hash,
                    'last_check': result.last_check,
                    'content': result.change_summary
                }
            else:
                logger.error(f"Baseline check failed for {urls[i]}: {result}")
        
        return baseline_results
    
    async def _continuous_monitoring(
        self, 
        baseline_results: List[MonitoringResult], 
        startup_info: Any
    ) -> List[MonitoringResult]:
        """Perform continuous monitoring with change detection"""
        
        monitoring_results = []
        
        # Monitor each URL for changes
        for baseline in baseline_results:
            try:
                # Check for changes
                current_result = await self._check_single_url(baseline.url, is_baseline=False)
                
                # Compare with baseline
                cache_key = hashlib.md5(baseline.url.encode()).hexdigest()
                baseline_data = self.monitoring_cache.get(cache_key, {})
                
                if baseline_data:
                    baseline_hash = baseline_data.get('baseline_hash', '')
                    current_result.previous_content_hash = baseline_hash
                    current_result.has_changes = current_result.new_content_hash != baseline_hash
                    
                    if current_result.has_changes:
                        # Analyze the nature of changes
                        change_analysis = await self._analyze_content_changes(
                            baseline_data.get('content', ''),
                            current_result.change_summary,
                            startup_info
                        )
                        current_result.change_type = change_analysis['change_type']
                        current_result.monitoring_confidence = change_analysis['confidence']
                
                monitoring_results.append(current_result)
                
                # Update cache
                self.monitoring_cache[cache_key] = {
                    'baseline_hash': current_result.new_content_hash,
                    'last_check': current_result.last_check,
                    'content': current_result.change_summary
                }
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Monitoring failed for {baseline.url}: {e}")
        
        return monitoring_results
    
    async def _check_single_url(self, url: str) -> MonitoringResult:
        """Check a single URL for changes"""
        
        try:
            # Create a new session to avoid loop issues
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Calculate content hash
                        content_hash = hashlib.md5(content.encode()).hexdigest()
                        
                        # Check for changes
                        if url in self.change_history:
                            previous_hash = self.change_history[url]['hash']
                            has_changed = content_hash != previous_hash
                        else:
                            has_changed = False
                        
                        # Update history
                        self.change_history[url] = {
                            'hash': content_hash,
                            'last_check': time.time(),
                            'content_length': len(content)
                        }
                        
                        return MonitoringResult(
                            url=url,
                            status="success",
                            has_changed=has_changed,
                            content_hash=content_hash,
                            last_check=time.time(),
                            error=None
                        )
                    else:
                        return MonitoringResult(
                            url=url,
                            status="error",
                            has_changed=False,
                            content_hash=None,
                            last_check=time.time(),
                            error=f"HTTP {response.status}"
                        )
                        
        except Exception as e:
            return MonitoringResult(
                url=url,
                status="error",
                has_changed=False,
                content_hash=None,
                last_check=time.time(),
                error=str(e)
            )
    
    def _extract_main_content(self, soup) -> str:
        """Extract main content from webpage"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find main content areas
        main_selectors = [
            'main', 'article', '.content', '.main-content', 
            '#content', '#main', '.body', '.text'
        ]
        
        for selector in main_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        # Fallback to body text
        return soup.get_text().strip()
    
    async def _analyze_content_changes(
        self, 
        old_content: str, 
        new_content: str, 
        startup_info: Any
    ) -> Dict:
        """Analyze content changes using AI"""
        
        try:
            prompt = f"""
            Analyze the changes between two versions of regulatory content:
            
            OLD CONTENT:
            {old_content[:2000]}...
            
            NEW CONTENT:
            {new_content[:2000]}...
            
            Industry: {startup_info.industry}
            Business Activities: {', '.join(startup_info.business_activities)}
            
            Determine:
            1. Change type: "critical", "high", "medium", "low", or "none"
            2. Confidence level (0-1)
            3. Impact on compliance requirements
            
            Return JSON:
            {{
                "change_type": "critical|high|medium|low|none",
                "confidence": 0.0-1.0,
                "impact_summary": "Brief description of impact",
                "compliance_affected": true/false
            }}
            """
            
            response = await gemini_client.generate_response(prompt, temperature=0.2)
            
            # Parse AI response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis
            
        except Exception as e:
            logger.error(f"AI change analysis failed: {e}")
        
        # Fallback analysis
        return {
            "change_type": "medium",
            "confidence": 0.5,
            "impact_summary": "Content change detected",
            "compliance_affected": False
        }
    
    async def _analyze_changes(
        self, 
        monitoring_results: List[MonitoringResult], 
        startup_info: Any
    ) -> List[MonitoringResult]:
        """Analyze monitoring results and generate alerts"""
        
        analyzed_results = []
        
        for result in monitoring_results:
            if result.has_changes:
                # Determine alert level
                alert_level = self._determine_alert_level(result)
                
                # Generate alert if threshold is met
                if alert_level in ["critical", "high"]:
                    await self._generate_alert(result, alert_level, startup_info)
                
                # Update change history
                self._update_change_history(result)
            
            analyzed_results.append(result)
        
        return analyzed_results
    
    def _determine_alert_level(self, result: MonitoringResult) -> str:
        """Determine alert level based on change type and confidence"""
        
        change_type = result.change_type
        confidence = result.monitoring_confidence
        
        # Check thresholds
        for level, threshold in self.alert_thresholds.items():
            if confidence >= threshold:
                return level
        
        return "low"
    
    async def _generate_alert(self, result: MonitoringResult, level: str, startup_info: Any):
        """Generate alert for significant changes"""
        
        alert_message = f"""
        🚨 REGULATORY ALERT - {level.upper()} PRIORITY
        
        URL: {result.url}
        Change Type: {result.change_type}
        Confidence: {result.monitoring_confidence:.2f}
        Detected: {result.last_check.strftime('%Y-%m-%d %H:%M:%S')}
        
        Impact: This change may affect compliance requirements for {startup_info.industry} businesses.
        
        Action Required: Review the updated regulatory content and assess impact on your compliance strategy.
        """
        
        logger.warning(alert_message)
        
        # Store alert for UI display
        if not hasattr(self, 'alerts'):
            self.alerts = []
        
        self.alerts.append({
            'timestamp': result.last_check,
            'level': level,
            'url': result.url,
            'message': alert_message,
            'change_type': result.change_type
        })
    
    def _update_change_history(self, result: MonitoringResult):
        """Update change history for trend analysis"""
        
        url = result.url
        if url not in self.change_history:
            self.change_history[url] = []
        
        self.change_history[url].append({
            'timestamp': result.last_check,
            'change_type': result.change_type,
            'confidence': result.monitoring_confidence
        })
        
        # Keep only last 10 changes
        self.change_history[url] = self.change_history[url][-10:]
    
    async def get_monitoring_summary(self) -> Dict:
        """Get summary of monitoring activities"""
        
        total_urls = len(self.monitoring_cache)
        changed_urls = sum(1 for result in self.change_history.values() if result)
        
        # Calculate change frequency
        change_frequency = {}
        for url, changes in self.change_history.items():
            if changes:
                days_since_first = (datetime.now() - changes[0]['timestamp']).days
                if days_since_first > 0:
                    change_frequency[url] = len(changes) / days_since_first
        
        return {
            'total_urls_monitored': total_urls,
            'urls_with_changes': changed_urls,
            'change_frequency': change_frequency,
            'recent_alerts': getattr(self, 'alerts', [])[-5:],  # Last 5 alerts
            'last_check': datetime.now()
        }


# Global instance
realtime_monitoring_agent = RealtimeMonitoringAgent() 