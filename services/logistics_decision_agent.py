def generate_logistics_decision(state):
    shipment = state.get("shipment")
    risk_score = state.get("risk_score", 0)
    risk_level = state.get("risk_level", "Unknown")
    route = state.get("route") or {}
    disruption = state.get("disruption_assessment") or {}
    policies = state.get("policies") or []

    if shipment is None:
        return {
            "decision": "Review",
            "confidence": 0.0,
            "final_score": risk_score,
            "decision_reason": "Shipment information is unavailable.",
            "final_recommendation": (
                "Manual review is required because the shipment record "
                "could not be evaluated."
            ),
        }

    shipment_type = shipment[3]
    priority = shipment[4]
    shipment_status = shipment[5]

    route_level = route.get("route_risk", "Unknown")
    disruption_severity = disruption.get("severity", "Unknown")

    decision = "Ship"
    confidence = 0.85

    if risk_level == "High":
        if route_level == "High":
            decision = "Reroute"
            confidence = 0.90
            decision_reason = (
                "The shipment has a High overall risk level and the current "
                "route is classified as High risk."
            )

        else:
            decision = "Delay"
            confidence = 0.88
            decision_reason = (
                "The shipment has a High overall risk level and should not "
                "continue under normal execution conditions."
            )

    elif risk_level == "Medium":
        if route_level == "High":
            decision = "Reroute"
            confidence = 0.86
            decision_reason = (
                "The shipment has manageable overall risk, but the current "
                "route has High transportation risk."
            )

        elif shipment_status == "Delayed":
            decision = "Delay"
            confidence = 0.82
            decision_reason = (
                "The shipment is already delayed and has additional risk "
                "exposure that requires schedule review."
            )

        else:
            decision = "Ship"
            confidence = 0.80
            decision_reason = (
                "The shipment has Medium risk, but current conditions remain "
                "manageable with active monitoring."
            )

    else:
        decision = "Ship"
        confidence = 0.92
        decision_reason = (
            "The shipment has Low overall risk and can continue under normal "
            "operating procedures."
        )

    if decision == "Ship":
        final_recommendation = (
            f"Proceed with the {shipment_type} shipment while monitoring "
            "weather, route conditions, and external disruption signals."
        )

    elif decision == "Delay":
        final_recommendation = (
            f"Temporarily delay the {shipment_type} shipment and reassess "
            "the identified disruption conditions before release."
        )

    elif decision == "Reroute":
        final_recommendation = (
            f"Evaluate an alternate route for the {shipment_type} shipment "
            "before continuing transportation."
        )

    else:
        final_recommendation = "Manual logistics review is required."

    return {
        "decision": decision,
        "confidence": confidence,
        "final_score": risk_score,
        "decision_reason": decision_reason,
        "final_recommendation": final_recommendation,
        "policy_context_count": len(policies),
        "disruption_severity": disruption_severity,
        "priority": priority,
    }