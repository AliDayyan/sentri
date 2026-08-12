import os
import base64
import time
import requests
from dotenv import load_dotenv
from app.services import typosquat_detector

load_dotenv()

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
VT_BASE_URL = "https://www.virustotal.com/api/v3"


def _url_to_id(url: str) -> str:
    """VirusTotal requires URLs to be base64-encoded (no padding) to use as an ID."""
    return base64.urlsafe_b64encode(url.encode()).decode().strip("=")


def check_url(url: str) -> dict:
    """
    Submits a URL to VirusTotal and retrieves its analysis.
    Also checks for typosquatting against known brands.
    """
    typosquat_result = typosquat_detector.check_typosquatting(url)

    if not VIRUSTOTAL_API_KEY:
        return {
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "summary": "VirusTotal API key not configured.",
            "malicious_count": 0,
            "suspicious_count": 0,
        }

    headers = {"x-apikey": VIRUSTOTAL_API_KEY}

    submit_response = requests.post(
        f"{VT_BASE_URL}/urls",
        headers=headers,
        data={"url": url},
    )

    if submit_response.status_code != 200:
        return {
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "summary": f"VirusTotal submission failed: {submit_response.status_code}",
            "malicious_count": 0,
            "suspicious_count": 0,
        }

    url_id = _url_to_id(url)
    time.sleep(2)

    report_response = requests.get(
        f"{VT_BASE_URL}/urls/{url_id}",
        headers=headers,
    )

    if report_response.status_code != 200:
        return {
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "summary": f"VirusTotal report fetch failed: {report_response.status_code}",
            "malicious_count": 0,
            "suspicious_count": 0,
        }

    data = report_response.json()
    stats = data["data"]["attributes"]["last_analysis_stats"]

    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)

    risk_score = min(100, (malicious * 8) + (suspicious * 3))

    if malicious >= 5:
        risk_level = "CRITICAL"
    elif malicious >= 1:
        risk_level = "HIGH"
    elif suspicious >= 1:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    summary = f"{malicious} security vendors flagged this URL as malicious, {suspicious} as suspicious."

    if typosquat_result["is_typosquat"]:
        risk_score = min(100, risk_score + 40)
        if risk_level in ("LOW", "MEDIUM"):
            risk_level = "HIGH"
        summary += f" This domain closely resembles '{typosquat_result['matched_brand']}' and may be impersonating it (typosquatting)."

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "summary": summary,
        "malicious_count": malicious,
        "suspicious_count": suspicious,
    }