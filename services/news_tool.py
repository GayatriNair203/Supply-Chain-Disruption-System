import re
from typing import Any

import requests

from services.news_intelligence import (
    build_article_text,
    build_shipment_profile,
    build_shipment_search_text,
    llm_relevance_classifier,
    rank_articles_by_similarity,
)


# ==========================================================
# CONFIGURATION
# ==========================================================

NEWS_API_URL = "https://newsapi.org/v2/everything"

MAX_CANDIDATE_ARTICLES = 100
MAX_SEMANTIC_ARTICLES = 10
MAX_CLASSIFIED_ARTICLES = 10
MAX_DISPLAYED_ARTICLES = 5

MAX_NEWS_RISK_SCORE = 20

# The classifier must be at least this confident before an
# article can affect shipment risk.
MIN_CLASSIFIER_CONFIDENCE = 0.70

# Embedding similarity is primarily used for ranking.
# Very weak semantic matches are discarded before GPT analysis.
MIN_SEMANTIC_SIMILARITY = 0.20


# ==========================================================
# SHIPMENT CATEGORY SEARCH TERMS
# ==========================================================

SHIPMENT_TYPE_SEARCH_TERMS = {
    "Pharmaceuticals": [
        "pharmaceutical",
        "pharmaceuticals",
        "medicine",
        "drug",
        "drug manufacturing",
        "pharmaceutical distribution",
        "pharmaceutical supply chain",
        "cold chain",
    ],

    "Perishable Food": [
        "perishable food",
        "food distribution",
        "food supply chain",
        "cold chain",
        "refrigerated food",
        "food processing",
        "meat processing",
        "produce distribution",
    ],

    "Medical Supplies": [
        "medical supplies",
        "medical equipment",
        "healthcare supplies",
        "hospital supplies",
        "medical supply chain",
        "healthcare logistics",
    ],

    "Automotive Parts": [
        "automotive parts",
        "auto parts",
        "vehicle parts",
        "automotive supply chain",
        "automotive manufacturing",
        "vehicle production",
    ],

    "Industrial Machinery": [
        "industrial machinery",
        "industrial equipment",
        "manufacturing equipment",
        "heavy equipment",
        "machinery supply chain",
    ],

    "Electronics": [
        "electronics",
        "electronic components",
        "semiconductor",
        "semiconductors",
        "computer components",
        "electronics supply chain",
    ],

    "Consumer Goods": [
        "consumer goods",
        "consumer products",
        "consumer supply chain",
        "retail distribution",
        "consumer logistics",
    ],

    "Retail Goods": [
        "retail goods",
        "retail products",
        "retail supply chain",
        "retail logistics",
        "distribution center",
    ],

    "Textiles": [
        "textiles",
        "textile",
        "apparel",
        "garment",
        "textile supply chain",
        "garment manufacturing",
    ],

    "Aerospace Components": [
        "aerospace components",
        "aerospace parts",
        "aircraft parts",
        "aviation components",
        "aerospace supply chain",
        "aircraft manufacturing",
    ],
}


# ==========================================================
# DISRUPTION SEARCH TERMS
# ==========================================================

DISRUPTION_SEARCH_TERMS = [
    "closure",
    "closed",
    "shutdown",
    "fire",
    "delay",
    "delayed",
    "disruption",
    "outage",
    "strike",
    "shortage",
    "recall",
    "congestion",
    "accident",
    "flood",
    "flooding",
    "hurricane",
    "tornado",
    "wildfire",
    "earthquake",
    "cyberattack",
    "ransomware",
    "operations suspended",
    "production halted",
    "road closure",
    "rail disruption",
    "port disruption",
    "warehouse disruption",
    "freight disruption",
    "shipping disruption",
]


# ==========================================================
# CONTENT THAT SHOULD BE EXCLUDED EARLY
# ==========================================================

IGNORE_TERMS = [
    # Sports
    "nba",
    "nfl",
    "mlb",
    "wnba",
    "nhl",
    "football",
    "basketball",
    "baseball",
    "soccer",
    "playoffs",
    "championship",
    "red sox",
    "dodgers",
    "astros",
    "mets",

    # Entertainment
    "celebrity",
    "movie",
    "music",
    "concert",
    "wedding",
    "taylor swift",
    "travis kelce",

    # Investor and financial notices
    "earnings call",
    "conference call",
    "quarterly results",
    "investor alert",
    "shareholder alert",
    "securities lawsuit",
    "class action lawsuit",
    "lead plaintiff",
    "stock price",

    # Routine promotional announcements
    "award",
    "awards",
    "recognition",
    "strategic partnership",
    "new partnership",
    "appoints",
    "product launch",
    "general availability",

    # Shopping
    "coupon",
    "shopping deal",
    "free shipping",
    "sale price",
    "slickdeals",
]


