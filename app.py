import io
import os
import smtplib
from email.message import EmailMessage

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from models.shipment_db import get_shipment_by_id
from workflow.graph import build_graph, run_graph



# =========================================================
# REPORT EXPORT HELPERS
# =========================================================

def build_pdf_report(
    shipment,
    risk_level,
    risk_score,
    shipment_risk,
    weather_risk,
    news_risk,
    route_risk_score,
    ai_recommendation,
    ai_confidence,
    final_operational_decision,
    review_outcome,
    decision_authority,
    reviewer_notes,
    executive_summary,
    policy_titles,
    detected_threats,
):
    """
    Builds the executive decision report as PDF bytes.
    """

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title=f"Supply Chain Decision Report - {shipment[0]}",
        author="Supply Chain Disruption Intelligence System",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        spaceAfter=16,
    )

    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=7,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13,
        spaceAfter=6,
    )

    decision_style = ParagraphStyle(
        "Decision",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        spaceAfter=8,
    )

    story = [
        Paragraph(
            "SUPPLY CHAIN EXECUTIVE DECISION REPORT",
            title_style,
        ),
        Paragraph(
            f"Shipment {shipment[0]}",
            styles["Heading3"],
        ),
        Spacer(1, 6),
        Paragraph(
            "Final Operational Decision",
            heading_style,
        ),
        Paragraph(
            str(final_operational_decision).upper(),
            decision_style,
        ),
    ]

    decision_table = Table(
        [
            ["Risk Level", "AI Confidence", "Decision Authority"],
            [
                risk_level,
                f"{ai_confidence * 100:.0f}%",
                decision_authority,
            ],
        ],
        colWidths=[1.75 * inch, 1.75 * inch, 2.55 * inch],
    )

    decision_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EDF3")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAB2BD")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.extend(
        [
            decision_table,
            Spacer(1, 14),
            Paragraph("Shipment Summary", heading_style),
        ]
    )

    shipment_table = Table(
        [
            ["Shipment ID", shipment[0], "Priority", shipment[4]],
            ["Origin", shipment[1], "Destination", shipment[2]],
            ["Cargo", shipment[3], "Status", shipment[5]],
        ],
        colWidths=[
            1.1 * inch,
            2.0 * inch,
            1.0 * inch,
            2.0 * inch,
        ],
    )

    shipment_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F3F4F6")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C7CDD4")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.extend(
        [
            shipment_table,
            Spacer(1, 12),
            Paragraph("Risk Breakdown", heading_style),
        ]
    )

    risk_table = Table(
        [
            ["Category", "Score", "Maximum"],
            ["Shipment Risk", shipment_risk, 35],
            ["Weather Risk", weather_risk, 20],
            ["News Risk", news_risk, 20],
            ["Route Risk", route_risk_score, 25],
            ["Overall Risk", risk_score, 100],
        ],
        colWidths=[3.3 * inch, 1.2 * inch, 1.2 * inch],
    )

    risk_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EDF3")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C7CDD4")),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.extend(
        [
            risk_table,
            Spacer(1, 12),
            Paragraph("Executive Summary", heading_style),
            Paragraph(executive_summary, body_style),
            Paragraph("AI and Human Decision", heading_style),
            Paragraph(
                f"<b>AI Recommendation:</b> {ai_recommendation}<br/>"
                f"<b>Review Outcome:</b> {review_outcome}<br/>"
                f"<b>Final Decision:</b> {final_operational_decision}<br/>"
                f"<b>Reviewer Notes:</b> {reviewer_notes}",
                body_style,
            ),
            Paragraph("Primary Threats", heading_style),
        ]
    )

    if detected_threats:
        for threat in detected_threats:
            story.append(
                Paragraph(
                    f"- {threat}",
                    body_style,
                )
            )
    else:
        story.append(
            Paragraph(
                "- No material disruption threat was identified.",
                body_style,
            )
        )

    story.append(
        Paragraph(
            "Policies Applied",
            heading_style,
        )
    )

    for policy_title in policy_titles:
        story.append(
            Paragraph(
                f"- {policy_title}",
                body_style,
            )
        )

    document.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def send_report_email(
    recipient_email,
    shipment_id,
    final_decision,
    risk_level,
    executive_summary,
    pdf_bytes,
):
    """
    Sends the PDF report using SMTP credentials stored in .env.
    """

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender_email = os.getenv(
        "REPORT_FROM_EMAIL",
        smtp_username or "",
    )

    missing_settings = [
        name
        for name, value in {
            "SMTP_HOST": smtp_host,
            "SMTP_USERNAME": smtp_username,
            "SMTP_PASSWORD": smtp_password,
            "REPORT_FROM_EMAIL": sender_email,
        }.items()
        if not value
    ]

    if missing_settings:
        raise RuntimeError(
            "Missing email settings: "
            + ", ".join(missing_settings)
        )

    message = EmailMessage()
    message["Subject"] = (
        f"Supply Chain Decision Report - {shipment_id}"
    )
    message["From"] = sender_email
    message["To"] = recipient_email

    message.set_content(
        f"""Supply Chain Decision Report

Shipment: {shipment_id}
Final Decision: {final_decision}
Risk Level: {risk_level}

Executive Summary:
{executive_summary}

The full report is attached as a PDF.
"""
    )

    message.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=f"{shipment_id}_decision_report.pdf",
    )

    use_ssl = os.getenv(
        "SMTP_USE_SSL",
        "false",
    ).strip().lower() in {
        "1",
        "true",
        "yes",
    }

    if use_ssl:
        with smtplib.SMTP_SSL(
            smtp_host,
            smtp_port,
            timeout=30,
        ) as smtp_server:
            smtp_server.login(
                smtp_username,
                smtp_password,
            )
            smtp_server.send_message(message)

    else:
        with smtplib.SMTP(
            smtp_host,
            smtp_port,
            timeout=30,
        ) as smtp_server:
            smtp_server.ehlo()
            smtp_server.starttls()
            smtp_server.ehlo()
            smtp_server.login(
                smtp_username,
                smtp_password,
            )
            smtp_server.send_message(message)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Supply Chain Disruption System"
)

