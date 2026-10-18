from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import InvestigationState
from app.agents.supervisor import SupervisorAgent
from app.agents.sensor_analytics import SensorAnalyticsAgent
from app.agents.rag_knowledge import RAGKnowledgeAgent
from app.agents.web_research import WebResearchAgent
from app.agents.evidence_normalizer import EvidenceNormalizer
from app.agents.root_cause import RootCauseAnalysisAgent
from app.agents.maintenance_planner import MaintenancePlanningAgent
from app.graph.safety_verification import SafetyVerificationEngine

# Agent Node Instances
sensor_agent = SensorAnalyticsAgent()
rag_agent = RAGKnowledgeAgent()
web_agent = WebResearchAgent()
root_cause_agent = RootCauseAnalysisAgent()
planner_agent = MaintenancePlanningAgent()

def node_sensor_analytics(state: InvestigationState) -> Dict[str, Any]:
    return sensor_agent.run(state)

def node_rag_retrieval(state: InvestigationState) -> Dict[str, Any]:
    return rag_agent.run(state)

def node_web_research(state: InvestigationState) -> Dict[str, Any]:
    return web_agent.run(state)

def node_merge_evidence(state: InvestigationState) -> Dict[str, Any]:
    return EvidenceNormalizer.merge_evidence(state)

def node_check_sufficiency(state: InvestigationState) -> Dict[str, Any]:
    return SupervisorAgent.evaluate_evidence_sufficiency(state)

def node_root_cause(state: InvestigationState) -> Dict[str, Any]:
    return root_cause_agent.run(state)

def node_maintenance_planning(state: InvestigationState) -> Dict[str, Any]:
    return planner_agent.run(state)

def node_safety_verification(state: InvestigationState) -> Dict[str, Any]:
    return SafetyVerificationEngine.verify_investigation(state)

def node_compile_report(state: InvestigationState) -> Dict[str, Any]:
    return SupervisorAgent.compile_final_report(state)

def route_evidence_check(state: InvestigationState) -> Literal["rag_retrieval", "root_cause_analysis"]:
    if state.get("route_step") == "additional_retrieval":
        return "rag_retrieval"
    return "root_cause_analysis"

def build_investigation_graph():
    """Builds and compiles the complete LangGraph StateGraph workflow."""
    workflow = StateGraph(InvestigationState)

    # 1. Register Nodes
    workflow.add_node("sensor_analytics", node_sensor_analytics)
    workflow.add_node("rag_retrieval", node_rag_retrieval)
    workflow.add_node("web_research", node_web_research)
    workflow.add_node("merge_evidence", node_merge_evidence)
    workflow.add_node("check_sufficiency", node_check_sufficiency)
    workflow.add_node("root_cause_analysis", node_root_cause)
    workflow.add_node("maintenance_planning", node_maintenance_planning)
    workflow.add_node("safety_verification", node_safety_verification)
    workflow.add_node("compile_report", node_compile_report)

    # 2. Register Edges
    # Start sequentially triggers analytical and retrieval nodes
    workflow.add_edge(START, "sensor_analytics")
    workflow.add_edge("sensor_analytics", "rag_retrieval")
    workflow.add_edge("rag_retrieval", "web_research")
    workflow.add_edge("web_research", "merge_evidence")
    workflow.add_edge("merge_evidence", "check_sufficiency")

    # Conditional sufficiency routing
    workflow.add_conditional_edges(
        "check_sufficiency",
        route_evidence_check,
        {
            "rag_retrieval": "rag_retrieval",
            "root_cause_analysis": "root_cause_analysis"
        }
    )

    workflow.add_edge("root_cause_analysis", "maintenance_planning")
    workflow.add_edge("maintenance_planning", "safety_verification")
    workflow.add_edge("safety_verification", "compile_report")
    workflow.add_edge("compile_report", END)

    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app

# Singleton compiled app
investigation_app = build_investigation_graph()
