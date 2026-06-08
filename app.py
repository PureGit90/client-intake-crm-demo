"""
Client Intake, Document Reminder & CRM Workflow Demo
=====================================================
Demonstrates all three workflow stages end-to-end on dummy data.

Tab 1 — Client Intake
Tab 2 — Document Checklist & Reminders
Tab 3 — CRM Log
"""

import os
from datetime import datetime, timezone

import streamlit as st
from dotenv import load_dotenv

import crm
import documents
import intake

load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Client Intake & CRM Workflows",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        key = st.session_state.get("api_key", "")
    return key


def mask_email(email: str) -> str:
    """Mask email for audit log — data protection."""
    if "@" not in email:
        return "[masked]"
    local, domain = email.split("@", 1)
    masked_local = local[:2] + "***" if len(local) > 2 else "***"
    return f"{masked_local}@{domain}"


# ── Sidebar — API Key & data protection notice ────────────────────────────────
with st.sidebar:
    st.markdown("## Configuration")
    if not os.getenv("ANTHROPIC_API_KEY"):
        api_key_input = st.text_input(
            "Anthropic API Key",
            type="password",
            help="Enter your Anthropic API key. Not stored — session only.",
        )
        if api_key_input:
            st.session_state["api_key"] = api_key_input
            st.success("API key set for this session.")
    else:
        st.success("API key loaded from environment.")

    st.divider()
    st.markdown("### Data Protection")
    st.info(
        "**Demo mode:** All data shown is sample/dummy data only.\n\n"
        "No real PII is stored or transmitted.\n\n"
        "In production: GDPR-compliant, encrypted at rest, data processing "
        "agreements in place, and all PII handled per UK/EU data protection law."
    )
    st.divider()
    st.markdown("### Architecture")
    st.markdown(
        "```\n"
        "Intake form\n"
        "  → Claude extract\n"
        "    → CRM JSON record\n"
        "      → Doc checklist\n"
        "        → Claude reminder\n"
        "          → Human review gate\n"
        "            → Audit log\n"
        "```"
    )

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Client Intake, Document Reminder & CRM Workflows")
st.caption("AI-powered client onboarding — intake extraction · document chasing · full audit trail")

