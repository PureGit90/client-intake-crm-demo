"""
documents.py — Document reminder logic.
Uses Claude to draft professional, personalised reminder emails for missing documents.
"""

import re
import anthropic


SYSTEM_PROMPT = """You are a professional client success manager at an AI automation agency.
Draft polite, professional reminder emails for clients who have outstanding onboarding documents.

Rules:
- Warm but professional tone — never pushy or passive-aggressive
- Mention each missing document by name on its own line
- Include a clear subject line as the first line in format: Subject: <subject>
- Keep body under 150 words
- End with a helpful note about data protection and secure upload
- Sign off as "The Onboarding Team"
- Do NOT include placeholders like [Your Name] — write the full email ready to send"""


def _mock_reminder(client: dict, missing_docs: list[str]) -> dict:
    """Return a realistic mock reminder email without an API key."""
    docs_list = "\n".join(f"  - {doc}" for doc in missing_docs)
    subject = f"Action Required: Outstanding Documents — {client.get('company', 'Your Account')}"
    body = f"""Hi {client.get('name', 'there')},

I hope you're settling in well. To complete your onboarding for the {client.get('service_requested', 'service')} we have set up for you, we still need the following documents:

{docs_list}

Once received, we'll process them securely and confirm receipt within one business day. All documents are handled in line with our data protection policy and never stored in plain text.

Please reply to this email or use our secure upload link to submit them at your convenience.

The Onboarding Team"""
    return {
        "subject": subject,
        "body": body,
        "full_text": f"Subject: {subject}\n\n{body}",
        "demo_mode": True,
    }


def draft_reminder(client: dict, missing_docs: list[str], api_key: str) -> dict:
    """
    Given a client record and list of missing document names,
    draft a reminder email using Claude.

    Returns: {"subject": str, "body": str, "full_text": str}
    """
    if not api_key:
        return _mock_reminder(client, missing_docs)

    anthropic_client = anthropic.Anthropic(api_key=api_key)

    docs_list = "\n".join(f"- {doc}" for doc in missing_docs)

    prompt = f"""Client name: {client['name']}
Company: {client['company']}
Service requested: {client['service_requested']}

Missing documents:
{docs_list}

Draft a reminder email asking them to submit the missing documents above."""

    message = anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    full_text = message.content[0].text.strip()

    # Parse subject line from first line
    lines = full_text.split("\n")
    subject = ""
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("subject:"):
            subject = line.strip()[len("subject:"):].strip()
            body_start = i + 1
            break

    # Skip blank lines after subject
    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1

    body = "\n".join(lines[body_start:]).strip()

    return {
        "subject": subject or f"Action Required: Outstanding Documents — {client['company']}",
        "body": body,
        "full_text": full_text,
    }


def get_missing_docs(client: dict) -> list[str]:
    """Return list of documents that are required but not yet submitted."""
    required = set(client.get("docs_required", []))
    submitted = set(client.get("docs_submitted", []))
    # Preserve original order
    return [doc for doc in client.get("docs_required", []) if doc not in submitted]


def get_doc_status(client: dict) -> list[dict]:
    """Return full doc status list with submitted flag for UI rendering."""
    submitted = set(client.get("docs_submitted", []))
    return [
        {"name": doc, "submitted": doc in submitted}
        for doc in client.get("docs_required", [])
    ]
