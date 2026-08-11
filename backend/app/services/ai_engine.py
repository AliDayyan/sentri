import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = """You are a security analyst AI for Sentri, a scam and phishing detection app.
Analyze the given message for signs of scams, phishing, or social engineering.

Look for:
- Urgency or pressure tactics
- Impersonation of banks, companies, or authorities
- Requests for money, gift cards, or financial info
- Requests for passwords or credentials
- Prize/lottery scams
- Suspicious links
- Generic greetings combined with high-stakes requests

Respond ONLY with valid JSON in this exact format, no other text:
{
  "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "risk_score": <integer 0-100>,
  "summary": "<one sentence explanation>",
  "flags": ["<flag1>", "<flag2>"]
}
"""


def analyze_message(text: str) -> dict:
    if not text or not text.strip():
        return {
            "risk_level": "LOW",
            "risk_score": 0,
            "summary": "No message content provided.",
            "flags": [],
        }

    if not client:
        return {
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "summary": "AI engine not configured (missing GROQ_API_KEY).",
            "flags": [],
        }

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            max_tokens=300,
        )

        raw_content = response.choices[0].message.content.strip()

        # Strip markdown code fences if the model added them
        if raw_content.startswith("```"):
            raw_content = raw_content.strip("`")
            if raw_content.startswith("json"):
                raw_content = raw_content[4:].strip()

        result = json.loads(raw_content)

        return {
            "risk_level": result.get("risk_level", "UNKNOWN"),
            "risk_score": int(result.get("risk_score", 0)),
            "summary": result.get("summary", "No summary provided."),
            "flags": result.get("flags", []),
        }

    except Exception as e:
        return {
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "summary": f"AI analysis failed: {str(e)}",
            "flags": [],
        }