st.info(
    "**Demo Notice:** This demo uses sample data only. "
    "No real client information is used or stored. "
    "All AI processing is performed via Anthropic's API on dummy records.",
    icon="🔒",
)

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(
    ["📋 Client Intake", "📁 Document Checklist & Reminders", "📊 CRM Log"]
)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CLIENT INTAKE
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("New Client Intake")
    st.markdown(
        "Fill in the form below. Claude will extract and structure the intake, "
        "then you can save it to the CRM."
    )

    st.info(
        "**Data Protection Notice:** Only sample data is used in this demo. "
        "In production, all PII is handled per GDPR/data processing agreement "
        "and is never stored in plain text logs.",
        icon="🔒",
    )

    with st.form("intake_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Full Name *", placeholder="e.g. Alex Johnson")
            company = st.text_input("Company *", placeholder="e.g. Acme Ltd")
            email = st.text_input("Email *", placeholder="alex@acmeltd.co.uk")

        with col2:
            phone = st.text_input("Phone", placeholder="+44 7700 900000")
            service = st.selectbox(
                "Service Requested *",
                ["CRM Setup", "Email Automation", "Document Workflow", "Other"],
            )
            notes = st.text_area(
                "Notes (optional)",
                placeholder="Any additional context about the client's needs...",
                height=100,
            )

        submitted = st.form_submit_button("Process Intake", type="primary", use_container_width=True)

    if submitted:
        if not name or not company or not email:
            st.error("Please fill in Name, Company, and Email before submitting.")
        else:
            api_key = get_api_key()
            if not api_key:
                st.error("Please enter your Anthropic API key in the sidebar.")
            else:
                with st.spinner("Processing intake with Claude..."):
                    form_data = {
                        "name": name,
                        "company": company,
                        "email": email,
                        "phone": phone,
                        "service_requested": service,
                        "notes": notes,
                    }
                    try:
                        structured = intake.extract_intake(form_data, api_key)
                        st.session_state["pending_intake"] = structured
                        st.session_state["pending_intake_raw_email"] = email
                    except Exception as e:
                        st.error(f"Claude extraction failed: {e}")
                        structured = None

                if st.session_state.get("pending_intake"):
                    st.success("Intake processed successfully.")

    # Show structured profile if available
    if st.session_state.get("pending_intake"):
        s = st.session_state["pending_intake"]
        st.markdown("---")
        st.markdown("### Structured Client Profile")
        st.markdown("*Extracted and structured by Claude. Review before saving.*")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Name", s.get("name", "—"))
            st.metric("Company", s.get("company", "—"))
        with col2:
            st.metric("Service", s.get("service_requested", "—"))
            st.metric("Intake Date", s.get("intake_date", "—"))
        with col3:
            st.metric("Phone", s.get("phone") or "—")
            st.metric("Email", "✉ [on file]")

        if s.get("notes"):
            st.markdown(f"**Notes:** {s['notes']}")

        docs = s.get("docs_required", [])
        if docs:
            st.markdown("**Documents Required:**")
            for doc in docs:
                st.markdown(f"- {doc}")

        col_save, col_clear = st.columns([1, 4])
        with col_save:
            if st.button("Save to CRM", type="primary"):
                try:
                    record = crm.create_client(s)
                    st.session_state["last_saved_client"] = record
                    st.session_state.pop("pending_intake", None)
                    st.success(f"Saved! Client ID: `{record['id']}`")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save: {e}")
        with col_clear:
            if st.button("Clear"):
                st.session_state.pop("pending_intake", None)
                st.rerun()

    if st.session_state.get("last_saved_client"):
        saved = st.session_state["last_saved_client"]
        st.success(f"Last saved: **{saved['name']}** ({saved['company']}) — ID `{saved['id']}`")

    # Show existing clients summary
    st.markdown("---")
    st.markdown("### Existing CRM Clients")
    clients = crm.get_clients()
    if clients:
        for c in clients:
            missing = documents.get_missing_docs(c)
            status_icon = "✅" if not missing else ("⚠️" if len(missing) < len(c.get("docs_required", [])) else "🔴")
            with st.expander(f"{status_icon} {c['name']} — {c['company']} ({c['service_requested']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**ID:** `{c['id']}`")
                    st.write(f"**Status:** {c.get('status', 'active')}")
                    st.write(f"**Intake Date:** {c.get('intake_date', '—')}")
                with col2:
                    submitted_count = len(c.get("docs_submitted", []))
                    required_count = len(c.get("docs_required", []))
                    st.write(f"**Docs:** {submitted_count}/{required_count} submitted")
                    if missing:
                        st.write(f"**Missing:** {', '.join(missing)}")
    else:
        st.info("No clients in CRM yet. Submit an intake above to get started.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DOCUMENT CHECKLIST & REMINDERS
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Document Checklist & Reminder Emails")
    st.markdown(
        "Select a client to see their document status. "
        "For clients with missing documents, generate a polite reminder email and route it through the human review gate."
    )

    clients = crm.get_clients()
    if not clients:
        st.info("No clients found. Add one via the Intake tab first.")
    else:
        client_options = {f"{c['name']} — {c['company']}": c for c in clients}
        selected_label = st.selectbox("Select Client", list(client_options.keys()))
        selected_client = client_options[selected_label]

        st.markdown("---")
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown(f"### {selected_client['name']}")
            st.markdown(f"**Company:** {selected_client['company']}")
            st.markdown(f"**Service:** {selected_client['service_requested']}")
            st.markdown(f"**Status:** {selected_client.get('status', 'active').title()}")

        with col2:
            st.markdown("### Document Checklist")
            doc_status = documents.get_doc_status(selected_client)
            for doc in doc_status:
                icon = "✅" if doc["submitted"] else "❌"
                label = doc["name"]
                status_text = "Submitted" if doc["submitted"] else "**Missing**"
                st.markdown(f"{icon} {label} — {status_text}")

        missing = documents.get_missing_docs(selected_client)

        st.markdown("---")
        if not missing:
            st.success("All documents submitted for this client. No reminder needed.")
        else:
            st.warning(f"{len(missing)} document(s) outstanding: {', '.join(missing)}")

            api_key = get_api_key()
            if not api_key:
                st.error("Please enter your Anthropic API key in the sidebar to draft reminders.")
            else:
                draft_key = f"draft_{selected_client['id']}"
                log_key = f"log_entry_{selected_client['id']}"

                if st.button("Draft Reminder Email", type="primary"):
                    with st.spinner("Drafting reminder email with Claude..."):
                        try:
                            draft = documents.draft_reminder(selected_client, missing, api_key)
                            st.session_state[draft_key] = draft
                        except Exception as e:
                            st.error(f"Failed to draft reminder: {e}")

                if st.session_state.get(draft_key):
                    draft = st.session_state[draft_key]

                    st.markdown("#### Drafted Reminder Email")
                    st.caption("Review and edit before approving for send.")

                    subject_edit = st.text_input(
                        "Subject",
                        value=draft["subject"],
                        key=f"subject_{selected_client['id']}",
                    )
                    body_edit = st.text_area(
                        "Email Body",
                        value=draft["body"],
                        height=250,
                        key=f"body_{selected_client['id']}",
                    )

                    st.info(
                        "**Human Review Gate:** This email will be logged as 'Pending Send' until you "
                        "confirm it in the CRM Log tab. No email is dispatched automatically.",
                        icon="🔐",
                    )

                    col_approve, col_discard = st.columns([1, 4])
                    with col_approve:
                        if st.button("Log as Sent (Pending Approval)", type="primary", key=f"approve_{selected_client['id']}"):
                            # Log to audit — mask the email for data protection
                            masked = mask_email(selected_client.get("email", ""))
                            details = (
                                f"Reminder drafted for missing docs: {', '.join(missing)}. "
                                f"Email sent to: {masked}. "
                                f"Subject: {subject_edit}"
                            )
                            entry = crm.log_action(
                                client_id=selected_client["id"],
                                action="reminder_logged_pending",
                                details=details,
                                status="pending",
                                client_name=selected_client["name"],
                            )
                            st.session_state[log_key] = entry["id"]
                            st.session_state.pop(draft_key, None)
                            st.success(
                                f"Logged as pending. Go to **CRM Log** tab to confirm and mark as sent. "
                                f"Log entry ID: `{entry['id'][:8]}...`"
                            )
                            st.rerun()

                    with col_discard:
                        if st.button("Discard Draft", key=f"discard_{selected_client['id']}"):
                            st.session_state.pop(draft_key, None)
                            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CRM LOG
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("CRM Audit Log")
    st.markdown(
        "Full record of all actions taken in this session and from sample data. "
        "Pending reminder approvals can be confirmed here."
    )

    st.info(
        "**Data Protection:** Email addresses are masked in this log. "
        "Raw PII is never stored in audit records.",
        icon="🔒",
    )

    col_refresh, col_filter = st.columns([1, 3])
    with col_refresh:
        if st.button("Refresh Log"):
            st.rerun()
    with col_filter:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All", "completed", "pending"],
            key="log_filter",
        )

    audit = crm.get_audit_log()
    if filter_status != "All":
        audit = [e for e in audit if e.get("status") == filter_status]

    # Show in reverse chronological order
    audit = list(reversed(audit))

    if not audit:
        st.info("No log entries yet.")
    else:
        # Pending reminders get special treatment
        pending = [e for e in audit if e.get("status") == "pending"]
        if pending:
            st.markdown("### Pending Approvals")
            for entry in pending:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 3, 1])
                    with col1:
                        ts = entry.get("timestamp", "")
                        if ts:
                            try:
                                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                                ts = dt.strftime("%Y-%m-%d %H:%M UTC")
                            except Exception:
                                pass
                        st.markdown(f"**{entry.get('client_name', '—')}**")
                        st.caption(ts)
                    with col2:
                        st.markdown(f"*{entry.get('details', '—')}*")
                    with col3:
                        if st.button("Mark as Sent", key=f"marksent_{entry['id']}", type="primary"):
                            success = crm.mark_reminder_sent(entry["id"])
                            if success:
                                st.success("Marked as sent.")
                                st.rerun()
                            else:
                                st.error("Could not update entry.")
            st.divider()

        # Full log table
        st.markdown("### Full Audit Log")
        import pandas as pd

        rows = []
        for entry in audit:
            ts = entry.get("timestamp", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    ts = dt.strftime("%Y-%m-%d %H:%M UTC")
                except Exception:
                    pass
            action_display = entry.get("action", "").replace("_", " ").title()
            rows.append({
                "Timestamp": ts,
                "Client": entry.get("client_name", "—"),
                "Action": action_display,
                "Details": entry.get("details", "—"),
                "Status": entry.get("status", "—").title(),
            })

        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Timestamp": st.column_config.TextColumn("Timestamp", width="small"),
                "Client": st.column_config.TextColumn("Client", width="small"),
                "Action": st.column_config.TextColumn("Action", width="medium"),
                "Details": st.column_config.TextColumn("Details", width="large"),
                "Status": st.column_config.TextColumn("Status", width="small"),
            },
        )

        st.caption(f"Showing {len(rows)} log entries.")
