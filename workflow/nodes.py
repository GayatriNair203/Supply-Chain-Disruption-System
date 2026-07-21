import os

from models.shipment_db import get_shipment_by_id
from services.weather_tool import get_weather
from services.news_tool import get_news_data
from services.route_tool import get_route_data
from services.policy_retriever import retrieve_relevant_policies
from services.disruption_agent import generate_disruption_assessment
from services.logistics_decision_agent import generate_logistics_decision


NEWS_API_KEY = os.getenv("NEWS_API_KEY")


def shipment_lookup_node(state):
    shipment = get_shipment_by_id(state["shipment_id"])

    if shipment is None:
        state["shipment"] = None
        state["workflow_status"] = "Shipment Not Found"
        return state

    state["shipment"] = shipment
    state["workflow_status"] = "Shipment Loaded"

    return state


def weather_node(state):
    shipment = state.get("shipment")

    if shipment is None:
        state["weather"] = None
        state["workflow_status"] = "Weather Unavailable"
        return state

    origin = shipment[1]
    destination = shipment[2]

    state["weather"] = {
        "origin": get_weather(origin),
        "destination": get_weather(destination),
    }

    state["workflow_status"] = "Weather Loaded"

    return state


def news_node(state):
    shipment = state.get("shipment")

    if shipment is None:
        state["news"] = None
        state["relevant_news_count"] = 0
        state["ignored_news_count"] = 0
        state["news_assessments"] = []
        state["workflow_status"] = "News Unavailable"
        return state

    origin = shipment[1]
    destination = shipment[2]
    shipment_type = shipment[3]
    priority = shipment[4]
    shipment_status = shipment[5]

    news_data = get_news_data(
        origin=origin,
        destination=destination,
        shipment_type=shipment_type,
        api_key=NEWS_API_KEY,
        priority=priority,
        status=shipment_status,
    )

    state["news"] = news_data

    state["relevant_news_count"] = news_data.get(
        "relevant_news_count",
        0,
    )

    state["ignored_news_count"] = news_data.get(
        "ignored_news_count",
        0,
    )

    state["news_assessments"] = news_data.get(
        "news_assessments",
        [],
    )

    state["workflow_status"] = "News Loaded"

    return state


def route_node(state):
    shipment = state.get("shipment")

    if shipment is None:
        state["route"] = None
        state["workflow_status"] = "Route Unavailable"
        return state

    origin = shipment[1]
    destination = shipment[2]

    state["route"] = get_route_data(
        origin,
        destination,
    )

    state["workflow_status"] = "Route Loaded"

    return state


