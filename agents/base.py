import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "bias": {"type": "string", "enum": ["Bullish", "Bearish", "Neutral"]},
        "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
        "summary": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "suggested_action": {"type": "string", "enum": ["Buy", "Sell", "Hold"]},
        "entry": {"type": ["number", "null"]},
        "stop_loss": {"type": ["number", "null"]},
        "take_profit": {"type": ["number", "null"]},
        "reasoning": {"type": "string"},
    },
    "required": ["bias", "confidence", "summary", "key_points", "suggested_action", "entry", "stop_loss", "take_profit", "reasoning"],
    "additionalProperties": False,
}


class BaseAgent:
    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
        self.last_report = None
        self.status = "Idle" if self.api_key else "API key missing"
        self.history = []

    def analyze(self, market_data: dict, extra_context: str = "") -> dict:
        self.status = "Analyzing..."
        try:
            if not self.api_key:
                raise RuntimeError("GEMINI_API_KEY is missing. Add it to your .env file.")

            user_content = f"""
Current Gold (XAUUSD) Market Data:
{json.dumps(market_data, indent=2)}

Extra Context:
{extra_context or "None"}

Analyze the supplied information for your assigned role. Return a concise,
data-driven report. Use null for trade levels when no reliable level can be inferred.
"""
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            payload = {
                "systemInstruction": {"parts": [{"text": self.system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_content}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 1024,
                    "responseMimeType": "application/json",
                    "responseJsonSchema": REPORT_SCHEMA,
                },
            }
            response = requests.post(
                url,
                headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"},
                json=payload,
                timeout=90,
            )
            response.raise_for_status()
            result = response.json()
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            report = json.loads(content)
            report["agent"] = self.name
            report["role"] = self.role
            report["timestamp"] = datetime.now().isoformat()
            self.last_report = report
            self.history.append(report)
            self.status = "Ready"
            return report
        except Exception as e:
            self.status = f"Error: {str(e)[:50]}"
            error_report = {
                "agent": self.name,
                "role": self.role,
                "bias": "Neutral",
                "confidence": 0,
                "summary": f"Analysis failed: {str(e)}",
                "key_points": [],
                "suggested_action": "Hold",
                "entry": None,
                "stop_loss": None,
                "take_profit": None,
                "reasoning": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            self.last_report = error_report
            return error_report
