import os


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

POLICY_FILE_PATH = os.path.join(
    BASE_DIR,
    "knowledge_base",
    "company_policies.txt"
)


def load_policies():
    if not os.path.exists(POLICY_FILE_PATH):
        print(
            f"Policy file not found: {POLICY_FILE_PATH}"
        )
        return []

    with open(
        POLICY_FILE_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        content = file.read()

    policy_blocks = content.split("\n\n")

    policies = []

    for block in policy_blocks:
        block = block.strip()

        if block.startswith("POLICY"):
            policies.append(block)

    return policies


def retrieve_relevant_policies(state):
    policies = load_policies()

    if not policies:
        return []

    shipment = state.get("shipment")
    weather = state.get("weather") or {}
    news = state.get("news") or {}
    route = state.get("route") or {}

    risk_level = state.get(
        "risk_level",
        "Unknown"
    )

    if shipment is None:
        return []

    shipment_type = shipment[3]
    priority = shipment[4]
    shipment_status = shipment[5]

    relevant_policy_numbers = set()


    # High-priority shipment policy
    if priority == "High":
        relevant_policy_numbers.add(1)


    # Delayed shipment policy
    if shipment_status == "Delayed":
        relevant_policy_numbers.add(2)


    # Sensitive cargo policy
    sensitive_types = [
        "Pharmaceuticals",
        "Perishable Food",
        "Medical Supplies",
        "Aerospace Components",
    ]

    if shipment_type in sensitive_types:
        relevant_policy_numbers.add(3)


    # Weather disruption policy
    severe_weather_keywords = [
        "heavy rain",
        "thunder",
        "storm",
        "snow",
        "hurricane",
        "tornado",
        "flood",
        "freezing",
    ]

    for location in [
        "origin",
        "destination"
    ]:

        weather_data = weather.get(
            location,
            {}
        )

        condition = str(
            weather_data.get(
                "condition",
                ""
            )
        ).lower()

        temperature = weather_data.get(
            "temperature_c",
            0
        )

        if any(
            keyword in condition
            for keyword in severe_weather_keywords
        ):
            relevant_policy_numbers.add(4)

        if temperature >= 40:
            relevant_policy_numbers.add(4)


    # Route risk policy
    route_level = route.get(
        "route_risk",
        "Unknown"
    )

    traffic_delay = route.get(
        "traffic_delay_minutes",
        0
    )

    if route_level in [
        "Medium",
        "High"
    ]:
        relevant_policy_numbers.add(5)

    if traffic_delay >= 20:
        relevant_policy_numbers.add(5)


    # News disruption policy
    if news.get("risk_flag"):
        relevant_policy_numbers.add(6)


    # Auto-approval policy
    relevant_policy_numbers.add(7)


    # Rerouting policy
    if (
        route_level == "High"
        or traffic_delay >= 60
    ):
        relevant_policy_numbers.add(8)


    # Delay recommendation policy
    if (
        shipment_status == "Delayed"
        or risk_level == "High"
    ):
        relevant_policy_numbers.add(9)


    # Ship recommendation policy
    if risk_level in [
        "Low",
        "Medium"
    ]:
        relevant_policy_numbers.add(10)


    matched_policies = []

    for policy in policies:

        for policy_number in sorted(
            relevant_policy_numbers
        ):

            policy_prefix = (
                f"POLICY {policy_number}:"
            )

            if policy.startswith(
                policy_prefix
            ):
                matched_policies.append(
                    policy
                )

                break


    return matched_policies