from typing import TypedDict, Optional, List


class SupplyChainState(TypedDict):
    """
    Shared state passed between every LangGraph node.
    Every node can read from it and update it.
    """

    # ==========================================================
    # User Input
    # ==========================================================

    shipment_id: str

    # ==========================================================
    # Shipment Information
    # ==========================================================

    shipment: Optional[tuple]

    # ==========================================================
    # Tool Outputs
    # ==========================================================

    weather: Optional[dict]
    news: Optional[dict]
    route: Optional[dict]
    policies: Optional[List[str]]

    # Detailed News Intelligence
    relevant_news_count: Optional[int]
    ignored_news_count: Optional[int]
    news_assessments: Optional[List[dict]]

    # ==========================================================
    # Risk Analysis
    # ==========================================================

    risk_score: Optional[float]
    risk_level: Optional[str]

    shipment_risk: Optional[int]
    weather_risk: Optional[int]
    news_risk: Optional[int]
    route_risk: Optional[int]

    risk_reasons: Optional[List[str]]

    primary_concern: Optional[str]

    operational_impact: Optional[dict]

    recommended_attention: Optional[str]

    # Detailed explanation of scoring
    risk_breakdown_details: Optional[dict]

    # ==========================================================
    # Agent 1 - Disruption Detection Agent
    # ==========================================================

    disruption_assessment: Optional[dict]

    # ==========================================================
    # Agent 2 - Logistics Decision Agent
    # ==========================================================

    decision: Optional[str]
    confidence: Optional[float]
    final_score: Optional[float]
    decision_reason: Optional[str]
    final_recommendation: Optional[str]

    # ==========================================================
    # Conditional Routing / Human Approval
    # ==========================================================

    approval_status: Optional[str]

    human_required: Optional[bool]
    human_decision: Optional[str]

    # ==========================================================
    # Workflow Status
    # ==========================================================

    workflow_status: Optional[str]