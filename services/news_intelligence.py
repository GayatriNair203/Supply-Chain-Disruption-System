from typing import Any
import json
import os
from math import sqrt

from dotenv import load_dotenv
from openai import OpenAI


# ==========================================================
# ENVIRONMENT AND OPENAI CONFIGURATION
# ==========================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is missing. Add it to your .env file."
    )


client = OpenAI(
    api_key=OPENAI_API_KEY
)

EMBEDDING_MODEL = "text-embedding-3-small"
CLASSIFIER_MODEL = "gpt-4.1-mini"


# ==========================================================
# RELEVANT DISRUPTION TYPES BY SHIPMENT CATEGORY
# ==========================================================

EVENT_MAP = {
    "Pharmaceuticals": [
        "road closure",
        "warehouse disruption",
        "freight delay",
        "cold chain failure",
        "drug shortage",
        "pharmaceutical recall",
        "factory shutdown",
        "power outage",
        "temperature-control failure",
    ],

    "Perishable Food": [
        "road closure",
        "warehouse disruption",
        "freight delay",
        "cold chain failure",
        "food recall",
        "refrigeration failure",
        "port congestion",
        "processing plant shutdown",
    ],

    "Medical Supplies": [
        "road closure",
        "warehouse disruption",
        "freight delay",
        "medical supply shortage",
        "factory shutdown",
        "hospital supply disruption",
        "port congestion",
        "product recall",
    ],

    "Automotive Parts": [
        "factory shutdown",
        "supplier disruption",
        "component shortage",
        "rail disruption",
        "port congestion",
        "truck delay",
        "warehouse disruption",
        "labor strike",
    ],

    "Industrial Machinery": [
        "factory shutdown",
        "equipment shortage",
        "supplier disruption",
        "freight delay",
        "port congestion",
        "rail disruption",
        "warehouse disruption",
        "labor strike",
    ],

    "Electronics": [
        "semiconductor shortage",
        "chip shortage",
        "factory shutdown",
        "supplier disruption",
        "port congestion",
        "freight delay",
        "cyberattack",
        "warehouse disruption",
    ],

    "Consumer Goods": [
        "warehouse disruption",
        "distribution disruption",
        "freight delay",
        "port congestion",
        "retail supply shortage",
        "factory shutdown",
        "labor strike",
        "road closure",
    ],

    "Retail Goods": [
        "warehouse disruption",
        "distribution center closure",
        "freight delay",
        "port congestion",
        "inventory shortage",
        "labor strike",
        "road closure",
        "carrier disruption",
    ],

    "Textiles": [
        "factory shutdown",
        "garment production disruption",
        "supplier disruption",
        "port congestion",
        "freight delay",
        "warehouse disruption",
        "labor strike",
        "material shortage",
    ],

    "Aerospace Components": [
        "supplier shutdown",
        "factory shutdown",
        "component shortage",
        "quality hold",
        "freight delay",
        "port congestion",
        "cyberattack",
        "production disruption",
    ],
}


# ==========================================================
# DEFAULT EVENTS FOR UNKNOWN CATEGORIES
# ==========================================================

DEFAULT_EVENT_TYPES = [
    "road closure",
    "warehouse disruption",
    "freight delay",
    "carrier disruption",
    "factory shutdown",
    "port congestion",
    "rail disruption",
    "labor strike",
    "power outage",
    "severe weather disruption",
]


# ==========================================================
# SHIPMENT PROFILE BUILDER
# ==========================================================

def build_shipment_profile(
    shipment: tuple[Any, ...] | list[Any],
) -> dict:
    """
    Builds a structured shipment profile automatically from
    the shipment record returned by the SQLite database.

    Expected shipment structure:

    index 0: shipment_id
    index 1: origin
    index 2: destination
    index 3: shipment_type
    index 4: priority
    index 5: status
    """

    if not shipment:
        raise ValueError(
            "Shipment data is required to build a shipment profile."
        )

    if len(shipment) < 6:
        raise ValueError(
            "Shipment record must contain at least six fields: "
            "shipment ID, origin, destination, shipment type, "
            "priority, and status."
        )

    shipment_id = str(shipment[0]).strip()
    origin = str(shipment[1]).strip()
    destination = str(shipment[2]).strip()
    shipment_type = str(shipment[3]).strip()
    priority = str(shipment[4]).strip()
    status = str(shipment[5]).strip()

    expected_event_types = EVENT_MAP.get(
        shipment_type,
        DEFAULT_EVENT_TYPES,
    )

    return {
        "shipment_id": shipment_id,
        "origin": origin,
        "destination": destination,
        "shipment_type": shipment_type,
        "priority": priority,
        "status": status,
        "expected_event_types": expected_event_types,
    }


# ==========================================================
# SEMANTIC SEARCH DESCRIPTION BUILDER
# ==========================================================

