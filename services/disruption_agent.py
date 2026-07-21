def generate_disruption_assessment(state):
    shipment = state.get("shipment")
    weather = state.get("weather") or {}
    news = state.get("news") or {}
    route = state.get("route") or {}
    policies = state.get("policies") or []

    risk_level = state.get("risk_level", "Unknown")
    risk_score = state.get("risk_score", 0)
    risk_reasons = state.get("risk_reasons", [])
    primary_concern = state.get("primary_concern", "No primary concern identified.")

    if shipment is None:
        return {
            "status": "Unavailable",
            "severity": "Unknown",
            "summary": "Shipment information is unavailable, so disruption assessment cannot be completed.",
            "detected_threats": [],
            "affected_areas": [],
            "policy_context_count": 0,
        }

    origin = shipment[1]
    destination = shipment[2]
    shipment_type = shipment[3]
    priority = shipment[4]
    shipment_status = shipment[5]

    detected_threats = []
    affected_areas = []

    if shipment_status == "Delayed":
        detected_threats.append("Existing shipment delay")
        affected_areas.append("Schedule reliability")

    if news.get("risk_flag"):
        detected_threats.append("External disruption signals from news intelligence")
        affected_areas.append("Route environment")

    if route.get("route_risk") in ["Medium", "High"]:
        detected_threats.append(f"{route.get('route_risk')} route transportation risk")
        affected_areas.append("Transportation corridor")

    for location in ["origin", "destination"]:
        weather_data = weather.get(location, {})
        condition = str(weather_data.get("condition", "")).lower()
        temp = weather_data.get("temperature_c", 0)

        if any(word in condition for word in ["heavy rain", "storm", "snow", "hurricane", "tornado", "flood"]):
            detected_threats.append(
                f"Severe weather at {location}: {weather_data.get('condition')}"
            )
            affected_areas.append(location)

        if temp >= 40:
            detected_threats.append(
                f"Extreme heat at {location}: {temp}°C"
            )
            affected_areas.append(location)

    if not detected_threats:
        detected_threats.append("No major disruption threat detected")

    affected_areas = list(set(affected_areas))

    if risk_level == "High":
        severity = "High"
        status = "Active Disruption Review Needed"
    elif risk_level == "Medium":
        severity = "Medium"
        status = "Monitor Conditions"
    elif risk_level == "Low":
        severity = "Low"
        status = "Normal Monitoring"
    else:
        severity = "Unknown"
        status = "Assessment Incomplete"

    summary = (
        f"Shipment from {origin} to {destination} carrying {shipment_type} is assessed as "
        f"{risk_level} risk with a score of {risk_score}/100. "
        f"Primary concern: {primary_concern}"
    )

    return {
        "status": status,
        "severity": severity,
        "summary": summary,
        "detected_threats": detected_threats,
        "affected_areas": affected_areas,
        "policy_context_count": len(policies),
        "risk_reasons_used": risk_reasons,
        "shipment_context": {
            "origin": origin,
            "destination": destination,
            "shipment_type": shipment_type,
            "priority": priority,
            "status": shipment_status,
        },
    }