st.title("📦 Supply Chain Disruption Intelligence System")
st.write("Enter Shipment ID to retrieve shipment record")


# =========================================================
# BUILD LANGGRAPH APPLICATION
# =========================================================

app = build_graph()


# =========================================================
# SHIPMENT INPUT
# =========================================================

shipment_id = st.text_input(
    "Shipment ID (e.g., SHP001)"
)


search_clicked = st.button("Search Shipment")

if search_clicked:
    normalized_shipment_id = shipment_id.strip().upper()

    if normalized_shipment_id == "":
        st.warning("Please enter a Shipment ID")

    else:
        shipment_record = get_shipment_by_id(
            normalized_shipment_id
        )

        if shipment_record is None:
            st.error("No existing shipment record found.")

        else:
            with st.spinner(
                "Analyzing shipment and external disruption signals..."
            ):
                workflow_result = run_graph(
                    app,
                    normalized_shipment_id,
                )

            st.session_state["active_shipment_id"] = (
                normalized_shipment_id
            )
            st.session_state["active_shipment"] = (
                shipment_record
            )
            st.session_state["analysis_result"] = (
                workflow_result
            )

            # Clear any human decision from an earlier shipment.
            st.session_state.pop("human_review_record", None)

if st.session_state.get("analysis_result") is not None:
    shipment_id = st.session_state.get(
        "active_shipment_id",
        "",
    )

    shipment = st.session_state.get(
        "active_shipment"
    )

    result = st.session_state.get(
        "analysis_result",
        {},
    )

    st.success("Shipment Found")

    # -----------------------------------------------------
    # SHIPMENT DETAILS
    # -----------------------------------------------------

    st.write("### Shipment Details")

    st.write(f"**Shipment ID:** {shipment[0]}")
    st.write(f"**Origin:** {shipment[1]}")
    st.write(f"**Destination:** {shipment[2]}")
    st.write(f"**Shipment Type:** {shipment[3]}")
    st.write(f"**Priority:** {shipment[4]}")
    st.write(f"**Status:** {shipment[5]}")
    # =====================================================
    # ROUTE INTELLIGENCE
    # =====================================================

    st.write("## 🚚 Route Intelligence")

    route = result.get("route")

    if route:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Distance",
                f"{route.get('distance_km', 'N/A')} km"
            )

        with col2:
            st.metric(
                "Travel Time",
                f"{route.get('travel_time_hours', 'N/A')} hrs"
            )

        with col3:
            st.metric(
                "Traffic Delay",
                f"{route.get('traffic_delay_minutes', 'N/A')} min"
            )

        route_risk = route.get(
            "route_risk",
            "Unknown"
        )

        if route_risk == "High":
            st.error(f"Route Risk: {route_risk}")

        elif route_risk == "Medium":
            st.warning(f"Route Risk: {route_risk}")

        elif route_risk == "Low":
            st.success(f"Route Risk: {route_risk}")

        else:
            st.info(f"Route Risk: {route_risk}")

    else:
        st.warning("No route data available")

    # =====================================================
    # RISK ASSESSMENT
    # =====================================================

    st.write("## ⚠️ Risk Assessment")

    risk_level = result.get(
        "risk_level",
        "Unknown"
    )

    risk_score = result.get(
        "risk_score",
        0
    )

    shipment_risk = result.get(
        "shipment_risk",
        0
    )

    weather_risk = result.get(
        "weather_risk",
        0
    )

    news_risk = result.get(
        "news_risk",
        0
    )

    route_risk_score = result.get(
        "route_risk",
        0
    )

    risk_reasons = result.get(
        "risk_reasons",
        []
    )

    primary_concern = result.get(
        "primary_concern",
        "No concern identified."
    )

    operational_impact = result.get(
        "operational_impact",
        {}
    )

    recommended_attention = result.get(
        "recommended_attention",
        "No recommendation available."
    )

    # -----------------------------------------------------
    # OVERALL RISK SUMMARY
    # -----------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Overall Risk Level",
            risk_level
        )

    with col2:
        st.metric(
            "Overall Risk Score",
            f"{risk_score}/100"
        )

    if risk_level == "High":
        st.error(
            "High-risk shipment requiring active attention."
        )

    elif risk_level == "Medium":
        st.warning(
            "Medium-risk shipment requiring continued monitoring."
        )

    elif risk_level == "Low":
        st.success(
            "Low-risk shipment operating within normal conditions."
        )

    else:
        st.info(
            "Risk level is unavailable."
        )

    # -----------------------------------------------------
    # RISK BREAKDOWN
    # -----------------------------------------------------

    st.write("### Risk Breakdown")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Shipment Risk",
            f"{shipment_risk}/35"
        )

    with col2:
        st.metric(
            "Weather Risk",
            f"{weather_risk}/20"
        )

    with col3:
        st.metric(
            "News Risk",
            f"{news_risk}/20"
        )

    with col4:
        st.metric(
            "Route Risk",
            f"{route_risk_score}/25"
        )

    # -----------------------------------------------------
    # DETAILED RISK SCORE EXPLANATION
    # -----------------------------------------------------

    risk_breakdown_details = result.get(
        "risk_breakdown_details",
        {}
    )

    if risk_breakdown_details:
        st.write("### How the Risk Score Was Calculated")

        category_order = [
            "shipment",
            "weather",
            "news",
            "route",
        ]

        for category_key in category_order:
            category = risk_breakdown_details.get(
                category_key,
                {}
            )

            label = category.get(
                "label",
                category_key.title()
            )

            score = category.get(
                "score",
                0
            )

            maximum = category.get(
                "maximum",
                0
            )

            details = category.get(
                "details",
                []
            )

            with st.expander(
                f"{label}: {score}/{maximum}"
            ):
                if details:
                    for detail in details:
                        st.write(f"- {detail}")

                    st.write(
                        f"**Category Total: {score}/{maximum}**"
                    )

                else:
                    st.write(
                        "No scoring details available."
                    )

    else:
        st.info(
            "Detailed risk-score explanations are unavailable."
        )

    # -----------------------------------------------------
    # PRIMARY CONCERN
    # -----------------------------------------------------

    st.write("### Primary Concern")
    st.info(primary_concern)

    # -----------------------------------------------------
    # OPERATIONAL IMPACT
    # -----------------------------------------------------

    st.write("### Operational Impact")

    impact_col1, impact_col2 = st.columns(2)

    with impact_col1:
        st.write(
            f"**Schedule Impact:** "
            f"{operational_impact.get('schedule_impact', 'Unknown')}"
        )

        st.write(
            f"**Delivery Reliability:** "
            f"{operational_impact.get('delivery_reliability', 'Unknown')}"
        )

    with impact_col2:
        st.write(
            f"**Route Stability:** "
            f"{operational_impact.get('route_stability', 'Unknown')}"
        )

        st.write(
            f"**Cargo Exposure:** "
            f"{operational_impact.get('cargo_exposure', 'Unknown')}"
        )

    # -----------------------------------------------------
    # KEY RISK FACTORS
    # -----------------------------------------------------

    if risk_reasons:
        st.write("### Key Risk Factors")

        for number, reason in enumerate(
            risk_reasons,
            start=1
        ):
            st.write(
                f"**{number}.** {reason}"
            )

    else:
        st.info(
            "No significant risk factors identified."
        )

    # -----------------------------------------------------
    # RECOMMENDED ATTENTION
    # -----------------------------------------------------

    st.write("### Recommended Attention")

    if risk_level == "High":
        st.error(recommended_attention)

    elif risk_level == "Medium":
        st.warning(recommended_attention)

    else:
        st.success(recommended_attention)

    # =====================================================
    # RETRIEVED COMPANY POLICIES
    # =====================================================

    st.write("## 📚 Retrieved Company Policies")

    policies = result.get(
        "policies",
        []
    )

    if policies:
        for policy in policies:
            with st.container(border=True):
                st.write(policy)

    else:
        st.info(
            "No relevant company policies were retrieved."
        )

    # =====================================================
    # AGENT 1: DISRUPTION DETECTION
    # =====================================================

    st.write("## 🧠 Disruption Detection Agent")

    disruption = result.get(
        "disruption_assessment",
        {}
    )

    if disruption:
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Assessment Status",
                disruption.get(
                    "status",
                    "Unknown"
                )
            )

        with col2:
            st.metric(
                "Severity",
                disruption.get(
                    "severity",
                    "Unknown"
                )
            )

        st.write("### Analyst Summary")

        st.info(
            disruption.get(
                "summary",
                "No summary available."
            )
        )

        threats = disruption.get(
            "detected_threats",
            []
        )

        if threats:
            st.write("### Detected Threats")

            for threat in threats:
                st.write(f"- {threat}")

        affected_areas = disruption.get(
            "affected_areas",
            []
        )

        if affected_areas:
            st.write("### Affected Areas")
            st.write(", ".join(affected_areas))

        st.write(
            f"**Policies Used:** "
            f"{disruption.get('policy_context_count', 0)}"
        )

    else:
        st.warning(
            "Disruption assessment is unavailable."
        )

    # =====================================================
    # AGENT 2: LOGISTICS DECISION
    # =====================================================

    st.write("## 🚛 Logistics Decision Agent")

    decision = result.get(
        "decision",
        "Unknown"
    )

    confidence = result.get(
        "confidence",
        0
    )

    final_score = result.get(
        "final_score",
        0
    )

    decision_reason = result.get(
        "decision_reason",
        "No decision reason available."
    )

    final_recommendation = result.get(
        "final_recommendation",
        "No final recommendation available."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Decision",
            decision
        )

    with col2:
        st.metric(
            "Confidence",
            f"{confidence * 100:.0f}%"
        )

    with col3:
        st.metric(
            "Decision Score",
            final_score
        )

    st.write("### Decision Reason")

    if decision == "Reroute":
        st.warning(decision_reason)

    elif decision == "Delay":
        st.error(decision_reason)

    elif decision == "Ship":
        st.success(decision_reason)

    else:
        st.info(decision_reason)

    st.write("### Final Recommendation")
    st.info(final_recommendation)

    # =====================================================
    # HUMAN-IN-THE-LOOP APPROVAL
    # =====================================================

    st.write("## 👤 Human Approval")

    approval_status = result.get(
        "approval_status",
        "Unknown",
    )

    human_required = result.get(
        "human_required",
        False,
    )

    ai_decision = result.get(
        "decision",
        "Review",
    )

    review_record = st.session_state.get(
        "human_review_record"
    )

    if not human_required:
        st.success(
            f"Approval Status: {approval_status}"
        )

        st.write(
            f"**Final Approved Decision:** {ai_decision}"
        )

        st.caption(
            "This shipment met the workflow's automatic-approval rules."
        )

    else:
        st.warning(
            "Human review is required before the AI recommendation "
            "can become the final operational decision."
        )

        st.write(
            f"**AI Recommendation:** {ai_decision}"
        )

        with st.form(
            key=f"human_review_form_{shipment_id}"
        ):
            human_action = st.radio(
                "Select Human Decision",
                [
                    "Approve AI Decision",
                    "Override AI Decision",
                    "Reject Shipment",
                ],
            )

            override_decision = None

            if human_action == "Override AI Decision":
                available_decisions = [
                    decision
                    for decision in [
                        "Ship",
                        "Delay",
                        "Reroute",
                    ]
                    if decision != ai_decision
                ]

                override_decision = st.selectbox(
                    "Select Replacement Decision",
                    available_decisions,
                )

            review_notes = st.text_area(
                "Review Notes",
                placeholder=(
                    "Document why the recommendation was approved, "
                    "overridden, or rejected."
                ),
            )

            submitted = st.form_submit_button(
                "Submit Human Decision"
            )

        if submitted:
            if not review_notes.strip():
                st.error(
                    "Review notes are required before submitting "
                    "a human decision."
                )

            else:
                if human_action == "Approve AI Decision":
                    human_status = "Approved"
                    final_decision = ai_decision
                    final_message = (
                        f"AI recommendation approved: {ai_decision}"
                    )

                elif human_action == "Override AI Decision":
                    human_status = "Overridden"
                    final_decision = override_decision
                    final_message = (
                        "AI recommendation overridden. "
                        f"Final decision: {override_decision}"
                    )

                else:
                    human_status = "Rejected"
                    final_decision = "Pending Review"
                    final_message = (
                        "AI recommendation rejected. The shipment is "
                        "pending further operational review."
                    )

                review_record = {
                    "shipment_id": shipment_id,
                    "human_status": human_status,
                    "ai_decision": ai_decision,
                    "final_decision": final_decision,
                    "review_notes": review_notes.strip(),
                }

                st.session_state["human_review_record"] = (
                    review_record
                )

                result["human_decision"] = human_status
                result["final_human_decision"] = final_decision
                result["human_review_notes"] = review_notes.strip()
                result["approval_status"] = (
                    "Human Decision Completed"
                )

                st.session_state["analysis_result"] = result

                if human_status == "Approved":
                    st.success(final_message)

                elif human_status == "Overridden":
                    st.warning(final_message)

                else:
                    st.error(final_message)

        if review_record:
            st.write("### Recorded Human Decision")

            decision_col1, decision_col2 = st.columns(2)

            with decision_col1:
                st.metric(
                    "Review Outcome",
                    review_record.get(
                        "human_status",
                        "Unknown",
                    ),
                )

            with decision_col2:
                st.metric(
                    "Final Decision",
                    review_record.get(
                        "final_decision",
                        "Unknown",
                    ),
                )

            st.write(
                f"**Original AI Recommendation:** "
                f"{review_record.get('ai_decision', 'Unknown')}"
            )

            st.write(
                f"**Reviewer Notes:** "
                f"{review_record.get('review_notes', '')}"
            )

    # =====================================================
    # WEATHER INTELLIGENCE
    # =====================================================

    st.write("## 🌦 Weather Overview")

    weather = result.get("weather")

    if weather:
        col1, col2 = st.columns(2)

        origin_weather = weather.get(
            "origin",
            {}
        )

        destination_weather = weather.get(
            "destination",
            {}
        )

        with col1:
            st.write("### 📍 Origin")

            st.metric(
                "City",
                origin_weather.get(
                    "city",
                    "Unknown"
                )
            )

            st.metric(
                "Condition",
                origin_weather.get(
                    "condition",
                    "N/A"
                )
            )

            st.metric(
                "Temp (°C)",
                origin_weather.get(
                    "temperature_c",
                    "N/A"
                )
            )

        with col2:
            st.write("### 📍 Destination")

            st.metric(
                "City",
                destination_weather.get(
                    "city",
                    "Unknown"
                )
            )

            st.metric(
                "Condition",
                destination_weather.get(
                    "condition",
                    "N/A"
                )
            )

            st.metric(
                "Temp (°C)",
                destination_weather.get(
                    "temperature_c",
                    "N/A"
                )
            )

    else:
        st.warning(
            "No weather data available"
        )

    # =====================================================
    # NEWS INTELLIGENCE
    # =====================================================

    st.write("## 📰 News Intelligence")

    news = result.get("news")

    if news:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Route",
                (
                    f"{news.get('origin', 'N/A')} "
                    f"→ "
                    f"{news.get('destination', 'N/A')}"
                )
            )

        with col2:
            st.metric(
                "Relevant Articles",
                news.get(
                    "event_count",
                    0
                )
            )

        with col3:
            if news.get("risk_flag"):
                st.metric(
                    "News Risk",
                    "Disruption Detected"
                )

            else:
                st.metric(
                    "News Risk",
                    "No Disruption Detected"
                )

        st.write(
            f"**News Source:** "
            f"{news.get('source', 'N/A')}"
        )

        if news.get("search_level"):
            st.write(
                f"**Search Level:** "
                f"{news.get('search_level')}"
            )

        events = news.get(
            "events",
            []
        )

        if events:
            st.write("### Relevant News")

            for event in events:
                with st.container(border=True):
                    st.subheader(
                        event.get(
                            "title",
                            "Untitled Article"
                        )
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(
                            f"**Source:** "
                            f"{event.get('source', 'Unknown')}"
                        )

                    with col2:
                        st.write(
                            f"**Published:** "
                            f"{event.get('date', 'Unknown')}"
                        )

                    description = event.get(
                        "description"
                    )

                    if description:
                        st.write(description)

                    article_url = event.get(
                        "url"
                    )

                    if article_url:
                        st.link_button(
                            "Read Full Article",
                            article_url
                        )

        else:
            st.info(
                "No relevant logistics or supply chain news was found."
            )

    else:
        st.warning(
            "News intelligence is unavailable."
        )

    # =====================================================
    # EXECUTIVE DECISION REPORT
    # =====================================================

    st.write("## 📋 Executive Decision Report")

    human_review_record = st.session_state.get(
        "human_review_record"
    )

    ai_recommendation = result.get(
        "decision",
        "Review",
    )

    ai_confidence = result.get(
        "confidence",
        0.0,
    )

    if human_review_record:
        review_outcome = human_review_record.get(
            "human_status",
            "Completed",
        )

        final_operational_decision = human_review_record.get(
            "final_decision",
            ai_recommendation,
        )

        reviewer_notes = human_review_record.get(
            "review_notes",
            "No reviewer notes were provided.",
        )

        decision_authority = "Human Reviewer"

    elif result.get("human_required", False):
        review_outcome = "Pending Human Review"
        final_operational_decision = "Pending Review"
        reviewer_notes = (
            "A final operational decision cannot be issued until "
            "the required human review is completed."
        )
        decision_authority = "Pending"

    else:
        review_outcome = "Auto Approved"
        final_operational_decision = ai_recommendation
        reviewer_notes = (
            "Human review was not required under the workflow's "
            "automatic-approval rules."
        )
        decision_authority = "Automated Workflow"

    disruption_summary = result.get(
        "disruption_assessment",
        {},
    ) or {}

    detected_threats = disruption_summary.get(
        "detected_threats",
        [],
    )

    policy_titles = []

    for policy_text in policies:
        first_line = str(policy_text).strip().splitlines()[0]

        if not first_line:
            continue

        if len(first_line) > 100:
            first_line = first_line[:97] + "..."

        policy_titles.append(first_line)

    if not policy_titles:
        policy_titles = [
            "No company policy was retrieved for this analysis."
        ]

    weather_summary_parts = []

    if weather:
        origin_weather = weather.get("origin", {})
        destination_weather = weather.get("destination", {})

        weather_summary_parts.append(
            f"{origin_weather.get('city', shipment[1])}: "
            f"{origin_weather.get('condition', 'Unknown')}, "
            f"{origin_weather.get('temperature_c', 'N/A')}°C"
        )

        weather_summary_parts.append(
            f"{destination_weather.get('city', shipment[2])}: "
            f"{destination_weather.get('condition', 'Unknown')}, "
            f"{destination_weather.get('temperature_c', 'N/A')}°C"
        )

    weather_summary = "; ".join(weather_summary_parts)

    news_summary = "No GPT-verified shipment disruption was found."

    if news and news.get("risk_flag"):
        news_summary = (
            f"{news.get('relevant_news_count', news.get('event_count', 0))} "
            "GPT-verified disruption article(s) affected the news-risk score."
        )

    threat_text = (
        ", ".join(detected_threats)
        if detected_threats
        else "no material disruption threats beyond the scored risk factors"
    )

    executive_summary = (
        f"Shipment {shipment[0]} is scheduled to move {shipment[3]} "
        f"from {shipment[1]} to {shipment[2]}. The shipment was assessed "
        f"as {risk_level} risk with an overall score of {risk_score}/100. "
        f"The primary concern is: {primary_concern} "
        f"The assessment identified {threat_text}. "
        f"Weather intelligence shows {weather_summary or 'no weather data available'}. "
        f"{news_summary} The AI logistics agent recommended {ai_recommendation} "
        f"with {ai_confidence * 100:.0f}% confidence. "
        f"The current final operational decision is {final_operational_decision}, "
        f"authorized by {decision_authority}. {recommended_attention}"
    )

    with st.container(border=True):
        st.write("### Final Operational Decision")

        decision_col1, decision_col2, decision_col3 = st.columns(3)

        with decision_col1:
            st.metric(
                "Final Decision",
                final_operational_decision,
            )

        with decision_col2:
            st.metric(
                "Risk Level",
                risk_level,
            )

        with decision_col3:
            st.metric(
                "AI Confidence",
                f"{ai_confidence * 100:.0f}%",
            )

        if final_operational_decision == "Ship":
            st.success(
                "The shipment is cleared to continue under the stated controls."
            )

        elif final_operational_decision == "Delay":
            st.error(
                "The shipment should remain delayed until the identified "
                "conditions are reassessed."
            )

        elif final_operational_decision == "Reroute":
            st.warning(
                "An alternate route should be evaluated before transportation continues."
            )

        else:
            st.warning(
                "The final operational decision is pending additional review."
            )

    st.write("### Shipment and Risk Summary")

    summary_col1, summary_col2 = st.columns(2)

    with summary_col1:
        st.write(f"**Shipment ID:** {shipment[0]}")
        st.write(f"**Route:** {shipment[1]} → {shipment[2]}")
        st.write(f"**Cargo:** {shipment[3]}")
        st.write(f"**Priority:** {shipment[4]}")
        st.write(f"**Shipment Status:** {shipment[5]}")

    with summary_col2:
        st.write(f"**Overall Risk:** {risk_level} ({risk_score}/100)")
        st.write(f"**Shipment Risk:** {shipment_risk}/35")
        st.write(f"**Weather Risk:** {weather_risk}/20")
        st.write(f"**News Risk:** {news_risk}/20")
        st.write(f"**Route Risk:** {route_risk_score}/25")

    st.write("### Executive Summary")
    st.info(executive_summary)

    st.write("### Human Review Status")

    review_col1, review_col2 = st.columns(2)

    with review_col1:
        st.write(f"**Review Outcome:** {review_outcome}")
        st.write(f"**Decision Authority:** {decision_authority}")

    with review_col2:
        st.write(f"**AI Recommendation:** {ai_recommendation}")
        st.write(f"**Final Decision:** {final_operational_decision}")

    st.write(f"**Reviewer Notes:** {reviewer_notes}")

    st.write("### Policies Applied")

    for policy_title in policy_titles:
        st.write(f"- {policy_title}")

    st.write("### Primary Threats")

    if detected_threats:
        for threat in detected_threats:
            st.write(f"- {threat}")
    else:
        st.write("- No material disruption threat was identified.")

    # =====================================================
    # REPORT EXPORT AND EMAIL
    # =====================================================

    st.write("### Report Actions")

    report_ready = (
        not result.get("human_required", False)
        or human_review_record is not None
    )

    pdf_report = None

    if not report_ready:
        st.warning(
            "The final PDF and email report are unavailable until "
            "the required human review is submitted."
        )

        st.caption(
            "Complete the Human Approval section above, then the "
            "report will be regenerated using the recorded final decision."
        )

    else:
        try:
            pdf_report = build_pdf_report(
                shipment=shipment,
                risk_level=risk_level,
                risk_score=risk_score,
                shipment_risk=shipment_risk,
                weather_risk=weather_risk,
                news_risk=news_risk,
                route_risk_score=route_risk_score,
                ai_recommendation=ai_recommendation,
                ai_confidence=ai_confidence,
                final_operational_decision=final_operational_decision,
                review_outcome=review_outcome,
                decision_authority=decision_authority,
                reviewer_notes=reviewer_notes,
                executive_summary=executive_summary,
                policy_titles=policy_titles,
                detected_threats=detected_threats,
            )

        except Exception as report_error:
            st.error(
                "The PDF report could not be generated: "
                f"{report_error}"
            )

    action_col1, action_col2 = st.columns(2)

    with action_col1:
        st.download_button(
            label="Download Final PDF Report",
            data=pdf_report or b"",
            file_name=(
                f"{shipment[0]}_decision_report.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
            disabled=pdf_report is None,
        )

    with action_col2:
        if report_ready:
            st.write(
                "Email the finalized PDF report to a stakeholder."
            )
        else:
            st.write(
                "Email is disabled until human review is completed."
            )

    with st.expander("Send Final Report by Email"):
        recipient_email = st.text_input(
            "Recipient Email Address",
            key=f"report_recipient_{shipment[0]}",
            placeholder="manager@example.com",
            disabled=not report_ready,
        )

        email_button = st.button(
            "Send Final Email Report",
            key=f"send_report_{shipment[0]}",
            disabled=pdf_report is None,
        )

        if email_button:
            if not recipient_email.strip():
                st.error(
                    "Enter a recipient email address."
                )

            elif "@" not in recipient_email:
                st.error(
                    "Enter a valid email address."
                )

            else:
                try:
                    send_report_email(
                        recipient_email=recipient_email.strip(),
                        shipment_id=shipment[0],
                        final_decision=final_operational_decision,
                        risk_level=risk_level,
                        executive_summary=executive_summary,
                        pdf_bytes=pdf_report,
                    )

                    st.success(
                        "The finalized executive decision report "
                        f"was emailed to {recipient_email.strip()}."
                    )

                except Exception as email_error:
                    st.error(
                        "The report could not be emailed. "
                        f"{email_error}"
                    )

    if report_ready and not os.getenv("SMTP_HOST"):
        st.caption(
            "Email sending requires SMTP_HOST, SMTP_PORT, "
            "SMTP_USERNAME, SMTP_PASSWORD, and REPORT_FROM_EMAIL "
            "in the .env file."
        )
