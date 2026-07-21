from langgraph.graph import StateGraph, END
from workflow.state import SupplyChainState
from workflow.nodes import (
    shipment_lookup_node,
    weather_node,
    news_node,
    route_node,
    risk_assessment_node,
    policy_retrieval_node,
    disruption_detection_node,
    logistics_decision_node,
    approval_routing_node,
    auto_approval_node,
    human_review_node,
)


def build_graph():
    graph = StateGraph(SupplyChainState)

    # Register workflow nodes
    graph.add_node(
        "shipment_lookup",
        shipment_lookup_node
    )

    graph.add_node(
        "weather",
        weather_node
    )

    graph.add_node(
        "news",
        news_node
    )

    graph.add_node(
        "route",
        route_node
    )

    graph.add_node(
        "risk_assessment",
        risk_assessment_node
    )

    graph.add_node(
        "policy_retrieval",
        policy_retrieval_node
    )

    graph.add_node(
        "disruption_detection",
        disruption_detection_node
    )

    graph.add_node(
        "logistics_decision",
        logistics_decision_node
    )

    graph.add_node(
    "approval_routing",
    approval_routing_node,
    )

    graph.add_node(
        "auto_approval",
        auto_approval_node,
    )

    graph.add_node(
        "human_review",
        human_review_node,
    )

    # Set workflow starting point
    graph.set_entry_point("shipment_lookup")

    # Define workflow sequence
    graph.add_edge(
        "shipment_lookup",
        "weather"
    )

    graph.add_edge(
        "weather",
        "news"
    )

    graph.add_edge(
        "news",
        "route"
    )

    graph.add_edge(
        "route",
        "risk_assessment"
    )

    graph.add_edge(
        "risk_assessment",
        "policy_retrieval"
    )

    graph.add_edge(
        "policy_retrieval",
        "disruption_detection"
    )

    graph.add_edge(
        "disruption_detection",
        "logistics_decision"
    )

    graph.add_edge(
        "logistics_decision",
        "approval_routing"
    )

    graph.add_conditional_edges(
    "approval_routing",
    lambda state: state["approval_status"],
    {
        "Auto Approved": "auto_approval",
        "Human Review Required": "human_review",
    },
    )

    graph.add_edge(
    "auto_approval",
    END
    )

    graph.add_edge(
        "human_review",
        END
    )

    return graph.compile()


def run_graph(app, shipment_id: str):
    initial_state = {
        "shipment_id": shipment_id
    }

    return app.invoke(initial_state)