def build_shipment_search_text(
    shipment_profile: dict,
) -> str:
    """
    Creates a natural-language shipment description that can
    be embedded and compared with news articles.
    """

    origin = shipment_profile.get(
        "origin",
        "Unknown origin",
    )

    destination = shipment_profile.get(
        "destination",
        "Unknown destination",
    )

    shipment_type = shipment_profile.get(
        "shipment_type",
        "Unknown shipment type",
    )

    priority = shipment_profile.get(
        "priority",
        "Unknown",
    )

    status = shipment_profile.get(
        "status",
        "Unknown",
    )

    expected_events = shipment_profile.get(
        "expected_event_types",
        DEFAULT_EVENT_TYPES,
    )

    event_text = ", ".join(expected_events)

    return (
        f"A {priority.lower()}-priority {shipment_type} shipment "
        f"traveling from {origin} to {destination}. "
        f"The shipment status is {status}. "
        f"Relevant news must affect {origin}, {destination}, "
        f"or transportation operations between these locations. "
        f"Relevant operational disruptions include: {event_text}."
    )


# ==========================================================
# ARTICLE TEXT BUILDER
# ==========================================================

def build_article_text(
    article: dict,
) -> str:
    """
    Combines article fields into one string for embeddings.
    """

    title = str(
        article.get("title") or ""
    ).strip()

    description = str(
        article.get("description") or ""
    ).strip()

    content = str(
        article.get("content") or ""
    ).strip()

    source_data = article.get("source") or {}

    if isinstance(source_data, dict):
        source = str(
            source_data.get("name") or ""
        ).strip()
    else:
        source = str(source_data).strip()

    return (
        f"Title: {title}\n"
        f"Source: {source}\n"
        f"Description: {description}\n"
        f"Content: {content}"
    ).strip()


# ==========================================================
# EMBEDDING FUNCTIONS
# ==========================================================

def create_embedding(
    text: str,
) -> list[float]:
    """
    Converts one text value into an OpenAI embedding vector.
    """

    cleaned_text = str(text).strip()

    if not cleaned_text:
        raise ValueError(
            "Text is required to create an embedding."
        )

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=cleaned_text,
    )

    return response.data[0].embedding


def create_embeddings(
    texts: list[str],
) -> list[list[float]]:
    """
    Creates embeddings for multiple texts in one OpenAI request.

    The function preserves the original order of the input list.
    """

    cleaned_texts = [
        str(text).strip()
        for text in texts
    ]

    if not cleaned_texts:
        return []

    if any(
        not text
        for text in cleaned_texts
    ):
        raise ValueError(
            "Every text must contain content before embeddings "
            "can be created."
        )

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=cleaned_texts,
    )

    ordered_items = sorted(
        response.data,
        key=lambda item: item.index,
    )

    return [
        item.embedding
        for item in ordered_items
    ]


# ==========================================================
# COSINE SIMILARITY
# ==========================================================

def cosine_similarity(
    first_embedding: list[float],
    second_embedding: list[float],
) -> float:
    """
    Calculates cosine similarity between two vectors.

    Higher values indicate stronger semantic similarity.
    """

    if not first_embedding or not second_embedding:
        return 0.0

    if len(first_embedding) != len(second_embedding):
        raise ValueError(
            "Embedding vectors must have the same length."
        )

    dot_product = sum(
        first_value * second_value
        for first_value, second_value in zip(
            first_embedding,
            second_embedding,
        )
    )

    first_magnitude = sqrt(
        sum(
            value * value
            for value in first_embedding
        )
    )

    second_magnitude = sqrt(
        sum(
            value * value
            for value in second_embedding
        )
    )

    if first_magnitude == 0 or second_magnitude == 0:
        return 0.0

    return dot_product / (
        first_magnitude * second_magnitude
    )


# ==========================================================
# SEMANTIC ARTICLE RANKING
# ==========================================================

def rank_articles_by_similarity(
    shipment_text: str,
    article_texts: list[str],
) -> list[tuple[int, float]]:
    """
    Returns article indexes ranked from most to least
    semantically similar to the shipment description.
    """

    if not article_texts:
        return []

    shipment_embedding = create_embedding(
        shipment_text
    )

    article_embeddings = create_embeddings(
        article_texts
    )

    similarities = []

    for index, embedding in enumerate(
        article_embeddings
    ):
        score = cosine_similarity(
            shipment_embedding,
            embedding,
        )

        similarities.append(
            (index, score)
        )

    similarities.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return similarities


def compare_article_to_shipment(
    shipment_search_text: str,
    article_text: str,
) -> float:
    """
    Compares one article with one shipment description.
    """

    shipment_embedding = create_embedding(
        shipment_search_text
    )

    article_embedding = create_embedding(
        article_text
    )

    return cosine_similarity(
        shipment_embedding,
        article_embedding,
    )


# ==========================================================
# SAFE DEFAULT CLASSIFICATION
# ==========================================================

