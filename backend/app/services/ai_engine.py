import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = """You are a security analyst AI for Sentri, a scam and phishing detection app.
Analyze the given message for signs of scams, phishing, or social engineering.

Check for these specific risk factor categories:
- urgency: pressure tactics, deadlines, threats of account closure
- impersonation: claiming to be a bank, company, government agency, or authority
- financial_request: asking for money, gift cards, wire transfers, crypto
- credential_phishing: asking to verify passwords, login info, or personal identity
- prize_scam: fake lottery, prize, or reward claims
- suspicious_link: contains a URL that seems designed to trick the recipient

For EACH category, determine if it was detected, and if so, quote the specific
part of the message that triggered it as "evidence".

Respond ONLY with valid JSON in this exact format, no other text:
{
  "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "risk_score": <integer 0-100>,
  "summary": "<one sentence explanation>",
  "risk_factors": {
    "urgency": {"detected": true|false, "evidence": "<quote or null>"},
    "impersonation": {"detected": true|false, "evidence": "<quote or null>"},
    "financial_request": {"detected": true|false, "evidence": "<quote or null>"},
    "credential_phishing": {"detected": true|false, "evidence": "<quote or null>"},
    "prize_scam": {"detected": true|false, "evidence": "<quote or null>"},
    "suspicious_link": {"detected": true|false, "evidence": "<quote or null>"}
  }
}
"""


def analyze_message(text: str) -> dict:
    if not text or not text.strip():
        return {
            "risk_level": "LOW",
            "risk_score": 0,
            "summary": "No message content provided.",
            "flags": [],
            "risk_factors": {},
        }

    if not client:
        return {
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "summary": "AI engine not configured (missing GROQ_API_KEY).",
            "flags": [],
            "risk_factors": {},
        }

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            max_tokens=500,
        )

        raw_content = response.choices[0].message.content.strip()

        if raw_content.startswith("```"):
            raw_content = raw_content.strip("`")
            if raw_content.startswith("json"):
                raw_content = raw_content[4:].strip()

        result = json.loads(raw_content)

        risk_factors = result.get("risk_factors", {})
        flags = [
            key.replace("_", " ").title()
            for key, value in risk_factors.items()
            if isinstance(value, dict) and value.get("detected")
        ]

        return {
            "risk_level": result.get("risk_level", "UNKNOWN"),
            "risk_score": int(result.get("risk_score", 0)),
            "summary": result.get("summary", "No summary provided."),
            "flags": flags,
            "risk_factors": risk_factors,
        }

    except Exception as e:
        return {
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "summary": f"AI analysis failed: {str(e)}",
            "flags": [],
            "risk_factors": {},
        }