from fastapi import FastAPI
from pydantic import BaseModel
from app.services import threat_intel

app = FastAPI(title="Sentri API", version="0.1.0")


class MessagePayload(BaseModel):
    content: str = ""


class UrlPayload(BaseModel):
    content: str = ""


@app.get("/")
def root():
    return {"status": "Sentri backend is running"}


@app.post("/analyze/message")
def analyze_message(payload: MessagePayload):
    return {
        "risk_level": "LOW",
        "risk_score": 12,
        "summary": "No significant threats detected in this message.",
        "threats": [],
        "recommendations": []
    }


@app.post("/analyze/url")
def analyze_url(payload: UrlPayload):
    if not payload.content:
        return {
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "summary": "No URL provided.",
            "threats": [],
            "recommendations": []
        }

    result = threat_intel.check_url(payload.content)

    return {
        "risk_level": result["risk_level"],
        "risk_score": result["risk_score"],
        "summary": result["summary"],
        "threats": [],
        "recommendations": []
    }


@app.post("/analyze/image")
def analyze_image(payload: dict):
    return {
        "risk_level": "LOW",
        "risk_score": 10,
        "summary": "No significant threats detected in this image.",
        "threats": [],
        "recommendations": []
    }


@app.get("/history")
def get_history():
    return {"scans": []}