import os
import base64
import time
import requests
from dotenv import load_dotenv

load_dotenv()

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
VT_BASE_URL = "https://www.virustotal.com/api/v3"


def _url_to_id(url: str) -> str:
    """VirusTotal requires URLs to be base64-encoded (no padding) to use as an ID."""
    return base64.urlsafe_b64encode(url.encode()).decode().strip("=")


def check_url(url: str) -> dict:
    """
    Submits a URL to VirusTotal and retrieves its analysis.
    Returns a simplified dict with risk info.
    """
    if not VIRUSTOTAL_API_KEY:
        return {
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "summary": "VirusTotal API key not configured.",
            "malicious_count": 0,
            "suspicious_count": 0,
        }

    headers = {"x-apikey": VIRUSTOTAL_API_KEY}

    # Step 1: Submit the URL for scanning
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

    # Step 2: Get the analysis using the URL's ID
    url_id = _url_to_id(url)

    # Give VirusTotal a moment to process (free tier, simple approach)
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
    harmless = stats.get("harmless", 0)
    undetected = stats.get("undetected", 0)

    # Score based on absolute detections, not diluted by total engine count.
    # Even a handful of malicious flags from reputable vendors should score high.
    risk_score = min(100, (malicious * 8) + (suspicious * 3))

    if malicious >= 5:
        risk_level = "CRITICAL"
    elif malicious >= 1:
        risk_level = "HIGH"
    elif suspicious >= 1:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "summary": f"{malicious} security vendors flagged this URL as malicious, {suspicious} as suspicious.",
        "malicious_count": malicious,
        "suspicious_count": suspicious,
    }