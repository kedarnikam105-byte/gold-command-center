import os
import json
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class BaseAgent:
    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.1-8b-instant"  # Reliable free model on Groq
        self.last_report = None
        self.status = "Idle"
        self.history = []

    def analyze(self, market_data: dict, extra_context: str = "") -> dict:
        self.status = "Analyzing..."
        try:
            user_content = f"""
Current Gold (XAUUSD) Market Data:
{json.dumps(market_data, indent=2)}

Extra Context:
{extra_context}

Respond ONLY with valid JSON in this exact format:
{{
  "bias": "Bullish" or "Bearish" or "Neutral",
  "confidence": 0-100,
  "summary": "2-3 sentence summary",
  "key_points": ["point1", "point2", "point3"],
  "suggested_action": "Buy" or "Sell" or "Hold",
  "entry": null or number,
  "stop_loss": null or number,
  "take_profit": null or number,
  "reasoning": "detailed reasoning"
}}
"""
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
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
                "timestamp": datetime.now().isoformat()
            }
            self.last_report = error_report
            return error_report
