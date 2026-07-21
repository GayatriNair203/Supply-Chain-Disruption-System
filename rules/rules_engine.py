RULES = {
    "Pharmaceuticals": {
        "max_delay_hours": 12,
        "risk_threshold": 0.5,
        "requires_human_approval": True
    },

    "Perishable Food": {
        "max_delay_hours": 6,
        "risk_threshold": 0.4,
        "requires_human_approval": True
    },

    "Electronics": {
        "max_delay_hours": 48,
        "risk_threshold": 0.7,
        "requires_human_approval": False
    },

    "Automotive Parts": {
        "max_delay_hours": 72,
        "risk_threshold": 0.65,
        "requires_human_approval": False
    },

    "Industrial Machinery": {
        "max_delay_hours": 120,
        "risk_threshold": 0.7,
        "requires_human_approval": True
    },

    "Chemicals": {
        "max_delay_hours": 0,
        "risk_threshold": 0.3,
        "requires_human_approval": True
    },

    "Retail Goods": {
        "max_delay_hours": 72,
        "risk_threshold": 0.75,
        "requires_human_approval": False
    },

    "Aerospace Components": {
        "max_delay_hours": 24,
        "risk_threshold": 0.5,
        "requires_human_approval": True
    }
}


def get_rules(shipment_type: str):
    return RULES.get(shipment_type, {
        "max_delay_hours": 48,
        "risk_threshold": 0.6,
        "requires_human_approval": True
    })