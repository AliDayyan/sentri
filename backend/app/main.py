from fastapi import FastAPI

app = FastAPI(title="Sentri API", version="0.1.0")


@app.get("/")
def root():
    return {"status": "Sentri backend is running"}


@app.post("/analyze/message")
def analyze_message(payload: dict):
    return {
        "risk_level": "LOW",
        "risk_score": 12,
        "summary": "No significant threats detected in this message.",
        "threats": [],
        "recommendations": []
    }


@app.post("/analyze/url")
def analyze_url(payload: dict):
    return {
        "risk_level": "LOW",
        "risk_score": 8,
        "summary": "No significant threats detected in this URL.",
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