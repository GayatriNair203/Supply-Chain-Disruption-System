from rules.rules_engine import get_rules

def detect_disruption(shipment):
    """
    shipment = (id, origin, destination, type, priority, status)
    """

    shipment_id, origin, destination, shipment_type, priority, status = shipment

    rules = get_rules(shipment_type)

    risk_score = 0.0
    reasons = []

    # Rule 1: High-risk shipment types
    if shipment_type in ["Pharmaceuticals", "Chemicals", "Aerospace Components"]:
        risk_score += 0.3
        reasons.append("High-sensitivity shipment type")

    # Rule 2: Status risk
    if status == "Delayed":
        risk_score += 0.3
        reasons.append("Shipment already delayed")

    # Rule 3: Geographic risk simulation
    high_risk_cities = ["Miami", "Houston", "New York", "Los Angeles"]

    if origin in high_risk_cities or destination in high_risk_cities:
        risk_score += 0.2
        reasons.append("High-risk logistics hub location")

    # Rule 4: Route complexity (simple heuristic)
    if origin != destination:
        risk_score += 0.1

    # Cap score
    risk_score = min(risk_score, 1.0)

    # Final classification
    if risk_score < 0.4:
        risk_level = "LOW"
    elif risk_score < 0.7:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "reasons": reasons,
        "rules_applied": rules
    }