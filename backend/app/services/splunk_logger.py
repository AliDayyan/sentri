import os
import json
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

SPLUNK_HEC_TOKEN = os.getenv("SPLUNK_HEC_TOKEN")
SPLUNK_HEC_URL = os.getenv("SPLUNK_HEC_URL")


def log_scan_event(scan_type: str, content_preview: str, result: dict):
    """
    Sends a scan event to Splunk via HTTP Event Collector.
    Fails silently (logs to console) so Splunk being down never breaks the app.
    """
    if not SPLUNK_HEC_TOKEN or not SPLUNK_HEC_URL:
        return  # Splunk not configured, skip silently

    event_payload = {
        "event": {
            "app": "sentri",
            "scan_type": scan_type,
            "content_preview": content_preview,
            "risk_level": result.get("risk_level"),
            "risk_score": result.get("risk_score"),
            "summary": result.get("summary"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "sourcetype": "_json",
        "index": "sentri",
    }

    headers = {
        "Authorization": f"Splunk {SPLUNK_HEC_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        requests.post(
            SPLUNK_HEC_URL,
            headers=headers,
            data=json.dumps(event_payload),
            verify=False,  # local dev Splunk often uses self-signed certs
            timeout=3,
        )
    except Exception as e:
        print(f"[Splunk logging failed]: {e}")