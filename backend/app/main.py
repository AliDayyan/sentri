from fastapi import FastAPI, Depends, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.services import threat_intel, ai_engine, ocr_service, splunk_logger
from app.database import init_db, get_db, ScanRecord

app = FastAPI(title="Sentri API", version="0.1.0")


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

    # Also send to Splunk (fails silently if Splunk is unreachable)
    splunk_logger.log_scan_event(scan_type, preview, result)

    return record


@app.get("/")
def root():
    return {"status": "Sentri backend is running"}


@app.post("/analyze/message")
def analyze_message(payload: MessagePayload, db: Session = Depends(get_db)):
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
def analyze_url(payload: UrlPayload, db: Session = Depends(get_db)):
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
async def analyze_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
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