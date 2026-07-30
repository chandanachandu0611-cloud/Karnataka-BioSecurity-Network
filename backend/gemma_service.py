import base64
import json
import os
from typing import Any, Dict

import requests

GEMMA_PROMPT = """You are the AI assistant for Karnataka BioSecurity Network.

Analyze the uploaded livestock image.

Do NOT provide a final diagnosis.

Only identify visible information.

Return ONLY valid JSON in this format:

{
  "animal_type":"",
  "issue_title":"",
  "description":"",
  "severity":"Low|Medium|High",
  "symptoms":[]
}

Rules:
- Identify the animal if visible.
- Generate a short issue title.
- Write a concise description based only on what is visible.
- Estimate severity using Low, Medium or High.
- List only visible symptoms.
- Do not recommend medicine.
- Do not invent symptoms that are not visible.
- Return JSON only."""


def analyze_image(image: Any) -> Dict[str, Any]:
    """Analyze an uploaded image with Gemini and return structured form data."""
    if image is None:
        return {}

    if hasattr(image, "read"):
        image_bytes = image.read()
        filename = getattr(image, "filename", "") or "image.jpg"
    else:
        with open(image, "rb") as fh:
            image_bytes = fh.read()
        filename = os.path.basename(image)

    if not image_bytes:
        return {}

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {}

    mime_type = "image/jpeg"
    if filename.lower().endswith(".png"):
        mime_type = "image/png"
    elif filename.lower().endswith(".gif"):
        mime_type = "image/gif"

    try:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": GEMMA_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": encoded,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return _parse_response(text)
    except Exception as exc:
        print(f"Gemma image analysis failed: {exc}")
        return {}


def _parse_response(text: str) -> Dict[str, Any]:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]

    payload = json.loads(cleaned)
    severity = str(payload.get("severity", "Medium") or "Medium").strip().lower()
    if severity not in {"low", "medium", "high"}:
        severity = "medium"

    symptoms = payload.get("symptoms") or []
    if isinstance(symptoms, str):
        symptoms = [symptoms]

    return {
        "animal_type": str(payload.get("animal_type", "") or "").strip() or "poultry",
        "issue_title": str(payload.get("issue_title", "") or "").strip(),
        "description": str(payload.get("description", "") or "").strip(),
        "severity": severity,
        "symptoms": [str(item).strip() for item in symptoms if str(item).strip()],
    }
