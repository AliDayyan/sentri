from fastapi import FastAPI, Depends, UploadFile, File, Request, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.services import threat_intel, ai_engine, ocr_service, splunk_logger, auth_service
from app.database import init_db, get_db, ScanRecord, User
from collections import defaultdict
from datetime import date
from typing import Optional

app = FastAPI(title="Sentri API", version="0.1.0")

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


class RegisterPayload(BaseModel):
    email: EmailStr
    password: str


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


def get_current_user(
    authorization: Optional[str] = Header(None), db: Session = Depends(get_db)
) -> Optional[User]:
    """Returns the logged-in user if a valid token is provided, otherwise None (anonymous)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    user_id = auth_service.decode_access_token(token)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def _save_scan(db: Session, scan_type: str, content: str, result: dict, user: Optional[User] = None):
    preview = (content[:100] + "...") if len(content) > 100 else content
    record = ScanRecord(
        scan_type=scan_type,
        content_preview=preview,
        risk_level=result["risk_level"],
        risk_score=result["risk_score"],
        summary=result["summary"],
        user_id=user.id if user else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    splunk_logger.log_scan_event(scan_type, preview, result)

    return record


@app.get("/")
def root():
    return {"status": "Sentri backend is running"}


@app.post("/auth/register")
def register(payload: RegisterPayload, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = User(
        email=payload.email,
        hashed_password=auth_service.hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth_service.create_access_token(user.id)
    return {"access_token": token, "email": user.email}


@app.post("/auth/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not auth_service.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = auth_service.create_access_token(user.id)
    return {"access_token": token, "email": user.email}


@app.post("/analyze/message")
def analyze_message(
    payload: MessagePayload,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    client_ip = request.client.host
    if not current_user and not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Daily scan limit reached. Upgrade to Pro for unlimited scans.")

    result = ai_engine.analyze_message(payload.content)
    _save_scan(db, "message", payload.content, result, current_user)

    return {
        "risk_level": result["risk_level"],
        "risk_score": result["risk_score"],
        "summary": result["summary"],
        "threats": result.get("flags", []),
        "risk_factors": result.get("risk_factors", {}),
        "recommendations": []
    }


@app.post("/analyze/url")
def analyze_url(
    payload: UrlPayload,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    client_ip = request.client.host
    if not current_user and not check_rate_limit(client_ip):
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
    _save_scan(db, "url", payload.content, result, current_user)

    return {
        "risk_level": result["risk_level"],
        "risk_score": result["risk_score"],
        "summary": result["summary"],
        "threats": [],
        "recommendations": []
    }


@app.post("/analyze/image")
async def analyze_image(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    client_ip = request.client.host
    if not current_user and not check_rate_limit(client_ip):
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

    _save_scan(db, "image", extracted_text or "screenshot", result, current_user)

    return {
        "risk_level": result["risk_level"],
        "risk_score": result["risk_score"],
        "summary": result["summary"],
        "threats": result.get("flags", []),
        "risk_factors": result.get("risk_factors", {}),
        "recommendations": []
    }


@app.get("/history")
def get_history(db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user)):
    query = db.query(ScanRecord)
    if current_user:
        query = query.filter(ScanRecord.user_id == current_user.id)
    records = query.order_by(ScanRecord.created_at.desc()).limit(50).all()
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
def clear_history(db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user)):
    query = db.query(ScanRecord)
    if current_user:
        query = query.filter(ScanRecord.user_id == current_user.id)
    query.delete()
    db.commit()
    return {"status": "History cleared"}


@app.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user)):
    query = db.query(ScanRecord)
    if current_user:
        query = query.filter(ScanRecord.user_id == current_user.id)
    all_scans = query.all()

    total = len(all_scans)
    by_risk = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0, "UNKNOWN": 0}
    by_type = {"message": 0, "url": 0, "image": 0}

    for scan in all_scans:
        by_risk[scan.risk_level] = by_risk.get(scan.risk_level, 0) + 1
        by_type[scan.scan_type] = by_type.get(scan.scan_type, 0) + 1

    avg_score = (
        sum(s.risk_score for s in all_scans) / total if total > 0 else 0
    )

    return {
        "total_scans": total,
        "by_risk_level": by_risk,
        "by_scan_type": by_type,
        "average_risk_score": round(avg_score, 1),
    }