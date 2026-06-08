"""
intake.py — Claude API call to extract and structure client intake data.
Model: claude-haiku-4-5-20251001
"""

import json
import re
from datetime import datetime, timezone

import anthropic


SYSTEM_PROMPT = """You are a client intake processing assistant for an AI automation agency.
Given free-text or semi-structured client information, extract and return a structured JSON object.

Return ONLY valid JSON — no explanation, no markdown, no extra text. Use this exact schema:
{
  "name": "string — full name",
  "company": "string — company name",
  "email": "string — email address",
  "phone": "string — phone number",
  "service_requested": "string — one of: CRM Setup, Email Automation, Document Workflow, Other",
  "notes": "string — brief summary of key requirements",
  "intake_date": "string — YYYY-MM-DD (today if not specified)",
  "docs_required": ["array", "of", "required", "documents"]
}

For docs_required, use standard onboarding documents appropriate to the service type:
- CRM Setup: ["Signed Contract", "ID Verification", "Proof of Address"]
- Email Automation: ["Signed Contract", "ID Verification", "Signed NDA"]
- Document Workflow: ["Signed Contract", "ID Verification", "Proof of Address", "Signed NDA"]
- Other: ["Signed Contract", "ID Verification"]"""


def extract_intake(form_data: dict, api_key: str) -> dict:
    """
    Given a dict of form fields, use Claude to extract and structure the intake.
    Returns a structured client dict.
    """
    client = anthropic.Anthropic(api_key=api_key)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Build input text from form data
    input_text = f"""Today's date: {today}

Client intake form submission:
- Name: {form_data.get('name', '')}
- Company: {form_data.get('company', '')}
- Email: {form_data.get('email', '')}
- Phone: {form_data.get('phone', '')}
- Service Requested: {form_data.get('service_requested', '')}
- Notes / Additional Info: {form_data.get('notes', '')}

Extract and structure this intake. Infer any missing fields where reasonable."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": input_text}],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    structured = json.loads(raw)

    # Merge back any fields Claude couldn't infer from pure text
    structured.setdefault("email", form_data.get("email", ""))
    structured.setdefault("phone", form_data.get("phone", ""))
    structured["docs_submitted"] = []  # New intake: no docs submitted yet

    return structured
