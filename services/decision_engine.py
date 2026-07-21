def make_decision(risk_result, shipment):
    """
    Converts risk analysis into an enterprise-grade decision.
    """

    risk_score = risk_result["risk_score"]
    risk_level = risk_result["risk_level"]
    reasons = risk_result["reasons"]

    shipment_id, origin, destination, shipment_type, priority, status = shipment

    # ---------------------------
    # WEIGHTED DECISION LOGIC
    # ---------------------------

    score = 0
    breakdown = {}

    # 1. Risk contribution
    breakdown["base_risk"] = risk_score * 50
    score += breakdown["base_risk"]

    # 2. Priority adjustment
    priority_weight = {
        "Low": 5,
        "Medium": 10,
        "High": 20
    }

    breakdown["priority_impact"] = priority_weight.get(priority, 10)
    score += breakdown["priority_impact"]

    # 3. Status impact
    status_weight = {
        "Scheduled": 5,
        "In Transit": 10,
        "Delayed": 25
    }

    breakdown["status_impact"] = status_weight.get(status, 10)
    score += breakdown["status_impact"]

    # ---------------------------
    # DECISION RULES
    # ---------------------------

    if score < 40:
        decision = "SHIP"
        confidence = 0.85

    elif 40 <= score < 70:
        decision = "DELAY"
        confidence = 0.75

    else:
        decision = "REROUTE"
        confidence = 0.90

    # ---------------------------
    # HUMAN APPROVAL LOGIC
    # ---------------------------

    human_required = True if risk_level == "HIGH" or score > 65 else False

    # ---------------------------
    # FINAL OUTPUT
    # ---------------------------

    return {
        "decision": decision,
        "confidence": round(confidence * 100, 2),
        "score": round(score, 2),
        "risk_level": risk_level,
        "reasoning": reasons,

        "risk_breakdown": {
            "risk_score": risk_score,
            "priority": priority,
            "status": status,
        },

        "decision_breakdown": breakdown,

        "human_approval_required": human_required
    }