def default_classification(
    reason: str,
) -> dict:
    """
    Returns a consistent fallback classification.
    """

    return {
        "relevant": False,
        "confidence": 0.0,
        "location_match": False,
        "category_match": False,
        "operational_disruption": False,
        "event_type": "Unknown",
        "severity": "Low",
        "reason": reason,
    }


# ==========================================================
# LLM RELEVANCE CLASSIFIER
# ==========================================================

def llm_relevance_classifier(
    shipment_profile: dict,
    article: dict,
) -> dict:
    """
    Uses GPT to determine whether an article is operationally
    relevant to a particular shipment.

    An article should be relevant only when it describes a genuine
    operational disruption that could affect the shipment's origin,
    destination, cargo category, or transportation corridor.
    """

    origin = shipment_profile.get(
        "origin",
        "Unknown",
    )

    destination = shipment_profile.get(
        "destination",
        "Unknown",
    )

    shipment_type = shipment_profile.get(
        "shipment_type",
        "Unknown",
    )

    priority = shipment_profile.get(
        "priority",
        "Unknown",
    )

    status = shipment_profile.get(
        "status",
        "Unknown",
    )

    expected_events = shipment_profile.get(
        "expected_event_types",
        DEFAULT_EVENT_TYPES,
    )

    article_title = str(
        article.get("title") or ""
    ).strip()

    article_description = str(
        article.get("description") or ""
    ).strip()

    article_content = str(
        article.get("content") or ""
    ).strip()

    semantic_similarity = article.get(
        "semantic_similarity",
        None,
    )

    prompt = f"""
You are a senior supply-chain risk analyst.

Evaluate whether the news article is operationally relevant to the
shipment described below.

SHIPMENT

Origin: {origin}
Destination: {destination}
Shipment Type: {shipment_type}
Priority: {priority}
Current Status: {status}

Relevant disruption examples:
{", ".join(expected_events)}

NEWS ARTICLE

Title:
{article_title}

Description:
{article_description}

Content:
{article_content}

Semantic similarity score:
{semantic_similarity}

CLASSIFICATION RULES

An article is relevant only when:

1. It describes a real operational disruption, such as a closure,
   delay, outage, strike, shortage, recall, congestion, accident,
   severe weather event, cyberattack, production interruption,
   warehouse problem, transportation problem, or supplier disruption.

2. The disruption affects the shipment origin, destination, cargo
   category, or a transportation corridor that could reasonably affect
   movement between the origin and destination.

3. The article is not merely promotional, financial, political,
   entertainment, sports, investment, partnership, merger, award,
   product-launch, or general business news.

4. A location name alone is not enough. The operational disruption
   must reasonably affect the shipment.

5. A cargo-category word alone is not enough. The article must describe
   a disruption affecting that category or its supply chain.

Return only a JSON object using this structure:

{{
    "relevant": true,
    "confidence": 0.95,
    "location_match": true,
    "category_match": true,
    "operational_disruption": true,
    "event_type": "Warehouse power outage",
    "severity": "Medium",
    "reason": "The article describes a pharmaceutical distribution warehouse outage in the shipment destination."
}}

Severity must be one of:

- Low
- Medium
- High
"""

    try:
        response = client.chat.completions.create(
            model=CLASSIFIER_MODEL,
            temperature=0,
            response_format={
                "type": "json_object"
            },
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You classify shipment-specific logistics "
                        "and supply-chain disruption news."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

    except Exception as error:
        return default_classification(
            f"OpenAI classification failed: {error}"
        )

    content = response.choices[0].message.content

    if not content:
        return default_classification(
            "The model returned an empty response."
        )

    try:
        result = json.loads(content)

    except json.JSONDecodeError:
        return default_classification(
            "The model response was not valid JSON."
        )

    relevant = bool(
        result.get(
            "relevant",
            False,
        )
    )

    try:
        confidence = float(
            result.get(
                "confidence",
                0.0,
            )
        )

    except (TypeError, ValueError):
        confidence = 0.0

    confidence = min(
        max(confidence, 0.0),
        1.0,
    )

    location_match = bool(
        result.get(
            "location_match",
            False,
        )
    )

    category_match = bool(
        result.get(
            "category_match",
            False,
        )
    )

    operational_disruption = bool(
        result.get(
            "operational_disruption",
            False,
        )
    )

    event_type = str(
        result.get(
            "event_type",
            "Unknown",
        )
    ).strip()

    severity = str(
        result.get(
            "severity",
            "Low",
        )
    ).strip().title()

    if severity not in {
        "Low",
        "Medium",
        "High",
    }:
        severity = "Low"

    reason = str(
        result.get(
            "reason",
            "No explanation was provided.",
        )
    ).strip()

    # A result cannot be considered relevant without an
    # operational disruption.
    if not operational_disruption:
        relevant = False

    return {
        "relevant": relevant,
        "confidence": confidence,
        "location_match": location_match,
        "category_match": category_match,
        "operational_disruption": operational_disruption,
        "event_type": event_type or "Unknown",
        "severity": severity,
        "reason": reason,
    }