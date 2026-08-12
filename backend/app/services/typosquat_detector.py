from urllib.parse import urlparse

KNOWN_BRANDS = [
    "paypal.com", "amazon.com", "google.com", "apple.com", "microsoft.com",
    "facebook.com", "netflix.com", "bankofamerica.com", "chase.com",
    "wellsfargo.com", "irs.gov", "instagram.com", "linkedin.com", "ebay.com",
]


def _levenshtein_distance(a: str, b: str) -> int:
    """Compute edit distance between two strings."""
    if len(a) < len(b):
        return _levenshtein_distance(b, a)
    if len(b) == 0:
        return len(a)

    previous_row = range(len(b) + 1)
    for i, ca in enumerate(a):
        current_row = [i + 1]
        for j, cb in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (ca != cb)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def check_typosquatting(url: str) -> dict:
    """
    Checks if a URL's domain is suspiciously similar to a known brand
    without being an exact match (potential typosquatting/phishing).
    """
    try:
        parsed = urlparse(url if "://" in url else f"http://{url}")
        domain = parsed.netloc.lower().replace("www.", "")
    except Exception:
        return {"is_typosquat": False, "matched_brand": None, "distance": None}

    for brand in KNOWN_BRANDS:
        if domain == brand:
            return {"is_typosquat": False, "matched_brand": None, "distance": None}

        distance = _levenshtein_distance(domain, brand)
        if 0 < distance <= 2 and len(domain) >= len(brand) - 2:
            return {
                "is_typosquat": True,
                "matched_brand": brand,
                "distance": distance,
            }

    return {"is_typosquat": False, "matched_brand": None, "distance": None}