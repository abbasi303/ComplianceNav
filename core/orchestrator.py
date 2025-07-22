"""
ComplianceNavigator Orchestrator
LangGraph-based workflow orchestration for multi-agent compliance analysis
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from loguru import logger
from langgraph.graph import StateGraph, END
from langgraph.graph.message import MessageGraph
from langchain.schema import HumanMessage, AIMessage

# Import agents
from agents.intake_agent import intake_agent, StartupInfo
from agents.scout_agent import scout_agent
from agents.matcher_agent import matcher_agent
from agents.planner_agent import planner_agent
from agents.monitoring_agent import monitoring_agent

import asyncio
from datetime import datetime

class WorkflowState(BaseModel):
    """State object that flows through the agent workflow"""
    # Input
    user_query: str
    user_id: Optional[str] = None
    custom_sources: Optional[List[Dict]] = None  # User-provided custom sources
    
    # Custom Source Agent outputs
    processed_custom_sources: Optional[List[Any]] = None
    
    # Intake Agent outputs
    startup_info: Optional[StartupInfo] = None
    research_queries: Optional[List[Dict[str, str]]] = None
    
    # Scout Agent outputs
    regulatory_documents: Optional[List[Any]] = None
    
    # Matcher Agent outputs
    match_result: Optional[Any] = None
    
    # Planner Agent outputs
    compliance_plan: Optional[Any] = None
    
    # Workflow metadata
    workflow_id: str
    started_at: str
    completed_at: Optional[str] = None
    status: str = "running"
    errors: List[str] = []
    
    class Config:
        arbitrary_types_allowed = True

class ComplianceOrchestrator:
    """Main orchestrator for the compliance analysis workflow"""
    
    def __init__(self):
        """Initialize the orchestrator"""
        self.workflow = self._build_workflow()
        logger.info("ComplianceOrchestrator initialized")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the state graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes (agent functions)
        workflow.add_node("intake", self._intake_node)
        workflow.add_node("scout", self._scout_node)  
        workflow.add_node("matcher", self._matcher_node)
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("monitoring", self._monitoring_node)
        
        # Define the workflow edges
        workflow.set_entry_point("intake")
        workflow.add_edge("intake", "scout")
        workflow.add_edge("scout", "matcher")
        workflow.add_edge("matcher", "planner")
        workflow.add_edge("planner", "monitoring")
        workflow.add_edge("monitoring", END)
        
        # Compile the workflow
        return workflow.compile()
    
    async def process_compliance_request(
        self, 
        user_query: str, 
        user_id: Optional[str] = None,
        custom_sources: Optional[List[Dict]] = None,
        client_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a complete compliance analysis request with optional custom sources
        
        Args:
            user_query: User's description of their startup
            user_id: Optional user identifier
            custom_sources: Optional list of user-provided regulation sources
            
        Returns:
            Complete compliance analysis results
        """
        # Security validation
        try:
            from utils.security import security_middleware, security_auditor
            
            # Prepare request data for validation
            request_data = {
                'user_query': user_query,
                'user_id': user_id or 'anonymous'
            }
            
            if custom_sources:
                request_data['custom_sources'] = custom_sources
            
            # Validate request through security middleware
            validated_data = await security_middleware.validate_request(request_data, client_ip)
            
            # Update with validated data
            user_query = validated_data['user_query']
            custom_sources = validated_data.get('custom_sources')
            
            logger.info(f"Security validation passed for user: {user_id}")
            
        except Exception as security_error:
            logger.error(f"Security validation failed: {security_error}")
            
            # Log security incident
            try:
                from utils.security import security_auditor
                security_auditor.log_security_event(
                    'security_validation_failed',
                    {'error': str(security_error), 'user_id': user_id},
                    client_ip
                )
            except ImportError:
                pass
            
            return {
                'status': 'failed',
                'error': 'Security validation failed',
                'details': str(security_error)
            }

        workflow_id = f"workflow_{hash(user_query + str(datetime.now())) % 100000}"
        
        if custom_sources:
            logger.info(f"Starting compliance workflow {workflow_id} with {len(custom_sources)} custom sources")
        else:
            logger.info(f"Starting compliance workflow {workflow_id}")
        
        # Initialize workflow state
        initial_state = WorkflowState(
            user_query=user_query,
            user_id=user_id,
            workflow_id=workflow_id,
            started_at=datetime.now().isoformat()
        )
        
        # Store custom sources in state if provided
        if custom_sources:
            initial_state.custom_sources = custom_sources
        
        try:
            # Execute the workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Update completion status - handle both dict and object types
            completion_time = datetime.now().isoformat()
            if hasattr(final_state, 'completed_at'):
                final_state.completed_at = completion_time
                final_state.status = "completed"
            else:
                # Handle AddableValuesDict
                final_state['completed_at'] = completion_time
                final_state['status'] = "completed"
            
            logger.info(f"Compliance workflow {workflow_id} completed successfully")
            
            # Return structured results
            return self._format_workflow_results(final_state)
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
                "started_at": initial_state.started_at,
                "completed_at": datetime.now().isoformat()
            }
    
    async def _intake_node(self, state: WorkflowState) -> WorkflowState:
        """Intake Agent node - parses user input"""
        logger.info(f"Workflow {state.workflow_id}: Executing Intake Agent")
        
        try:
            # Parse startup description
            startup_info = intake_agent.parse_startup_description(state.user_query)
            state.startup_info = startup_info
            
            # Generate research queries
            research_queries = intake_agent.generate_research_queries(startup_info)
            state.research_queries = research_queries
            
            logger.info(f"Intake Agent completed: Industry={startup_info.industry}, Queries={len(research_queries)}")
            
        except Exception as e:
            error_msg = f"Intake Agent error: {str(e)}"
            state.errors.append(error_msg)
            logger.error(error_msg)
        
        return state
    
    async def _scout_node(self, state: WorkflowState) -> WorkflowState:
        """Scout Agent node - fetches regulatory information including custom sources"""
        logger.info(f"Workflow {state.workflow_id}: Executing Scout Agent")
        
        try:
            if not state.startup_info or not state.research_queries:
                raise Exception("Missing startup info or research queries from Intake Agent")
            
            # Research regulations with custom sources
            try:
                regulatory_documents = await scout_agent.research_regulations(
                    state.research_queries, 
                    state.startup_info,
                    custom_sources=state.custom_sources
                )
                
                # Debug logging
                logger.info(f"Scout Agent returned {len(regulatory_documents) if regulatory_documents else 0} documents")
                if regulatory_documents:
                    logger.info(f"First document type: {type(regulatory_documents[0])}")
                    logger.info(f"First document keys: {regulatory_documents[0].__dict__.keys() if hasattr(regulatory_documents[0], '__dict__') else 'No __dict__'}")
                
                state.regulatory_documents = regulatory_documents
                
                # Additional debugging
                logger.info(f"State regulatory_documents after assignment: {len(state.regulatory_documents) if state.regulatory_documents else 0}")
                logger.info(f"State regulatory_documents type: {type(state.regulatory_documents)}")
                
            except Exception as e:
                logger.error(f"Scout Agent research failed: {e}")
                # Provide fallback empty list to prevent workflow failure
                state.regulatory_documents = []
                logger.info("Using empty regulatory documents list as fallback")
            
            if state.custom_sources:
                logger.info(f"Scout Agent completed: Found {len(regulatory_documents)} regulatory documents (including custom sources)")
            else:
                logger.info(f"Scout Agent completed: Found {len(regulatory_documents)} regulatory documents")
            
        except Exception as e:
            error_msg = f"Scout Agent error: {str(e)}"
            state.errors.append(error_msg)
            logger.error(error_msg)
        
        return state
    
    async def _matcher_node(self, state: WorkflowState) -> WorkflowState:
        """Matcher Agent node - analyzes compliance gaps"""
        logger.info(f"Workflow {state.workflow_id}: Executing Matcher Agent")
        
        try:
            # Debug logging
            logger.info(f"Matcher node - startup_info: {state.startup_info is not None}")
            logger.info(f"Matcher node - regulatory_documents: {state.regulatory_documents is not None}")
            if state.regulatory_documents:
                logger.info(f"Matcher node - regulatory_documents count: {len(state.regulatory_documents)}")
                logger.info(f"Matcher node - regulatory_documents type: {type(state.regulatory_documents)}")
                if len(state.regulatory_documents) > 0:
                    logger.info(f"Matcher node - first document type: {type(state.regulatory_documents[0])}")
            else:
                logger.warning("Matcher node - regulatory_documents is None or empty")
            
            if not state.startup_info:
                raise Exception("Missing startup info from previous agents")
            
            # Handle empty regulatory documents gracefully
            if not state.regulatory_documents:
                logger.warning("No regulatory documents found, creating empty match result")
                # Create a minimal match result to allow workflow to continue
                from agents.matcher_agent import ComplianceGap, MatchResult
                empty_gap = ComplianceGap(
                    regulation_title="No regulations found",
                    regulation_source="System",
                    gap_description="No regulatory documents were discovered for analysis",
                    risk_level="unknown",
                    compliance_requirement="Contact regulatory authorities directly",
                    recommended_action="Manual research required"
                )
                match_result = MatchResult(
                    compliance_gaps=[empty_gap],
                    overall_risk_level="unknown",
                    summary="No regulatory documents available for analysis"
                )
            else:
                # Analyze compliance gaps
                match_result = await matcher_agent.analyze_compliance_gaps(
                    state.startup_info,
                    state.regulatory_documents
                )
            state.match_result = match_result
            
            logger.info(f"Matcher Agent completed: Found {len(match_result.compliance_gaps)} gaps, risk level {match_result.overall_risk_level}")
            
        except Exception as e:
            error_msg = f"Matcher Agent error: {str(e)}"
            state.errors.append(error_msg)
            logger.error(error_msg)
        
        return state
    
    async def _planner_node(self, state: WorkflowState) -> WorkflowState:
        """Planner Agent node - creates action plan"""
        logger.info(f"Workflow {state.workflow_id}: Executing Planner Agent")
        
        try:
            if not state.startup_info:
                raise Exception("Missing startup info from previous agents")
            
            if not state.match_result:
                logger.warning("No match result found, creating empty compliance plan")
                # Create a minimal compliance plan to allow workflow to continue
                from agents.planner_agent import ActionItem, CompliancePlan
                empty_action = ActionItem(
                    title="Manual Research Required",
                    description="No automated analysis available. Please conduct manual regulatory research.",
                    priority="high",
                    estimated_effort="2-4 weeks",
                    dependencies=[],
                    risk_level="unknown"
                )
                compliance_plan = CompliancePlan(
                    action_items=[empty_action],
                    overall_risk_level="unknown",
                    summary="Manual research required due to insufficient data"
                )
            else:
                # Create compliance plan
                compliance_plan = await planner_agent.create_compliance_plan(
                    state.startup_info,
                    state.match_result
                )
            state.compliance_plan = compliance_plan
            
            logger.info(f"Planner Agent completed: Created plan with {len(compliance_plan.action_items)} action items")
            
        except Exception as e:
            error_msg = f"Planner Agent error: {str(e)}"
            state.errors.append(error_msg)
            logger.error(error_msg)
        
        return state
    
    async def _monitoring_node(self, state: WorkflowState) -> WorkflowState:
        """Monitoring Agent node - sets up ongoing monitoring"""
        logger.info(f"Workflow {state.workflow_id}: Executing Monitoring Agent")
        
        try:
            if not state.startup_info:
                raise Exception("Missing startup info for monitoring setup")
            
            # Set up monitoring for this startup
            startup_id = state.user_id or state.workflow_id
            monitoring_agent.setup_monitoring(
                startup_id=startup_id,
                startup_info=state.startup_info,
                monitoring_frequency="weekly"  # Default frequency
            )
            
            # Start monitoring if not already running
            monitoring_agent.start_monitoring()
            
            logger.info(f"Monitoring Agent completed: Set up monitoring for {startup_id}")
            
        except Exception as e:
            error_msg = f"Monitoring Agent error: {str(e)}"
            state.errors.append(error_msg)
            logger.error(error_msg)
        
        return state
    
    def _format_workflow_results(self, state) -> Dict[str, Any]:
        """Format the final workflow results for presentation"""
        
        # Handle LangGraph state object which may be dict-like
        if hasattr(state, 'startup_info'):
            startup_info = state.startup_info
            workflow_id = state.workflow_id
            status = state.status
            started_at = state.started_at
            completed_at = getattr(state, 'completed_at', None)
            errors = getattr(state, 'errors', [])
        else:
            # If it's a dict-like object (AddableValuesDict)
            startup_info = state.get('startup_info')
            workflow_id = state.get('workflow_id')
            status = state.get('status')
            started_at = state.get('started_at')
            completed_at = state.get('completed_at')
            errors = state.get('errors', [])
        
        # Handle case where workflow failed early
        if not startup_info:
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": "Failed to parse startup information",
                "errors": errors
            }
        
        # Get other state variables using same approach
        research_queries = state.get('research_queries') if not hasattr(state, 'research_queries') else state.research_queries
        regulatory_documents = state.get('regulatory_documents') if not hasattr(state, 'regulatory_documents') else state.regulatory_documents
        match_result = state.get('match_result') if not hasattr(state, 'match_result') else state.match_result
        compliance_plan = state.get('compliance_plan') if not hasattr(state, 'compliance_plan') else state.compliance_plan
        
        # Basic startup information
        results = {
            "workflow_id": workflow_id,
            "status": status,
            "started_at": started_at,
            "completed_at": completed_at,
            "startup_info": {
                "company_name": startup_info.company_name,
                "industry": startup_info.industry,
                "target_countries": startup_info.target_countries,
                "business_activities": startup_info.business_activities,
                "data_handling": startup_info.data_handling,
                "customer_types": startup_info.customer_types
            }
        }
        
        # Research information
        if research_queries:
            results["research"] = {
                "queries_generated": len(research_queries),
                "query_types": list(set([q.get('type', 'general') for q in research_queries]))
            }
        
        # Regulatory documents found
        if regulatory_documents:
            # Convert regulatory documents to dict format for JSON serialization
            documents_list = []
            for doc in regulatory_documents:
                doc_dict = {
                    "title": doc.title,
                    "content": doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,  # Truncate for performance
                    "source": doc.source,
                    "country": doc.country,
                    "regulation_type": doc.regulation_type,
                    "url": doc.url or "",
                    "authority": doc.authority or "",
                    "regulation_id": doc.regulation_id or "",
                    "citation_format": doc.citation_format or "",
                    "relevance_score": getattr(doc, 'relevance_score', 0.0),
                    # Enhanced attributes from our improvements
                    "user_provided": getattr(doc, 'user_provided', False),
                    "priority_weight": getattr(doc, 'priority_weight', 0.0),
                    "source_priority": getattr(doc, 'source_priority', ''),
                    "coverage_quality": getattr(doc, 'coverage_quality', 'standard')
                }
                documents_list.append(doc_dict)
            
            results["regulatory_research"] = {
                "documents_found": len(regulatory_documents),
                "countries_covered": list(set([doc.country for doc in regulatory_documents])),
                "regulation_types": list(set([doc.regulation_type for doc in regulatory_documents])),
                # Add the actual documents so the UI can display them
                "documents": documents_list,
                "regulations": documents_list  # Alias for backward compatibility
            }
        
        # Compliance analysis
        if match_result:
            results["compliance_analysis"] = {
                "gaps_found": len(match_result.compliance_gaps),
                "compliant_areas": len(match_result.compliant_areas),
                "overall_risk_level": match_result.overall_risk_level,
                "recommendations_summary": match_result.recommendations_summary,
                "compliance_gaps": [
                    {
                        "title": gap.regulation_title,
                        "gap_type": gap.gap_type,
                        "severity": gap.severity,
                        "description": gap.description,
                        "recommended_actions": gap.recommended_actions,
                        "country": gap.country,
                        "deadline": gap.deadline,
                        "estimated_cost": gap.estimated_cost,
                        # Include source information that the UI expects
                        "source_url": gap.source_url,
                        "regulation_id": gap.regulation_id,
                        "authority": gap.authority,
                        "citation": gap.citation
                    }
                    for gap in match_result.compliance_gaps
                ]
            }
        
        # Implementation plan
        if compliance_plan:
            results["implementation_plan"] = {
                "plan_id": compliance_plan.plan_id,
                "total_action_items": len(compliance_plan.action_items),
                "implementation_timeline": compliance_plan.implementation_timeline,
                "total_estimated_cost": compliance_plan.total_estimated_cost,
                "risk_level": compliance_plan.risk_level,
                "next_review_date": compliance_plan.next_review_date,
                "action_items": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "description": item.description,
                        "priority": item.priority,
                        "category": item.category,
                        "estimated_effort": item.estimated_effort,
                        "estimated_cost": item.estimated_cost,
                        "deadline": item.deadline,
                        "dependencies": item.dependencies,
                        "resources_needed": item.resources_needed,
                        "status": item.status
                    }
                    for item in compliance_plan.action_items
                ]
            }
        
        # Add any errors that occurred
        if errors:
            results["errors"] = errors
        
        return results

# Global orchestrator instance
orchestrator = ComplianceOrchestrator() 