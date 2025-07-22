"""
Monitoring & Alerting Agent
Periodically monitors regulatory updates and alerts users to new compliance requirements
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from loguru import logger
from integrations.gemini_client import gemini_client
from core.vector_store import vector_store
from datetime import datetime, timedelta
import asyncio
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class RegulatoryUpdate(BaseModel):
    """Represents a new regulatory update"""
    update_id: str
    title: str
    description: str
    country: str
    regulation_type: str
    effective_date: Optional[str] = None
    impact_level: str  # 'high', 'medium', 'low'
    affected_industries: List[str]
    source_url: Optional[str] = None
    discovered_date: str

class MonitoringAlert(BaseModel):
    """Alert for regulatory changes affecting a startup"""
    alert_id: str
    startup_industry: str
    target_countries: List[str]
    regulatory_update: RegulatoryUpdate
    relevance_score: float
    recommended_actions: List[str]
    alert_created: str

class MonitoringAgent:
    """Agent for monitoring regulatory changes and alerting users"""
    
    def __init__(self):
        """Initialize the Monitoring Agent"""
        self.agent_name = "MonitoringAgent"
        self.scheduler = AsyncIOScheduler()
        self.active_monitors = {}  # startup_id -> monitoring config
        logger.info(f"{self.agent_name} initialized")
    
    def setup_monitoring(
        self, 
        startup_id: str, 
        startup_info: Any,
        monitoring_frequency: str = "weekly"
    ):
        """
        Set up regulatory monitoring for a startup
        
        Args:
            startup_id: Unique identifier for the startup
            startup_info: Startup information object
            monitoring_frequency: 'daily', 'weekly', or 'monthly'
        """
        logger.info(f"{self.agent_name}: Setting up monitoring for {startup_id}")
        
        # Store monitoring configuration
        self.active_monitors[startup_id] = {
            'startup_info': startup_info,
            'frequency': monitoring_frequency,
            'last_check': datetime.now().isoformat(),
            'alerts_sent': []
        }
        
        # Schedule monitoring job
        if monitoring_frequency == "daily":
            trigger = "interval"
            hours = 24
        elif monitoring_frequency == "weekly":
            trigger = "interval" 
            hours = 168  # 7 days
        else:  # monthly
            trigger = "interval"
            hours = 720  # 30 days
        
        self.scheduler.add_job(
            self._check_regulatory_updates,
            trigger=trigger,
            hours=hours,
            args=[startup_id],
            id=f"monitor_{startup_id}",
            replace_existing=True
        )
        
        logger.info(f"Monitoring scheduled for {startup_id} with {monitoring_frequency} frequency")
    
    async def _check_regulatory_updates(self, startup_id: str):
        """Check for new regulatory updates for a specific startup"""
        if startup_id not in self.active_monitors:
            logger.warning(f"No monitoring config found for {startup_id}")
            return
        
        config = self.active_monitors[startup_id]
        startup_info = config['startup_info']
        
        logger.info(f"{self.agent_name}: Checking regulatory updates for {startup_id}")
        
        try:
            # Search for new regulatory updates
            updates = await self._discover_regulatory_updates(startup_info)
            
            # Filter and score updates for relevance
            relevant_updates = self._filter_relevant_updates(updates, startup_info)
            
            # Generate alerts for high-relevance updates
            alerts = []
            for update in relevant_updates:
                if update.impact_level in ['high', 'medium']:
                    alert = await self._create_monitoring_alert(startup_info, update)
                    alerts.append(alert)
            
            # Send alerts if any found
            if alerts:
                await self._send_alerts(startup_id, alerts)
                config['alerts_sent'].extend([alert.alert_id for alert in alerts])
            
            # Update last check time
            config['last_check'] = datetime.now().isoformat()
            
            logger.info(f"Monitoring check complete for {startup_id}: {len(alerts)} alerts generated")
            
        except Exception as e:
            logger.error(f"Error during regulatory monitoring for {startup_id}: {e}")
    
    async def _discover_regulatory_updates(self, startup_info: Any) -> List[RegulatoryUpdate]:
        """Discover new regulatory updates relevant to the startup"""
        updates = []
        
        # Generate search queries for regulatory updates
        update_queries = self._generate_update_search_queries(startup_info)
        
        # Search for updates using multiple approaches
        for query in update_queries:
            # Search vector store for recent regulatory changes
            vector_results = vector_store.search_regulations(
                query=f"{query} new regulation update 2024",
                n_results=3,
                country_filter=startup_info.target_countries[0] if startup_info.target_countries else None
            )
            
            # Convert vector results to regulatory updates
            for result in vector_results:
                update = await self._create_regulatory_update_from_result(result, startup_info)
                if update:
                    updates.append(update)
            
            # For MVP: Generate synthetic regulatory updates
            synthetic_updates = await self._generate_synthetic_updates(query, startup_info)
            updates.extend(synthetic_updates)
        
        return updates
    
    def _generate_update_search_queries(self, startup_info: Any) -> List[str]:
        """Generate search queries for regulatory updates"""
        queries = []
        
        # Industry-specific queries
        queries.append(f"{startup_info.industry} regulatory changes")
        queries.append(f"{startup_info.industry} compliance updates")
        
        # Country-specific queries
        for country in startup_info.target_countries:
            queries.append(f"{country} business regulation updates")
            queries.append(f"{country} {startup_info.industry} law changes")
        
        # Data protection updates (if applicable)
        if startup_info.data_handling:
            queries.extend([
                "GDPR updates privacy law changes",
                "data protection regulation updates"
            ])
        
        return queries[:6]  # Limit to 6 queries
    
    async def _create_regulatory_update_from_result(
        self, 
        result: Dict[str, Any], 
        startup_info: Any
    ) -> Optional[RegulatoryUpdate]:
        """Create a regulatory update from vector search result"""
        try:
            metadata = result.get('metadata', {})
            content = result.get('content', '')
            
            # Check if this is actually a recent update
            if 'last_updated' in metadata:
                # For MVP, assume all results are recent updates
                update = RegulatoryUpdate(
                    update_id=f"update_{hash(content[:100]) % 10000}",
                    title=metadata.get('title', 'Regulatory Update'),
                    description=content[:200] + "..." if len(content) > 200 else content,
                    country=metadata.get('country', 'Unknown'),
                    regulation_type=metadata.get('regulation_type', 'general'),
                    effective_date=None,
                    impact_level=self._assess_impact_level(content, startup_info),
                    affected_industries=[startup_info.industry],
                    source_url=metadata.get('url'),
                    discovered_date=datetime.now().strftime("%Y-%m-%d")
                )
                return update
                
        except Exception as e:
            logger.error(f"Error creating regulatory update from result: {e}")
        
        return None
    
    async def _generate_synthetic_updates(self, query: str, startup_info: Any) -> List[RegulatoryUpdate]:
        """Generate synthetic regulatory updates for MVP demonstration"""
        updates = []
        
        system_prompt = f"""
        Generate 1-2 realistic regulatory updates for {startup_info.industry} businesses 
        in {', '.join(startup_info.target_countries)} based on this query: {query}
        
        Create updates that would typically occur:
        1. New compliance requirements
        2. Changes to existing regulations
        3. New licensing requirements
        4. Data protection updates
        
        Make them realistic but clearly synthetic for MVP purposes.
        Include effective dates in the next 3-6 months.
        """
        
        try:
            response = gemini_client.generate_response_sync(
                f"Generate regulatory updates for: {query}",
                system_prompt=system_prompt,
                temperature=0.5
            )
            
            # Parse response into updates
            update_sections = response.split('\n\n')
            for i, section in enumerate(update_sections[:2]):
                if len(section.strip()) > 50:
                    country = startup_info.target_countries[0] if startup_info.target_countries else "Unknown"
                    
                    update = RegulatoryUpdate(
                        update_id=f"synthetic_update_{hash(section) % 10000}",
                        title=f"New {startup_info.industry} Regulation Update #{i+1}",
                        description=section.strip()[:300],
                        country=country,
                        regulation_type="update",
                        effective_date=self._generate_future_date(),
                        impact_level=self._assess_impact_level(section, startup_info),
                        affected_industries=[startup_info.industry],
                        source_url=None,  # No fake URL
                        discovered_date=datetime.now().strftime("%Y-%m-%d")
                    )
                    updates.append(update)
        
        except Exception as e:
            logger.error(f"Error generating synthetic updates: {e}")
        
        return updates
    
    def _generate_future_date(self) -> str:
        """Generate a realistic future effective date"""
        import random
        future_days = random.randint(30, 180)  # 1-6 months in the future
        future_date = datetime.now() + timedelta(days=future_days)
        return future_date.strftime("%Y-%m-%d")
    
    def _assess_impact_level(self, content: str, startup_info: Any) -> str:
        """Assess the impact level of a regulatory update"""
        content_lower = content.lower()
        
        # High impact indicators
        if any(term in content_lower for term in ['mandatory', 'required', 'must comply', 'penalty', 'fine']):
            return 'high'
        
        # Medium impact indicators
        if any(term in content_lower for term in ['should', 'recommended', 'update', 'change']):
            return 'medium'
        
        # Industry-specific high impact
        if startup_info.industry.lower() in content_lower:
            return 'high'
        
        return 'low'
    
    def _filter_relevant_updates(
        self, 
        updates: List[RegulatoryUpdate], 
        startup_info: Any
    ) -> List[RegulatoryUpdate]:
        """Filter updates for relevance to the startup"""
        relevant_updates = []
        
        for update in updates:
            relevance_score = self._calculate_relevance_score(update, startup_info)
            
            # Only include updates with relevance score > 0.5
            if relevance_score > 0.5:
                relevant_updates.append(update)
        
        # Sort by impact level and relevance
        return sorted(relevant_updates, key=lambda x: (
            {'high': 3, 'medium': 2, 'low': 1}[x.impact_level],
            x.title
        ), reverse=True)
    
    def _calculate_relevance_score(self, update: RegulatoryUpdate, startup_info: Any) -> float:
        """Calculate relevance score for an update"""
        score = 0.0
        
        # Country match
        if update.country in startup_info.target_countries:
            score += 0.4
        
        # Industry match
        if startup_info.industry in update.affected_industries:
            score += 0.4
        elif startup_info.industry.lower() in update.description.lower():
            score += 0.3
        
        # Business activity match
        for activity in startup_info.business_activities:
            if activity.lower() in update.description.lower():
                score += 0.1
        
        # Impact level bonus
        if update.impact_level == 'high':
            score += 0.2
        elif update.impact_level == 'medium':
            score += 0.1
        
        return min(score, 1.0)
    
    async def _create_monitoring_alert(
        self, 
        startup_info: Any, 
        update: RegulatoryUpdate
    ) -> MonitoringAlert:
        """Create a monitoring alert from a regulatory update"""
        
        # Generate recommended actions using Gemini
        system_prompt = f"""
        A {startup_info.industry} startup in {', '.join(startup_info.target_countries)} 
        needs to respond to this regulatory update:
        
        Update: {update.title}
        Description: {update.description}
        Impact Level: {update.impact_level}
        Effective Date: {update.effective_date}
        
        Provide 3-5 specific, actionable recommendations for how this startup should respond.
        Be practical and prioritize based on the impact level.
        """
        
        try:
            response = gemini_client.generate_response_sync(
                "Generate regulatory update response recommendations",
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            actions = self._parse_recommended_actions(response)
            
        except Exception as e:
            logger.error(f"Error generating alert recommendations: {e}")
            actions = ["Review the regulatory update", "Consult legal counsel", "Assess compliance impact"]
        
        alert = MonitoringAlert(
            alert_id=f"alert_{update.update_id}_{hash(str(datetime.now())) % 1000}",
            startup_industry=startup_info.industry,
            target_countries=startup_info.target_countries,
            regulatory_update=update,
            relevance_score=self._calculate_relevance_score(update, startup_info),
            recommended_actions=actions,
            alert_created=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return alert
    
    def _parse_recommended_actions(self, response: str) -> List[str]:
        """Parse recommended actions from Gemini response"""
        actions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or line.startswith(('1.', '2.', '3.', '4.', '5.')):
                action = line.lstrip('- •123456789.').strip()
                if len(action) > 10:
                    actions.append(action)
        
        # Fallback if no actions parsed
        if not actions:
            actions = [
                "Review the full regulatory update",
                "Assess impact on current operations", 
                "Consult with legal counsel",
                "Update compliance procedures if needed"
            ]
        
        return actions[:5]  # Limit to 5 actions
    
    async def _send_alerts(self, startup_id: str, alerts: List[MonitoringAlert]):
        """Send alerts to the startup (for MVP, just log them)"""
        logger.info(f"{self.agent_name}: Sending {len(alerts)} alerts to {startup_id}")
        
        for alert in alerts:
            # In production, this would send via email, Slack, etc.
            # For MVP, we'll just log and store the alerts
            logger.warning(f"REGULATORY ALERT for {startup_id}: {alert.regulatory_update.title}")
            logger.info(f"Impact: {alert.regulatory_update.impact_level}, Relevance: {alert.relevance_score:.2f}")
            
            # Store alert in vector store for historical tracking
            try:
                alert_content = f"""
                Regulatory Alert: {alert.regulatory_update.title}
                Industry: {alert.startup_industry}
                Countries: {', '.join(alert.target_countries)}
                Description: {alert.regulatory_update.description}
                Recommended Actions: {'; '.join(alert.recommended_actions)}
                """
                
                vector_store.add_compliance_case(
                    case_description=alert_content,
                    outcome="Alert generated - pending response",
                    metadata={
                        'alert_id': alert.alert_id,
                        'industry': alert.startup_industry,
                        'country': alert.target_countries[0] if alert.target_countries else 'Unknown',
                        'impact_level': alert.regulatory_update.impact_level,
                        'alert_type': 'regulatory_update'
                    }
                )
                
            except Exception as e:
                logger.error(f"Error storing alert in vector store: {e}")
    
    def start_monitoring(self):
        """Start the monitoring scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info(f"{self.agent_name}: Monitoring scheduler started")
    
    def stop_monitoring(self):
        """Stop the monitoring scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info(f"{self.agent_name}: Monitoring scheduler stopped")
    
    def get_monitoring_status(self, startup_id: str) -> Dict[str, Any]:
        """Get monitoring status for a startup"""
        if startup_id in self.active_monitors:
            config = self.active_monitors[startup_id]
            return {
                'startup_id': startup_id,
                'monitoring_active': True,
                'frequency': config['frequency'],
                'last_check': config['last_check'],
                'alerts_sent_count': len(config['alerts_sent'])
            }
        else:
            return {
                'startup_id': startup_id,
                'monitoring_active': False
            }

# Global monitoring agent instance
monitoring_agent = MonitoringAgent() 