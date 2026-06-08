"""
crm.py — Simple JSON-file CRM backend.
Stores client records in data/crm.json and audit log in data/audit.json.
On first run, loads sample data automatically.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
CRM_FILE = DATA_DIR / "crm.json"
AUDIT_FILE = DATA_DIR / "audit.json"
SAMPLE_FILE = Path(__file__).parent / "sample_data" / "sample_clients.json"


def _ensure_files():
    DATA_DIR.mkdir(exist_ok=True)
    if not CRM_FILE.exists():
        # Seed with sample data on first run
        if SAMPLE_FILE.exists():
            with open(SAMPLE_FILE) as f:
                sample = json.load(f)
            with open(CRM_FILE, "w") as f:
                json.dump(sample, f, indent=2)
            # Log the seed events
            for client in sample:
                _append_audit({
                    "id": str(uuid.uuid4()),
                    "timestamp": client["intake_date"] + "T09:00:00Z",
                    "client_id": client["id"],
                    "client_name": client["name"],
                    "action": "intake_created",
                    "details": f"Sample client seeded: {client['service_requested']}",
                    "status": "completed",
                })
        else:
            with open(CRM_FILE, "w") as f:
                json.dump([], f)
    if not AUDIT_FILE.exists():
        with open(AUDIT_FILE, "w") as f:
            json.dump([], f)


def _append_audit(entry: dict):
    DATA_DIR.mkdir(exist_ok=True)
    if AUDIT_FILE.exists():
        with open(AUDIT_FILE) as f:
            log = json.load(f)
    else:
        log = []
    log.append(entry)
    with open(AUDIT_FILE, "w") as f:
        json.dump(log, f, indent=2)


def get_clients() -> list[dict]:
    _ensure_files()
    with open(CRM_FILE) as f:
        return json.load(f)


def get_client_by_id(client_id: str) -> dict | None:
    for c in get_clients():
        if c["id"] == client_id:
            return c
    return None


def create_client(data: dict) -> dict:
    _ensure_files()
    clients = get_clients()
    client_id = "client_" + str(uuid.uuid4())[:8]
    record = {
        "id": client_id,
        "name": data.get("name", ""),
        "company": data.get("company", ""),
        "email": data.get("email", ""),
        "phone": data.get("phone", ""),
        "service_requested": data.get("service_requested", ""),
        "notes": data.get("notes", ""),
        "intake_date": data.get("intake_date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        "docs_required": data.get("docs_required", ["Signed Contract", "ID Verification", "Proof of Address", "Signed NDA"]),
        "docs_submitted": data.get("docs_submitted", []),
        "status": "new",
    }
    clients.append(record)
    with open(CRM_FILE, "w") as f:
        json.dump(clients, f, indent=2)
    log_action(client_id, "intake_created", f"New client intake: {record['service_requested']}", status="completed", client_name=record["name"])
    return record


def update_client(client_id: str, updates: dict) -> dict | None:
    _ensure_files()
    clients = get_clients()
    for i, c in enumerate(clients):
        if c["id"] == client_id:
            clients[i].update(updates)
            with open(CRM_FILE, "w") as f:
                json.dump(clients, f, indent=2)
            log_action(client_id, "record_updated", f"Fields updated: {list(updates.keys())}", status="completed", client_name=c["name"])
            return clients[i]
    return None


def log_action(client_id: str, action: str, details: str, status: str = "completed", client_name: str = ""):
    """Log an action to the audit trail. Never stores raw email addresses."""
    if not client_name:
        c = get_client_by_id(client_id)
        client_name = c["name"] if c else "Unknown"

    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "client_id": client_id,
        "client_name": client_name,
        "action": action,
        "details": details,
        "status": status,
    }
    _append_audit(entry)
    return entry


def get_audit_log() -> list[dict]:
    _ensure_files()
    with open(AUDIT_FILE) as f:
        return json.load(f)


def mark_reminder_sent(log_entry_id: str) -> bool:
    """Mark a pending reminder as confirmed-sent in the audit log."""
    _ensure_files()
    with open(AUDIT_FILE) as f:
        log = json.load(f)
    found = False
    for entry in log:
        if entry["id"] == log_entry_id and entry["status"] == "pending":
            entry["status"] = "completed"
            entry["details"] += " [Confirmed sent by reviewer]"
            found = True
    if found:
        with open(AUDIT_FILE, "w") as f:
            json.dump(log, f, indent=2)
    return found
