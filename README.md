# Client Intake, Document Reminder & CRM Workflow Demo

A working Streamlit demo of AI-powered client onboarding — demonstrating intake extraction, document chasing, and a full audit trail with a human review gate.

## What It Does

### Tab 1 — Client Intake
Submit a new client via a form. Claude (Haiku) extracts and structures the intake into a clean JSON profile. Save it to the CRM with one click.

### Tab 2 — Document Checklist & Reminders
Select any client to see which onboarding documents are submitted vs missing. For clients with gaps, generate a polite, personalised reminder email via Claude — then route it through a **human review gate** before it's logged.

### Tab 3 — CRM Log
Full audit trail of every action: intakes created, reminders generated, approvals confirmed. Email addresses are masked in the log. Pending reminder approvals can be confirmed here.

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Anthropic API key
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-...

# Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key (or enter in the sidebar at runtime) |

Create a `.env` file or set the variable in your shell. The API key can also be entered at runtime via the sidebar — it is never stored beyond the browser session.

---

## Data Protection

### Demo Mode
This demo uses **sample/dummy data only**. No real PII is stored, transmitted, or logged. Sample clients are loaded from `sample_data/sample_clients.json` and stored locally in `data/crm.json`.

### Production Implementation
In a production deployment, this system would:

- **Encryption at rest:** All PII stored in an encrypted database (e.g. PostgreSQL with encrypted columns or Supabase with RLS).
- **GDPR/UK GDPR compliance:** Data subjects' rights (access, erasure, portability) implemented as CRM functions.
- **Data Processing Agreement (DPA):** Signed with all vendors handling PII, including Anthropic (their API processes the intake text — scoped to extraction only, not retained for training per Anthropic's API terms).
- **Audit log masking:** Email addresses and phone numbers are never stored verbatim in audit logs — masked with `***` as shown in Tab 3.
- **Human review gate:** No automated email dispatch. Every outbound communication is approved by a human operator before sending.
- **Role-based access:** CRM records accessible only to authorised staff via authenticated sessions.
- **Data minimisation:** Only the fields necessary for onboarding are collected and stored.

---

## Architecture

```
Intake form → Claude extract → CRM JSON record
CRM record → doc checklist → Claude draft reminder → human review gate → audit log
```

**Files:**
- `app.py` — Streamlit UI (3 tabs)
- `intake.py` — Claude API intake extraction
- `documents.py` — Document status + Claude reminder drafting
- `crm.py` — JSON-file CRM backend
- `data/crm.json` — Client records (auto-created on first run)
- `data/audit.json` — Audit log (auto-created on first run)
- `sample_data/sample_clients.json` — Seed data (3 clients, varied doc statuses)

---

## Sample Data

Three pre-loaded clients demonstrate different states:
- **Sarah Thompson** — All 4 docs submitted (no reminder needed)
- **James Okafor** — 2 of 4 docs missing (Proof of Address, Signed NDA)
- **Priya Mehta** — Brand new intake, all 4 docs missing
