from fastapi import FastAPI, Depends, UploadFile, File, Request, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.services import threat_intel, ai_engine, ocr_service, splunk_logger
from app.database import init_db, get_db, ScanRecord
from collections import defaultdict
from datetime import date

app = FastAPI(title="Sentri API", version="0.1.0")

# Simple in-memory rate limiter: {ip: {date: count}}
scan_counts = defaultdict(lambda: defaultdict(int))
DAILY_LIMIT = 3


def check_rate_limit(client_ip: str) -> bool:
    today = str(date.today())
    if scan_counts[client_ip][today] >= DAILY_LIMIT:
        return False
    scan_counts[client_ip][today] += 1
    return True


@app.on_event("startup")
def on_startup():
    init_db()


class MessagePayload(BaseModel):
    content: str = ""


class UrlPayload(BaseModel):
    content: str = ""


def _save_scan(db: Session, scan_type: str, content: str, result: dict):
    preview = (content[:100] + "...") if len(content) > 100 else content
    record = ScanRecord(
        scan_type=scan_type,
        content_preview=preview,
        risk_level=result["risk_level"],
        risk_score=result["risk_score"],
        summary=result["summary"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    splunk_logger.log_scan_event(scan_type, preview, result)

    return record


@app.get("/")
def root():
    return {"status": "Sentri backend is running"}


@app.post("/analyze/message")
def analyze_message(payload: MessagePayload, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Daily scan limit reached. Upgrade to Pro for unlimited scans.")

    result = ai_engine.analyze_message(payload.content)
    _save_scan(db, "message", payload.content, result)

    return {
        "risk_level": result["risk_level"],
        "risk_score": result["risk_score"],
        "summary": result["summary"],
        "threats": result.get("flags", []),
        "recommendations": []
    }


@app.post("/analyze/url")
def analyze_url(payload: UrlPayload, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Daily scan limit reached. Upgrade to Pro for unlimited scans.")

    if not payload.content:
        return {
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "summary": "No URL provided.",
            "threats": [],
            "recommendations": []
        }

    result = threat_intel.check_url(payload.content)
    _save_scan(db, "url", payload.content, result)

    return {
        "risk_level": result["risk_level"],
        "risk_score": result["risk_score"],
        "summary": result["summary"],
        "threats": [],
        "recommendations": []
    }


@app.post("/analyze/image")
async def analyze_image(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Daily scan limit reached. Upgrade to Pro for unlimited scans.")

    image_bytes = await file.read()
    extracted_text = ocr_service.extract_text_from_image(image_bytes)

    if extracted_text.startswith("__OCR_ERROR__"):
        result = {
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "summary": "Could not read text from this image.",
            "flags": [],
        }
    elif not extracted_text:
        result = {
            "risk_level": "LOW",
            "risk_score": 0,
            "summary": "No readable text found in this image.",
            "flags": [],
        }
    else:
        result = ai_engine.analyze_message(extracted_text)

    _save_scan(db, "image", extracted_text or "screenshot", result)

    return {
        "risk_level": result["risk_level"],
        "risk_score": result["risk_score"],
        "summary": result["summary"],
        "threats": result.get("flags", []),
        "recommendations": []
    }


@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    records = db.query(ScanRecord).order_by(ScanRecord.created_at.desc()).limit(50).all()
    return {
        "scans": [
            {
                "id": r.id,
                "scan_type": r.scan_type,
                "content_preview": r.content_preview,
                "risk_level": r.risk_level,
                "risk_score": r.risk_score,
                "summary": r.summary,
                "created_at": r.created_at.isoformat(),
            }
            for r in records
        ]
    }


@app.delete("/history")
def clear_history(db: Session = Depends(get_db)):
    db.query(ScanRecord).delete()
    db.commit()
    return {"status": "History cleared"}