# ==========================================================
# BASIC TEXT HELPERS
# ==========================================================

def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def contains_phrase(
    text: str,
    phrase: str,
) -> bool:
    if not text or not phrase:
        return False

    pattern = (
        r"(?<!\w)"
        + re.escape(phrase.lower())
        + r"(?!\w)"
    )

    return re.search(
        pattern,
        text.lower(),
    ) is not None


def contains_any(
    text: str,
    terms: list[str],
) -> bool:
    return any(
        contains_phrase(text, term)
        for term in terms
    )


def get_article_text(
    article: dict,
) -> str:
    """
    Returns searchable article text.
    """

    title = normalize_text(
        article.get("title")
    )

    description = normalize_text(
        article.get("description")
    )

    content = normalize_text(
        article.get("content")
    )

    return (
        f"{title} {description} {content}"
    ).strip()


# ==========================================================
# DUPLICATE REMOVAL
# ==========================================================

def normalize_title(
    title: str,
) -> str:
    normalized = title.lower()

    normalized = re.sub(
        r"[^a-z0-9\s]",
        " ",
        normalized,
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()


def remove_duplicates(
    articles: list[dict],
) -> list[dict]:
    """
    Removes exact title and URL duplicates.
    """

    unique_articles = []

    seen_titles = set()
    seen_urls = set()

    for article in articles:
        title = normalize_text(
            article.get("title")
        )

        url = normalize_text(
            article.get("url")
        )

        if not title:
            continue

        normalized_title = normalize_title(
            title
        )

        if normalized_title in seen_titles:
            continue

        if url and url in seen_urls:
            continue

        seen_titles.add(
            normalized_title
        )

        if url:
            seen_urls.add(url)

        unique_articles.append(
            article
        )

    return unique_articles


def remove_near_duplicates(
    articles: list[dict],
) -> list[dict]:
    """
    Removes articles whose titles describe nearly the same event.
    """

    unique_articles = []
    accepted_word_sets = []

    for article in articles:
        title = normalize_text(
            article.get("title")
        )

        normalized_title = normalize_title(
            title
        )

        title_words = set(
            normalized_title.split()
        )

        if not title_words:
            continue

        duplicate = False

        for previous_words in accepted_word_sets:
            smaller_size = min(
                len(title_words),
                len(previous_words),
            )

            if smaller_size == 0:
                continue

            overlap = len(
                title_words.intersection(
                    previous_words
                )
            )

            similarity = (
                overlap / smaller_size
            )

            if similarity >= 0.75:
                duplicate = True
                break

        if duplicate:
            continue

        accepted_word_sets.append(
            title_words
        )

        unique_articles.append(
            article
        )

    return unique_articles


# ==========================================================
# NEWSAPI QUERY BUILDERS
# ==========================================================

def build_or_query(
    terms: list[str],
) -> str:
    cleaned_terms = [
        normalize_text(term)
        for term in terms
        if normalize_text(term)
    ]

    return " OR ".join(
        f'"{term}"'
        for term in cleaned_terms
    )


def build_candidate_query(
    origin: str,
    destination: str,
    shipment_type: str,
) -> str:
    """
    Retrieves a broad candidate set based primarily on shipment
    locations. OpenAI performs the precise relevance filtering.
    """

    return f'"{origin}" OR "{destination}"'
def build_shipment_search_queries(
    shipment_profile: dict,
) -> list[str]:
    """
    Generates focused NewsAPI searches requiring a location or shipment
    category together with logistics and disruption terms.
    """

    origin = normalize_text(
        shipment_profile.get("origin")
    )

    destination = normalize_text(
        shipment_profile.get("destination")
    )

    shipment_type = normalize_text(
        shipment_profile.get("shipment_type")
    )

    expected_events = shipment_profile.get(
        "expected_event_types",
        [],
    )

    location_operations = (
        "logistics OR freight OR trucking OR warehouse "
        "OR transportation OR shipping OR supply chain "
        "OR distribution OR carrier OR rail OR port"
    )

    disruption_terms = (
        "delay OR delayed OR disruption OR closure OR closed "
        "OR shutdown OR outage OR strike OR shortage OR recall "
        "OR congestion OR accident OR fire OR flood OR flooding "
        "OR hurricane OR tornado OR wildfire OR earthquake "
        "OR cyberattack OR ransomware"
    )

    queries = []

    if origin:
        queries.append(
            f'"{origin}" '
            f'AND ({location_operations}) '
            f'AND ({disruption_terms})'
        )

    if destination:
        queries.append(
            f'"{destination}" '
            f'AND ({location_operations}) '
            f'AND ({disruption_terms})'
        )

    if shipment_type:
        queries.append(
            f'"{shipment_type}" '
            f'AND ({disruption_terms})'
        )

    selected_events = [
        normalize_text(event)
        for event in expected_events[:4]
        if normalize_text(event)
    ]

    if selected_events and (origin or destination):
        location_terms = []

        if origin:
            location_terms.append(
                f'"{origin}"'
            )

        if destination:
            location_terms.append(
                f'"{destination}"'
            )

        event_query = " OR ".join(
            f'"{event}"'
            for event in selected_events
        )

        queries.append(
            f'({" OR ".join(location_terms)}) '
            f'AND ({event_query})'
        )

    unique_queries = []
    seen = set()

    for query in queries:
        cleaned_query = query.strip()
        key = cleaned_query.lower()

        if not cleaned_query or key in seen:
            continue

        seen.add(key)
        unique_queries.append(cleaned_query)

    return unique_queries[:4]


# ==========================================================
# NEWSAPI REQUEST
# ==========================================================

def search_newsapi(
    queries: list[str],
    api_key: str,
) -> tuple[list[dict], dict]:
    """
    Runs NewsAPI searches and returns both articles and API status details.
    """

    all_articles = []

    api_status = {
        "status": "ok",
        "status_code": 200,
        "message": "NewsAPI requests completed successfully.",
        "requests_attempted": 0,
        "successful_requests": 0,
    }

    print("\n" + "=" * 70)
    print("NEWSAPI REQUEST DEBUG")

    for query_number, query in enumerate(
        queries,
        start=1,
    ):
        api_status["requests_attempted"] += 1

        params = {
            "q": query,
            "language": "en",
            "searchIn": "title,description",
            "sortBy": "publishedAt",
            "pageSize": 100,
            "apiKey": api_key,
        }

        print(
            f"\nRequest {query_number}/{len(queries)}"
        )
        print("Query:", query)

        try:
            response = requests.get(
                NEWS_API_URL,
                params=params,
                timeout=20,
            )

            print(
                "HTTP Status:",
                response.status_code,
            )

            if response.status_code == 429:
                try:
                    message = response.json().get(
                        "message",
                        "NewsAPI rate limit reached.",
                    )
                except ValueError:
                    message = "NewsAPI rate limit reached."

                print(
                    "NewsAPI rate limit reached:",
                    message,
                )

                api_status.update(
                    {
                        "status": "rate_limited",
                        "status_code": 429,
                        "message": message,
                    }
                )
                break

            if response.status_code != 200:
                try:
                    error_message = response.json().get(
                        "message",
                        "Unknown NewsAPI error",
                    )
                except ValueError:
                    error_message = response.text

                print(
                    f"NewsAPI Error {response.status_code}: "
                    f"{error_message}"
                )

                api_status.update(
                    {
                        "status": "error",
                        "status_code": response.status_code,
                        "message": error_message,
                    }
                )
                continue

            data = response.json()

            if data.get("status") != "ok":
                error_message = data.get(
                    "message",
                    "Unknown NewsAPI error",
                )

                print(
                    "NewsAPI unsuccessful response:",
                    error_message,
                )

                api_status.update(
                    {
                        "status": "error",
                        "status_code": response.status_code,
                        "message": error_message,
                    }
                )
                continue

            api_status["successful_requests"] += 1

            articles = data.get(
                "articles",
                [],
            )

            if not isinstance(
                articles,
                list,
            ):
                articles = []

            print(
                "Articles Returned:",
                len(articles),
            )

            all_articles.extend(
                articles
            )

        except requests.RequestException as error:
            print(
                "NewsAPI request failed:",
                error,
            )

            api_status.update(
                {
                    "status": "error",
                    "status_code": None,
                    "message": str(error),
                }
            )

        except ValueError as error:
            print(
                "NewsAPI returned invalid JSON:",
                error,
            )

            api_status.update(
                {
                    "status": "error",
                    "status_code": None,
                    "message": (
                        f"Invalid JSON response: {error}"
                    ),
                }
            )

    combined_articles = remove_duplicates(
        all_articles
    )[:MAX_CANDIDATE_ARTICLES]

    print(
        "\nCombined Unique Articles:",
        len(combined_articles),
    )
    print(
        "NewsAPI Final Status:",
        api_status["status"],
    )
    print("=" * 70)

    return combined_articles, api_status
# ==========================================================
# EARLY CANDIDATE CLEANING
# ==========================================================

def clean_candidate_articles(
    articles: list[dict],
) -> list[dict]:
    cleaned_articles = []

    for article in articles:
        text = get_article_text(
            article
        )

        if not text:
            continue

        if contains_any(
            text,
            IGNORE_TERMS,
        ):
            continue

        cleaned_articles.append(
            article
        )

    cleaned_articles = remove_duplicates(
        cleaned_articles
    )

    return remove_near_duplicates(
        cleaned_articles
    )


# ==========================================================
# SHIPMENT PROFILE FOR NEWS ANALYSIS
# ==========================================================

def create_news_shipment_profile(
    origin: str,
    destination: str,
    shipment_type: str,
    priority: str = "Unknown",
    status: str = "Unknown",
) -> dict:
    """
    Converts the news-tool arguments into the tuple format expected
    by build_shipment_profile().
    """

    shipment_record = (
        "News Analysis Shipment",
        origin,
        destination,
        shipment_type,
        priority,
        status,
    )

    return build_shipment_profile(
        shipment_record
    )


# ==========================================================
# SEMANTIC RANKING
# ==========================================================

def rank_candidate_articles_semantically(
    articles: list[dict],
    shipment_profile: dict,
    limit: int = MAX_SEMANTIC_ARTICLES,
) -> list[dict]:
    """
    Ranks candidate articles using OpenAI embeddings.
    """

    if not articles:
        return []

    shipment_text = build_shipment_search_text(
        shipment_profile
    )

    usable_articles = []
    article_texts = []

    for article in articles:
        article_text = build_article_text(
            article
        )

        if not article_text:
            continue

        usable_articles.append(
            article
        )

        article_texts.append(
            article_text
        )

    if not article_texts:
        return []

    try:
        rankings = rank_articles_by_similarity(
            shipment_text=shipment_text,
            article_texts=article_texts,
        )

    except Exception as error:
        print(
            "Semantic ranking failed:",
            error,
        )

        return []

    ranked_articles = []

    for article_index, similarity_score in rankings:
        if article_index >= len(usable_articles):
            continue

        if similarity_score < MIN_SEMANTIC_SIMILARITY:
            continue

        ranked_article = dict(
            usable_articles[article_index]
        )

        ranked_article["semantic_similarity"] = round(
            float(similarity_score),
            4,
        )

        ranked_articles.append(
            ranked_article
        )

        if len(ranked_articles) >= limit:
            break

    return ranked_articles


# ==========================================================
# GPT RELEVANCE CLASSIFICATION
# ==========================================================

def severity_to_risk_points(
    severity: str,
    confidence: float,
) -> int:
    """
    Converts the GPT severity result into shipment news-risk points.

    Confidence slightly reduces points for uncertain classifications.
    """

    normalized_severity = normalize_text(
        severity
    ).title()

    base_points = {
        "Low": 3,
        "Medium": 6,
        "High": 10,
    }.get(
        normalized_severity,
        0,
    )

    if confidence >= 0.90:
        multiplier = 1.0

    elif confidence >= 0.80:
        multiplier = 0.9

    elif confidence >= MIN_CLASSIFIER_CONFIDENCE:
        multiplier = 0.75

    else:
        multiplier = 0.0

    return round(
        base_points * multiplier
    )


def classify_ranked_articles(
    articles: list[dict],
    shipment_profile: dict,
) -> dict:
    """
    Uses GPT to classify semantically ranked articles.

    Only articles that GPT identifies as relevant, operational, and
    sufficiently confident are retained.
    """

    relevant_articles = []
    all_assessments = []

    for article in articles[
        :MAX_CLASSIFIED_ARTICLES
    ]:
        try:
            classification = llm_relevance_classifier(
                shipment_profile=shipment_profile,
                article=article,
            )

        except Exception as error:
            classification = {
                "relevant": False,
                "confidence": 0.0,
                "location_match": False,
                "category_match": False,
                "operational_disruption": False,
                "event_type": "Unknown",
                "severity": "Low",
                "reason": (
                    f"Article classification failed: {error}"
                ),
            }

        confidence = classification.get(
            "confidence",
            0.0,
        )

        try:
            confidence = float(confidence)

        except (TypeError, ValueError):
            confidence = 0.0

        confidence = min(
            max(confidence, 0.0),
            1.0,
        )

        relevant = bool(
            classification.get(
                "relevant",
                False,
            )
        )

        operational_disruption = bool(
            classification.get(
                "operational_disruption",
                False,
            )
        )

        risk_points = severity_to_risk_points(
            severity=classification.get(
                "severity",
                "Low",
            ),
            confidence=confidence,
        )

        enriched_article = format_classified_article(
            article=article,
            classification=classification,
            risk_points=risk_points,
        )

        all_assessments.append(
            enriched_article
        )

        if (
            relevant
            and operational_disruption
            and confidence >= MIN_CLASSIFIER_CONFIDENCE
            and risk_points > 0
        ):
            relevant_articles.append(
                enriched_article
            )

    relevant_articles.sort(
        key=lambda article: (
            article.get(
                "risk_points",
                0,
            ),
            article.get(
                "classifier_confidence",
                0.0,
            ),
            article.get(
                "semantic_similarity",
                0.0,
            ),
        ),
        reverse=True,
    )

    return {
        "relevant_articles": relevant_articles,
        "all_assessments": all_assessments,
    }


# ==========================================================
# ARTICLE OUTPUT FORMAT
# ==========================================================

def format_classified_article(
    article: dict,
    classification: dict,
    risk_points: int,
) -> dict:
    source_data = article.get(
        "source"
    ) or {}

    if isinstance(source_data, dict):
        source_name = normalize_text(
            source_data.get("name")
        )
    else:
        source_name = normalize_text(
            source_data
        )

    return {
        "title": (
            normalize_text(
                article.get("title")
            )
            or "Untitled Article"
        ),
        "description": normalize_text(
            article.get("description")
        ),
        "source": (
            source_name
            or "Unknown"
        ),
        "url": normalize_text(
            article.get("url")
        ),
        "date": normalize_text(
            article.get("publishedAt")
        ),

        # Existing fields expected by nodes.py and app.py
        "is_disruption": bool(
            classification.get(
                "relevant",
                False,
            )
            and classification.get(
                "operational_disruption",
                False,
            )
        ),
        "severity": normalize_text(
            classification.get(
                "severity",
                "Low",
            )
        ).title(),
        "risk_points": risk_points,
        "classification_reason": normalize_text(
            classification.get(
                "reason",
                "No classification explanation available.",
            )
        ),
        "matched_keywords": [],

        # New semantic and classifier details
        "semantic_similarity": article.get(
            "semantic_similarity",
            0.0,
        ),
        "classifier_confidence": classification.get(
            "confidence",
            0.0,
        ),
        "location_match": classification.get(
            "location_match",
            False,
        ),
        "category_match": classification.get(
            "category_match",
            False,
        ),
        "operational_disruption": classification.get(
            "operational_disruption",
            False,
        ),
        "event_type": normalize_text(
            classification.get(
                "event_type",
                "Unknown",
            )
        ),
    }


# ==========================================================
# RESPONSE BUILDERS
# ==========================================================

def build_news_response(
    origin: str,
    destination: str,
    shipment_type: str,
    relevant_articles: list[dict],
    all_assessments: list[dict],
    candidate_count: int,
    semantic_candidate_count: int,
) -> dict:
    raw_risk_score = sum(
        article.get(
            "risk_points",
            0,
        )
        for article in relevant_articles
    )

    risk_score = min(
        raw_risk_score,
        MAX_NEWS_RISK_SCORE,
    )

    displayed_articles = relevant_articles[
        :MAX_DISPLAYED_ARTICLES
    ]

    return {
        "origin": origin,
        "destination": destination,
        "shipment_type": shipment_type,
        "source": "NewsAPI + OpenAI",
        "search_level": (
            "Semantic Ranking + GPT Relevance Classification"
        ),
        "risk_source": (
            "Shipment-Specific AI News Intelligence"
        ),
        "maximum_news_score": MAX_NEWS_RISK_SCORE,

        "candidate_news_count": candidate_count,
        "semantic_candidate_count": semantic_candidate_count,
        "classified_news_count": len(
            all_assessments
        ),

        "event_count": len(
            displayed_articles
        ),
        "relevant_news_count": len(
            relevant_articles
        ),
        "ignored_news_count": max(
            len(all_assessments)
            - len(relevant_articles),
            0,
        ),

        "raw_risk_score": raw_risk_score,
        "risk_score": risk_score,
        "risk_flag": risk_score > 0,

        "events": displayed_articles,
        "news_assessments": all_assessments,

        "risk_explanation": (
            "News risk is based only on articles that passed "
            "semantic ranking and GPT shipment-relevance classification."
        ),
    }


def build_empty_news_response(
    origin: str,
    destination: str,
    shipment_type: str,
    search_level: str,
    explanation: str,
    source: str = "NewsAPI + OpenAI",
    candidate_count: int = 0,
    semantic_candidate_count: int = 0,
    assessments: list[dict] | None = None,
) -> dict:
    assessment_list = assessments or []

    return {
        "origin": origin,
        "destination": destination,
        "shipment_type": shipment_type,
        "source": source,
        "search_level": search_level,
        "risk_source": search_level,
        "maximum_news_score": MAX_NEWS_RISK_SCORE,

        "candidate_news_count": candidate_count,
        "semantic_candidate_count": semantic_candidate_count,
        "classified_news_count": len(
            assessment_list
        ),

        "event_count": 0,
        "relevant_news_count": 0,
        "ignored_news_count": len(
            assessment_list
        ),

        "raw_risk_score": 0,
        "risk_score": 0,
        "risk_flag": False,

        "events": [],
        "news_assessments": assessment_list,
        "risk_explanation": explanation,
    }


# ==========================================================
# MAIN NEWS TOOL
# ==========================================================

def get_news_data(
    origin: str,
    destination: str,
    shipment_type: str,
    api_key: str | None = None,
    priority: str = "Unknown",
    status: str = "Unknown",
) -> dict:
    """
    Retrieves and evaluates shipment-specific news.
    """

    origin = normalize_text(origin)
    destination = normalize_text(destination)
    shipment_type = normalize_text(shipment_type)
    priority = normalize_text(priority) or "Unknown"
    status = normalize_text(status) or "Unknown"

    print("\n" + "#" * 70)
    print("NEWS INTELLIGENCE PIPELINE")
    print("Route:", f"{origin} -> {destination}")
    print("Shipment Type:", shipment_type)
    print("Priority:", priority)
    print("Shipment Status:", status)

    if not api_key:
        print("Pipeline stopped: NEWS_API_KEY is missing.")
        print("#" * 70)

        response = build_empty_news_response(
            origin=origin,
            destination=destination,
            shipment_type=shipment_type,
            search_level="News Service Unavailable",
            source="None",
            explanation=(
                "NEWS_API_KEY is missing. News risk could not be evaluated."
            ),
        )

        response["news_available"] = False
        return response

    shipment_profile = create_news_shipment_profile(
        origin=origin,
        destination=destination,
        shipment_type=shipment_type,
        priority=priority,
        status=status,
    )

    queries = build_shipment_search_queries(
        shipment_profile=shipment_profile,
    )

    print("\nGenerated Queries:", len(queries))

    for query in queries:
        print(" -", query)

    raw_articles, api_status = search_newsapi(
        queries=queries,
        api_key=api_key,
    )

    print("\nPIPELINE COUNTS")
    print("Raw Articles:", len(raw_articles))

    if (
        api_status.get("status") == "rate_limited"
        and not raw_articles
    ):
        print("Pipeline stopped: NewsAPI rate limit reached.")
        print("#" * 70)

        response = build_empty_news_response(
            origin=origin,
            destination=destination,
            shipment_type=shipment_type,
            search_level="NewsAPI Rate Limit Reached",
            source="NewsAPI",
            candidate_count=0,
            explanation=(
                "NewsAPI returned HTTP 429. News intelligence was "
                "unavailable for this run, so a zero news-risk score "
                "does not mean no disruption exists."
            ),
        )

        response["api_status"] = api_status
        response["news_available"] = False
        return response

    if (
        api_status.get("status") == "error"
        and not raw_articles
    ):
        print("Pipeline stopped: NewsAPI request failed.")
        print("#" * 70)

        response = build_empty_news_response(
            origin=origin,
            destination=destination,
            shipment_type=shipment_type,
            search_level="News Service Error",
            source="NewsAPI",
            candidate_count=0,
            explanation=(
                "NewsAPI could not provide articles for this run. "
                "News risk was not evaluated."
            ),
        )

        response["api_status"] = api_status
        response["news_available"] = False
        return response

    candidate_articles = clean_candidate_articles(
        raw_articles
    )

    print(
        "Candidate Articles After Cleaning:",
        len(candidate_articles),
    )

    if not candidate_articles:
        print("Pipeline result: no usable candidate articles.")
        print("#" * 70)

        response = build_empty_news_response(
            origin=origin,
            destination=destination,
            shipment_type=shipment_type,
            search_level="No Candidate Articles",
            candidate_count=0,
            explanation=(
                "NewsAPI completed successfully, but no usable recent "
                "candidate articles were returned for this shipment."
            ),
        )

        response["api_status"] = api_status
        response["news_available"] = True
        return response

    print("\nTop Candidate Titles:")

    for article in candidate_articles[:10]:
        print(
            " -",
            article.get(
                "title",
                "Untitled Article",
            ),
        )

    semantic_articles = rank_candidate_articles_semantically(
        articles=candidate_articles,
        shipment_profile=shipment_profile,
        limit=MAX_SEMANTIC_ARTICLES,
    )

    print(
        "Semantic Matches:",
        len(semantic_articles),
    )

    if not semantic_articles:
        print(
            "Pipeline result: semantic filter removed all articles."
        )
        print("#" * 70)

        response = build_empty_news_response(
            origin=origin,
            destination=destination,
            shipment_type=shipment_type,
            search_level="No Semantic Matches",
            candidate_count=len(candidate_articles),
            explanation=(
                "Candidate articles were retrieved, but none met the "
                "minimum semantic-similarity requirement."
            ),
        )

        response["api_status"] = api_status
        response["news_available"] = True
        return response

    print("\nSemantic Match Details:")

    for article in semantic_articles:
        print(
            " -",
            article.get(
                "title",
                "Untitled Article",
            ),
            "| similarity:",
            article.get(
                "semantic_similarity",
                0.0,
            ),
        )

    classification_result = classify_ranked_articles(
        articles=semantic_articles,
        shipment_profile=shipment_profile,
    )

    relevant_articles = classification_result.get(
        "relevant_articles",
        [],
    )

    all_assessments = classification_result.get(
        "all_assessments",
        [],
    )

    print(
        "GPT-Classified Articles:",
        len(all_assessments),
    )
    print(
        "GPT-Verified Relevant Articles:",
        len(relevant_articles),
    )

    print("\nGPT Classification Results:")

    for assessment in all_assessments:
        print(
            " -",
            assessment.get(
                "title",
                "Untitled Article",
            ),
            "| disruption:",
            assessment.get(
                "is_disruption",
                False,
            ),
            "| confidence:",
            assessment.get(
                "classifier_confidence",
                0.0,
            ),
            "| event:",
            assessment.get(
                "event_type",
                "Unknown",
            ),
            "| reason:",
            assessment.get(
                "classification_reason",
                "No reason available.",
            ),
        )

    if not relevant_articles:
        print(
            "Pipeline result: GPT rejected all semantic matches."
        )
        print("#" * 70)

        response = build_empty_news_response(
            origin=origin,
            destination=destination,
            shipment_type=shipment_type,
            search_level=(
                "No GPT-Verified Shipment Disruptions"
            ),
            candidate_count=len(candidate_articles),
            semantic_candidate_count=len(semantic_articles),
            assessments=all_assessments,
            explanation=(
                "Articles were retrieved and semantically ranked, but "
                "GPT did not verify a sufficiently confident operational "
                "disruption affecting this shipment."
            ),
        )

        response["api_status"] = api_status
        response["news_available"] = True
        return response

    print(
        "Pipeline result: verified shipment disruption found."
    )
    print("#" * 70)

    response = build_news_response(
        origin=origin,
        destination=destination,
        shipment_type=shipment_type,
        relevant_articles=relevant_articles,
        all_assessments=all_assessments,
        candidate_count=len(candidate_articles),
        semantic_candidate_count=len(semantic_articles),
    )

    response["api_status"] = api_status
    response["news_available"] = True
    return response