def risk_assessment_node(state):
    shipment = state.get("shipment")
    weather = state.get("weather") or {}
    news = state.get("news") or {}
    route = state.get("route") or {}

    if shipment is None:
        state["shipment_risk"] = 0
        state["weather_risk"] = 0
        state["news_risk"] = 0
        state["route_risk"] = 0

        state["risk_score"] = 0
        state["risk_level"] = "Unknown"

        state["risk_reasons"] = [
            "Shipment data is unavailable."
        ]

        state["risk_breakdown_details"] = {
            "shipment": {
                "label": "Shipment Risk",
                "score": 0,
                "maximum": 35,
                "details": [
                    "Shipment information unavailable: +0 points"
                ],
            },
            "weather": {
                "label": "Weather Risk",
                "score": 0,
                "maximum": 20,
                "details": [
                    "Weather information unavailable: +0 points"
                ],
            },
            "news": {
                "label": "News Risk",
                "score": 0,
                "maximum": 20,
                "details": [
                    "News intelligence unavailable: +0 points"
                ],
            },
            "route": {
                "label": "Route Risk",
                "score": 0,
                "maximum": 25,
                "details": [
                    "Route information unavailable: +0 points"
                ],
            },
        }

        state["primary_concern"] = (
            "Shipment information is unavailable."
        )

        state["operational_impact"] = {
            "schedule_impact": "Unknown",
            "delivery_reliability": "Unknown",
            "route_stability": "Unknown",
            "cargo_exposure": "Unknown",
        }

        state["recommended_attention"] = (
            "Manual review is required because the shipment "
            "record could not be assessed."
        )

        state["workflow_status"] = "Risk Assessment Failed"

        return state

    shipment_type = shipment[3]
    priority = shipment[4]
    shipment_status = shipment[5]

    shipment_risk = 0
    weather_risk = 0
    news_risk = 0
    route_risk_score = 0

    risk_reasons = []

    shipment_details = []
    weather_details = []
    news_details = []
    route_details = []

    # =====================================================
    # SHIPMENT RISK — MAXIMUM 35
    # =====================================================

    if priority == "High":
        shipment_risk += 15

        shipment_details.append(
            "High business priority: +15 points"
        )

        risk_reasons.append(
            "High-priority shipment increases business impact."
        )

    elif priority == "Medium":
        shipment_risk += 8

        shipment_details.append(
            "Medium business priority: +8 points"
        )

        risk_reasons.append(
            "Medium-priority shipment creates moderate "
            "business exposure."
        )

    else:
        shipment_details.append(
            "Low business priority: +0 points"
        )

    if shipment_status == "Delayed":
        shipment_risk += 15

        shipment_details.append(
            "Shipment already delayed: +15 points"
        )

        risk_reasons.append(
            "Shipment is already delayed."
        )

    elif shipment_status == "In Transit":
        shipment_risk += 5

        shipment_details.append(
            "Shipment currently in transit: +5 points"
        )

    else:
        shipment_details.append(
            f"Shipment status is {shipment_status}: +0 points"
        )

    sensitive_types = [
        "Pharmaceuticals",
        "Perishable Food",
        "Medical Supplies",
        "Aerospace Components",
    ]

    if shipment_type in sensitive_types:
        shipment_risk += 5

        shipment_details.append(
            f"Sensitive cargo ({shipment_type}): +5 points"
        )

        risk_reasons.append(
            f"{shipment_type} requires closer handling "
            "and delivery control."
        )

    else:
        shipment_details.append(
            f"Standard cargo category ({shipment_type}): "
            "+0 points"
        )

    shipment_risk = min(
        shipment_risk,
        35,
    )

    # =====================================================
    # WEATHER RISK — MAXIMUM 20
    # =====================================================

    severe_weather = [
        "heavy rain",
        "thunder",
        "storm",
        "snow",
        "hurricane",
        "tornado",
        "flood",
    ]

    moderate_weather = [
        "rain",
        "dust",
        "haze",
        "fog",
        "wind",
    ]

    for location in ["origin", "destination"]:
        weather_data = weather.get(
            location,
            {},
        )

        condition = str(
            weather_data.get(
                "condition",
                "",
            )
        ).lower()

        temperature = weather_data.get(
            "temperature_c",
            0,
        )

        display_location = location.capitalize()

        display_condition = weather_data.get(
            "condition",
            "Unknown",
        )

        if any(
            keyword in condition
            for keyword in severe_weather
        ):
            weather_risk += 10

            weather_details.append(
                f"{display_location} severe weather "
                f"({display_condition}): +10 points"
            )

            risk_reasons.append(
                f"Severe weather at {location}: "
                f"{display_condition}."
            )

        elif any(
            keyword in condition
            for keyword in moderate_weather
        ):
            weather_risk += 5

            weather_details.append(
                f"{display_location} moderate weather "
                f"({display_condition}): +5 points"
            )

            risk_reasons.append(
                f"Moderate weather concern at {location}: "
                f"{display_condition}."
            )

        else:
            weather_details.append(
                f"{display_location} weather "
                f"({display_condition}): +0 points"
            )

        if temperature >= 40:
            weather_risk += 5

            weather_details.append(
                f"{display_location} extreme heat "
                f"({temperature}°C): +5 points"
            )

            risk_reasons.append(
                f"Extreme heat detected at {location}: "
                f"{temperature}°C."
            )

    weather_risk = min(
        weather_risk,
        20,
    )
    # =====================================================
    # NEWS RISK — MAXIMUM 20
    # =====================================================

    news_risk = news.get("risk_score", 0)
    news_risk = min(max(news_risk, 0), 20)

    relevant_news_count = news.get("relevant_news_count", 0)
    ignored_news_count = news.get("ignored_news_count", 0)
    search_level = news.get("search_level", "Unknown")
    news_assessments = news.get("news_assessments", [])

    if news_risk > 0:
        risk_reasons.append(
            f"{relevant_news_count} directly relevant operational "
            f"disruption article(s) contributed {news_risk} news-risk points."
        )

        news_details.append(
            f"{relevant_news_count} directly relevant disruption "
            f"article(s): +{news_risk} points"
        )

        relevant_assessments = [
            assessment
            for assessment in news_assessments
            if assessment.get("is_disruption")
        ]

        for assessment in relevant_assessments[:5]:
            title = assessment.get("title", "Untitled Article")
            severity = assessment.get("severity", "Unknown")
            article_points = assessment.get("risk_points", 0)

            news_details.append(
                f"{severity} disruption — {title}: "
                f"+{article_points} points"
            )

        if news_risk >= 15:
            risk_reasons.append(
                "News intelligence indicates substantial external "
                "disruption exposure."
            )
        else:
            risk_reasons.append(
                "News intelligence indicates potential external "
                "disruption exposure."
            )

    else:
        news_details.append(
            "No GPT-verified shipment disruption articles were found "
            "(+0 points)."
        )

    if ignored_news_count > 0:
        news_details.append(
            f"{ignored_news_count} unrelated or non-operational "
            "article(s) were ignored."
        )

    news_details.append(
        f"News search level: {search_level}"
    )

    # =====================================================
    # ROUTE RISK — MAXIMUM 25
    # =====================================================

    route_level = route.get(
        "route_risk",
        "Unknown",
    )

    traffic_delay = route.get(
        "traffic_delay_minutes",
        0,
    )

    distance = route.get(
        "distance_km",
        0,
    )

    if route_level == "High":
        route_risk_score += 15

        route_details.append(
            "High route risk classification: +15 points"
        )

        risk_reasons.append(
            "Route analysis indicates high transportation risk."
        )

    elif route_level == "Medium":
        route_risk_score += 10

        route_details.append(
            "Medium route risk classification: +10 points"
        )

        risk_reasons.append(
            "Route analysis indicates moderate "
            "transportation risk."
        )

    elif route_level == "Low":
        route_risk_score += 3

        route_details.append(
            "Low route risk classification: +3 points"
        )

    else:
        route_details.append(
            "Route risk classification unavailable: +0 points"
        )

    if traffic_delay >= 60:
        route_risk_score += 7

        route_details.append(
            f"Traffic delay ({traffic_delay:.1f} minutes): "
            "+7 points"
        )

        risk_reasons.append(
            f"High traffic delay detected: "
            f"{traffic_delay:.1f} minutes."
        )

    elif traffic_delay >= 20:
        route_risk_score += 4

        route_details.append(
            f"Traffic delay ({traffic_delay:.1f} minutes): "
            "+4 points"
        )

        risk_reasons.append(
            f"Moderate traffic delay detected: "
            f"{traffic_delay:.1f} minutes."
        )

    else:
        route_details.append(
            f"Traffic delay ({traffic_delay:.1f} minutes): "
            "+0 points"
        )

    if distance >= 1500:
        route_risk_score += 3

        route_details.append(
            f"Long-distance shipment "
            f"({distance:.1f} km): +3 points"
        )

    elif distance >= 900:
        route_risk_score += 2

        route_details.append(
            f"Medium-distance shipment "
            f"({distance:.1f} km): +2 points"
        )

    else:
        route_details.append(
            f"Short-distance shipment "
            f"({distance:.1f} km): +0 points"
        )

    route_risk_score = min(
        route_risk_score,
        25,
    )

    # =====================================================
    # FINAL RISK SCORE
    # =====================================================

    total_risk = (
        shipment_risk
        + weather_risk
        + news_risk
        + route_risk_score
    )

    if total_risk >= 70:
        risk_level = "High"

    elif total_risk >= 40:
        risk_level = "Medium"

    else:
        risk_level = "Low"

    # =====================================================
    # PRIMARY CONCERN
    # =====================================================

    if shipment_status == "Delayed":
        primary_concern = (
            "Shipment is already delayed, increasing schedule "
            "and customer-service risk."
        )

    elif weather_risk >= 10:
        primary_concern = (
            "Weather conditions may affect shipment reliability."
        )

    elif route_risk_score >= 15:
        primary_concern = (
            "Route conditions create significant transportation "
            "exposure."
        )

    elif news_risk >= 10:
        primary_concern = (
            "External disruption signals may affect route "
            "or shipment reliability."
        )

    elif route_risk_score >= 10:
        primary_concern = (
            "Route conditions create moderate transportation "
            "exposure."
        )

    else:
        primary_concern = (
            "No major disruption driver detected."
        )

    # =====================================================
    # OPERATIONAL IMPACT
    # =====================================================

    operational_impact = {
        "schedule_impact": (
            "High"
            if shipment_status == "Delayed"
            else "Medium"
            if total_risk >= 40
            else "Low"
        ),
        "delivery_reliability": (
            "At Risk"
            if total_risk >= 70
            else "Moderate"
            if total_risk >= 40
            else "Stable"
        ),
        "route_stability": route_level,
        "cargo_exposure": (
            "High"
            if shipment_type in sensitive_types
            else "Moderate"
            if priority in ["High", "Medium"]
            else "Low"
        ),
    }

    # =====================================================
    # RECOMMENDED ATTENTION
    # =====================================================

    if risk_level == "High":
        recommended_attention = (
            "Shipment requires active monitoring and review "
            "before continuing normal execution."
        )

    elif risk_level == "Medium":
        recommended_attention = (
            "Shipment should continue only with monitoring of "
            "route, weather, cargo conditions, and verified "
            "external disruption signals."
        )

    else:
        recommended_attention = (
            "Shipment can continue under normal operating "
            "procedures."
        )

    # =====================================================
    # DETAILED RISK BREAKDOWN
    # =====================================================

    risk_breakdown_details = {
        "shipment": {
            "label": "Shipment Risk",
            "score": shipment_risk,
            "maximum": 35,
            "details": shipment_details,
        },
        "weather": {
            "label": "Weather Risk",
            "score": weather_risk,
            "maximum": 20,
            "details": weather_details,
        },
        "news": {
            "label": "News Risk",
            "score": news_risk,
            "maximum": 20,
            "details": news_details,
        },
        "route": {
            "label": "Route Risk",
            "score": route_risk_score,
            "maximum": 25,
            "details": route_details,
        },
    }

    # =====================================================
    # SAVE RESULTS TO STATE
    # =====================================================

    state["shipment_risk"] = shipment_risk
    state["weather_risk"] = weather_risk
    state["news_risk"] = news_risk
    state["route_risk"] = route_risk_score

    state["risk_score"] = total_risk
    state["risk_level"] = risk_level
    state["risk_reasons"] = risk_reasons

    state["risk_breakdown_details"] = (
        risk_breakdown_details
    )

    state["primary_concern"] = primary_concern
    state["operational_impact"] = operational_impact
    state["recommended_attention"] = recommended_attention

    state["relevant_news_count"] = relevant_news_count
    state["ignored_news_count"] = ignored_news_count
    state["news_assessments"] = news_assessments

    state["workflow_status"] = "Risk Assessment Complete"

    return state


