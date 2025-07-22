"""
Action Planner Agent
Synthesizes compliance gaps into actionable recommendations and creates implementation plans
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from loguru import logger
from integrations.gemini_client import gemini_client
from datetime import datetime, timedelta
import json

class ActionItem(BaseModel):
    """Individual action item in a compliance plan"""
    id: str
    title: str
    description: str
    priority: str  # 'critical', 'high', 'medium', 'low'
    category: str  # 'licensing', 'data_protection', 'reporting', etc.
    estimated_effort: str  # 'hours', 'days', 'weeks'
    estimated_cost: Optional[str] = None
    deadline: Optional[str] = None
    dependencies: List[str] = []
    resources_needed: List[str] = []
    status: str = "pending"

class CompliancePlan(BaseModel):
    """Complete compliance implementation plan"""
    plan_id: str
    startup_name: str
    industry: str
    target_countries: List[str]
    plan_created: str
    action_items: List[ActionItem]
    implementation_timeline: str
    total_estimated_cost: str
    risk_level: str
    next_review_date: str

class PlannerAgent:
    """Agent for creating actionable compliance plans from identified gaps"""
    
    def __init__(self):
        """Initialize the Planner Agent"""
        self.agent_name = "PlannerAgent"
        logger.info(f"{self.agent_name} initialized")
    
    async def create_compliance_plan(
        self, 
        startup_info: Any, 
        match_result: Any
    ) -> CompliancePlan:
        """
        Create a comprehensive compliance action plan
        
        Args:
            startup_info: Structured startup information
            match_result: Results from the Matcher Agent
            
        Returns:
            Detailed compliance implementation plan
        """
        logger.info(f"{self.agent_name}: Creating compliance plan for {startup_info.industry} startup")
        
        # Generate action items from compliance gaps
        action_items = await self._generate_action_items(startup_info, match_result.compliance_gaps)
        
        # Prioritize and sequence action items
        prioritized_items = self._prioritize_action_items(action_items)
        
        # Generate implementation timeline
        timeline = await self._generate_implementation_timeline(prioritized_items)
        
        # Calculate total estimated costs
        total_cost = self._calculate_total_cost(prioritized_items)
        
        # Set next review date
        next_review = self._calculate_next_review_date(match_result.overall_risk_level)
        
        plan = CompliancePlan(
            plan_id=f"plan_{hash(startup_info.industry + str(datetime.now())) % 10000}",
            startup_name=startup_info.company_name or f"{startup_info.industry} Startup",
            industry=startup_info.industry,
            target_countries=startup_info.target_countries,
            plan_created=datetime.now().strftime("%Y-%m-%d"),
            action_items=prioritized_items,
            implementation_timeline=timeline,
            total_estimated_cost=total_cost,
            risk_level=match_result.overall_risk_level,
            next_review_date=next_review
        )
        
        logger.info(f"{self.agent_name}: Created plan with {len(prioritized_items)} action items, risk level: {match_result.overall_risk_level}")
        
        return plan
    
    async def _generate_action_items(self, startup_info: Any, compliance_gaps: List[Any]) -> List[ActionItem]:
        """Generate specific action items from compliance gaps"""
        action_items = []
        
        for i, gap in enumerate(compliance_gaps):
            # Use Gemini to generate detailed action items for each gap
            action_item = await self._create_action_item_from_gap(gap, startup_info, i)
            if action_item:
                action_items.append(action_item)
        
        # Add general compliance actions
        general_actions = self._generate_general_compliance_actions(startup_info)
        action_items.extend(general_actions)
        
        return action_items
    
    async def _create_action_item_from_gap(
        self, 
        gap: Any, 
        startup_info: Any, 
        index: int
    ) -> Optional[ActionItem]:
        """Create a detailed action item from a compliance gap"""
        
        system_prompt = f"""
        Create a specific, actionable compliance task for a {startup_info.industry} startup.
        
        Compliance Gap:
        - Regulation: {gap.regulation_title}
        - Activity: {gap.business_activity}
        - Gap Type: {gap.gap_type}
        - Severity: {gap.severity}
        - Description: {gap.description}
        
        Create a concrete action item with:
        1. Clear, actionable title
        2. Step-by-step description
        3. Required resources (legal counsel, documentation, etc.)
        4. Realistic effort estimate (hours/days/weeks)
        5. Estimated cost if applicable
        
        Be specific and practical.
        """
        
        try:
            response = gemini_client.generate_response_sync(
                f"Create action item for: {gap.gap_type} compliance gap",
                system_prompt=system_prompt,
                temperature=0.4
            )
            
            # Parse response into ActionItem
            action_item = ActionItem(
                id=f"action_{index + 1}_{gap.gap_type}",
                title=self._extract_title_from_response(response, gap),
                description=response[:300] + "..." if len(response) > 300 else response,
                priority=gap.severity,
                category=gap.gap_type,
                estimated_effort=self._estimate_effort(gap, response),
                estimated_cost=gap.estimated_cost or self._estimate_cost_from_response(response),
                deadline=gap.deadline or self._suggest_deadline(gap.severity),
                dependencies=self._identify_dependencies(gap, response),
                resources_needed=self._identify_resources(gap, response)
            )
            
            return action_item
            
        except Exception as e:
            logger.error(f"Error creating action item from gap: {e}")
            return None
    
    def _generate_general_compliance_actions(self, startup_info: Any) -> List[ActionItem]:
        """Generate general compliance actions that apply to most startups"""
        general_actions = []
        
        # Legal structure action
        general_actions.append(ActionItem(
            id="general_legal_structure",
            title="Establish Legal Business Structure",
            description="Register business entity and obtain necessary business licenses in target jurisdictions.",
            priority="high",
            category="business_setup",
            estimated_effort="1-2 weeks",
            estimated_cost="$500-2000",
            resources_needed=["Business attorney", "Registration documents"]
        ))
        
        # Data protection (if applicable)
        if startup_info.data_handling:
            general_actions.append(ActionItem(
                id="general_data_protection",
                title="Implement Data Protection Framework",
                description="Establish privacy policy, data handling procedures, and GDPR compliance if operating in EU.",
                priority="high",
                category="data_protection", 
                estimated_effort="2-3 weeks",
                estimated_cost="$1000-3000",
                resources_needed=["Privacy attorney", "Technical implementation"]
            ))
        
        # Compliance monitoring
        general_actions.append(ActionItem(
            id="general_monitoring",
            title="Set Up Compliance Monitoring System",
            description="Implement regular compliance reviews and regulatory update monitoring.",
            priority="medium",
            category="monitoring",
            estimated_effort="1 week",
            estimated_cost="$200-500",
            resources_needed=["Compliance software", "Legal updates subscription"]
        ))
        
        return general_actions
    
    def _prioritize_action_items(self, action_items: List[ActionItem]) -> List[ActionItem]:
        """Prioritize and sequence action items based on priority and dependencies"""
        if not action_items:
            return []
        
        # Define priority order
        priority_order = {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}
        
        # Sort by priority first
        sorted_items = sorted(action_items, key=lambda x: priority_order.get(x.priority, 5))
        
        # Handle dependencies (simple approach - move dependent items after their dependencies)
        final_order = []
        processed_ids = set()
        
        for item in sorted_items:
            self._add_item_with_dependencies(item, sorted_items, final_order, processed_ids)
        
        return final_order
    
    def _add_item_with_dependencies(
        self, 
        item: ActionItem, 
        all_items: List[ActionItem], 
        final_order: List[ActionItem], 
        processed_ids: set
    ):
        """Add item to final order, ensuring dependencies are added first"""
        if item.id in processed_ids:
            return
        
        # Add dependencies first
        for dep_id in item.dependencies:
            dep_item = next((i for i in all_items if i.id == dep_id), None)
            if dep_item and dep_item.id not in processed_ids:
                self._add_item_with_dependencies(dep_item, all_items, final_order, processed_ids)
        
        # Add the item itself
        final_order.append(item)
        processed_ids.add(item.id)
    
    async def _generate_implementation_timeline(self, action_items: List[ActionItem]) -> str:
        """Generate a high-level implementation timeline"""
        if not action_items:
            return "No actions required."
        
        # Calculate phases based on priorities
        critical_items = [item for item in action_items if item.priority == 'critical']
        high_items = [item for item in action_items if item.priority == 'high']
        medium_items = [item for item in action_items if item.priority == 'medium']
        low_items = [item for item in action_items if item.priority == 'low']
        
        timeline_parts = []
        
        if critical_items:
            timeline_parts.append(f"Phase 1 (Immediate - 2 weeks): {len(critical_items)} critical items")
        if high_items:
            timeline_parts.append(f"Phase 2 (Month 1): {len(high_items)} high-priority items")
        if medium_items:
            timeline_parts.append(f"Phase 3 (Months 2-3): {len(medium_items)} medium-priority items")
        if low_items:
            timeline_parts.append(f"Phase 4 (Ongoing): {len(low_items)} low-priority items")
        
        return "; ".join(timeline_parts)
    
    def _calculate_total_cost(self, action_items: List[ActionItem]) -> str:
        """Calculate total estimated cost for all action items"""
        total_min = 0
        total_max = 0
        
        for item in action_items:
            if item.estimated_cost:
                cost_range = self._parse_cost_range(item.estimated_cost)
                if cost_range:
                    total_min += cost_range[0]
                    total_max += cost_range[1]
        
        if total_min > 0:
            return f"${total_min:,} - ${total_max:,}"
        else:
            return "Cost estimates vary - consult legal counsel"
    
    def _parse_cost_range(self, cost_str: str) -> Optional[tuple]:
        """Parse cost string into min/max range"""
        import re
        
        # Handle ranges like "$500-2000"
        range_match = re.search(r'\$?(\d{1,3}(?:,?\d{3})*)\s*-\s*\$?(\d{1,3}(?:,?\d{3})*)', cost_str)
        if range_match:
            min_cost = int(range_match.group(1).replace(',', ''))
            max_cost = int(range_match.group(2).replace(',', ''))
            return (min_cost, max_cost)
        
        # Handle single values like "$1500"
        single_match = re.search(r'\$?(\d{1,3}(?:,?\d{3})*)', cost_str)
        if single_match:
            cost = int(single_match.group(1).replace(',', ''))
            return (cost, cost * 1.5)  # Assume 50% variance
        
        return None
    
    def _calculate_next_review_date(self, risk_level: str) -> str:
        """Calculate next compliance review date based on risk level"""
        today = datetime.now()
        
        if risk_level == 'critical':
            next_review = today + timedelta(weeks=4)  # 1 month
        elif risk_level == 'high':
            next_review = today + timedelta(weeks=12)  # 3 months
        elif risk_level == 'medium':
            next_review = today + timedelta(weeks=24)  # 6 months
        else:
            next_review = today + timedelta(weeks=52)  # 1 year
        
        return next_review.strftime("%Y-%m-%d")
    
    def _extract_title_from_response(self, response: str, gap: Any) -> str:
        """Extract action title from Gemini response"""
        lines = response.split('\n')
        
        # Look for title-like lines
        for line in lines:
            line = line.strip()
            if line and (line.endswith(':') or len(line) < 80):
                # Clean up the title
                title = line.rstrip(':').strip()
                if len(title) > 10 and not title.lower().startswith('step'):
                    return title
        
        # Fallback to generating title from gap
        return f"Address {gap.gap_type.replace('_', ' ').title()} Compliance Gap"
    
    def _estimate_effort(self, gap: Any, response: str) -> str:
        """Estimate effort required for action item"""
        response_lower = response.lower()
        
        if any(term in response_lower for term in ['complex', 'extensive', 'comprehensive']):
            return "2-4 weeks"
        elif any(term in response_lower for term in ['simple', 'straightforward', 'quick']):
            return "1-3 days"
        elif gap.severity in ['critical', 'high']:
            return "1-2 weeks"
        else:
            return "3-7 days"
    
    def _estimate_cost_from_response(self, response: str) -> Optional[str]:
        """Extract cost estimates from response"""
        import re
        
        cost_patterns = [
            r'\$[\d,]+-\$[\d,]+',
            r'\$[\d,]+',
            r'(\d+)\s*-\s*(\d+)\s*dollars?',
        ]
        
        for pattern in cost_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _suggest_deadline(self, severity: str) -> str:
        """Suggest deadline based on severity"""
        today = datetime.now()
        
        if severity == 'critical':
            deadline = today + timedelta(weeks=2)
        elif severity == 'high':
            deadline = today + timedelta(weeks=6)
        elif severity == 'medium':
            deadline = today + timedelta(weeks=12)
        else:
            deadline = today + timedelta(weeks=24)
        
        return deadline.strftime("%Y-%m-%d")
    
    def _identify_dependencies(self, gap: Any, response: str) -> List[str]:
        """Identify dependencies from gap and response"""
        dependencies = []
        
        # Simple rule-based dependency detection
        if gap.gap_type == 'licensing' and 'general_legal_structure' not in dependencies:
            dependencies.append('general_legal_structure')
        
        if 'legal' in response.lower() or 'attorney' in response.lower():
            # This might depend on having legal counsel
            pass
        
        return dependencies
    
    def _identify_resources(self, gap: Any, response: str) -> List[str]:
        """Identify required resources from gap and response"""
        resources = []
        response_lower = response.lower()
        
        if any(term in response_lower for term in ['attorney', 'lawyer', 'legal counsel']):
            resources.append('Legal counsel')
        
        if any(term in response_lower for term in ['accountant', 'tax', 'financial']):
            resources.append('Accounting/Tax advisor')
        
        if any(term in response_lower for term in ['consultant', 'expert', 'specialist']):
            resources.append('Industry consultant')
        
        if any(term in response_lower for term in ['document', 'form', 'application']):
            resources.append('Documentation preparation')
        
        if gap.gap_type == 'data_protection':
            resources.extend(['Privacy attorney', 'Technical implementation'])
        
        if gap.gap_type == 'licensing':
            resources.extend(['Legal documentation', 'Government fees'])
        
        return list(set(resources))  # Remove duplicates

# Global planner agent instance
planner_agent = PlannerAgent() 