def policy_retrieval_node(state):
    policies = retrieve_relevant_policies(state)

    state["policies"] = policies
    state["workflow_status"] = "Policies Retrieved"

    return state


def disruption_detection_node(state):
    assessment = generate_disruption_assessment(state)

    state["disruption_assessment"] = assessment
    state["workflow_status"] = (
        "Disruption Assessment Complete"
    )

    return state


def logistics_decision_node(state):
    decision_result = generate_logistics_decision(state)

    state["decision"] = decision_result.get(
        "decision",
        "Review",
    )

    state["confidence"] = decision_result.get(
        "confidence",
        0.0,
    )

    state["final_score"] = decision_result.get(
        "final_score",
        state.get("risk_score", 0),
    )

    state["decision_reason"] = decision_result.get(
        "decision_reason",
        "No decision reason available.",
    )

    state["final_recommendation"] = decision_result.get(
        "final_recommendation",
        "Manual logistics review is required.",
    )

    state["workflow_status"] = (
        "Logistics Decision Complete"
    )

    return state


def approval_routing_node(state):
    risk_level = state.get(
        "risk_level",
        "Unknown",
    )

    route = state.get("route") or {}
    weather_risk = state.get("weather_risk", 0)
    shipment = state.get("shipment")

    route_level = route.get(
        "route_risk",
        "Unknown",
    )

    shipment_status = (
        shipment[5]
        if shipment
        else "Unknown"
    )

    requires_human_review = (
        risk_level == "High"
        or route_level == "High"
        or weather_risk >= 10
        or shipment_status == "Delayed"
    )

    if requires_human_review:
        state["approval_status"] = (
            "Human Review Required"
        )

        state["human_required"] = True
        state["human_decision"] = None
        state["workflow_status"] = (
            "Awaiting Human Review"
        )

    else:
        state["approval_status"] = "Auto Approved"
        state["human_required"] = False
        state["human_decision"] = "Approved"
        state["workflow_status"] = "Auto Approved"

    return state

def auto_approval_node(state):
    """
    Automatically approves Low- and Medium-risk shipments.
    """

    state["approval_status"] = "Auto Approved"
    state["human_required"] = False
    state["human_decision"] = "Approved"
    state["workflow_status"] = "Auto Approved"

    return state


def human_review_node(state):
    """
    Pauses High-risk shipments for human review.
    The user's decision will later be collected in Streamlit.
    """

    state["approval_status"] = "Human Review Required"
    state["human_required"] = True
    state["human_decision"] = None
    state["workflow_status"] = "Awaiting Human Review"

    return state