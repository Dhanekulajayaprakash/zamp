"""Vendor email drafting.

The ONLY place an LLM is used. Decisions come from engine.py (deterministic);
the model just turns structured facts into a polite email. Guardrails:
  * the model gets vendor-safe text only (never watchlist reasons / internal detail)
  * output is checked for forbidden words and leaked account numbers
  * any failure -> deterministic template, so the pipeline never breaks
"""
from __future__ import annotations

import json
import os
import re

MODEL = os.environ.get("VENDOR_LLM_MODEL", "gemini-1.5-flash")
FORBIDDEN = ["watchlist", "blocklist", "fraud", "suspicious", "sanction", "debar", "mule", "risk score", "compromise"]
COMPANY = "Acme Procurement"  # the (fictional) buyer


def _api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def _facts(sub, decision):
    codes = set(decision["issue_codes"])
    if decision["status"] == "REJECTED":
        mode = "decline"
        asks = []
    elif decision["status"] == "APPROVED":
        mode = "welcome"
        asks = []
    elif codes & {"bank_change", "contact_domain_change"}:
        mode = "verify_bank_change"
        asks = []
    else:
        mode = "request_info"
        asks = [r["vendor_ask"] for r in decision["reasons"] if r.get("vendor_ask")]
    return {
        "mode": mode, "buyer": COMPANY, "vendor_name": sub.get("legal_name"),
        "contact_name": decision.get("email_to_name") or "there", "requests": asks,
        "resolved_since_last_time": decision.get("resolved", []),
    }


def _template(facts):
    n, v = facts["contact_name"], facts["vendor_name"]
    if facts["mode"] == "welcome":
        return (f"Welcome to {COMPANY} - {v} is approved",
                f"Hi {n},\n\nThanks for completing onboarding. {v} has been approved as a vendor with {COMPANY}, "
                "and you will be able to receive purchase orders and payments shortly. Your procurement contact will be in touch.\n\n"
                f"Best regards,\nVendor Onboarding Team, {COMPANY}")
    if facts["mode"] == "decline":
        return (f"Update on your vendor application - {v}",
                f"Hi {n},\n\nThank you for your interest in working with {COMPANY}. After review, we are unable to proceed "
                "with this vendor application at this time. If you believe this is a mistake, please contact your "
                "procurement contact at our company directly.\n\n"
                f"Best regards,\nVendor Onboarding Team, {COMPANY}")
    if facts["mode"] == "verify_bank_change":
        return (f"Action needed: please confirm a banking-details change for {v}",
                f"Hi {n},\n\nWe received a request to update the bank account and contact details on file for {v}. "
                "As a security precaution we do not change payment details from an emailed request alone. "
                "Please call your procurement contact at the phone number you already have for us, or reply from your "
                "registered email, to confirm whether this change was made by you. Until it is confirmed, payments will "
                "continue to go to the existing account.\n\nIf you did not request this change, please let us know right away.\n\n"
                f"Best regards,\nVendor Onboarding Team, {COMPANY}")
    items = "\n".join(f"  {i}. {a}" for i, a in enumerate(facts["requests"], 1))
    resolved = ""
    if facts["resolved_since_last_time"]:
        resolved = "Thank you - we have received the following from your last submission: " + \
                   "; ".join(r.lower() for r in facts["resolved_since_last_time"]) + ".\n\n"
    return (f"Action needed to complete your onboarding - {v}",
            f"Hi {n},\n\nThanks for submitting your details. {resolved}To finish onboarding {v} we still need:\n\n{items}\n\n"
            "You can reply to this email with the corrected information or documents, and we will re-check right away.\n\n"
            f"Best regards,\nVendor Onboarding Team, {COMPANY}")


def _llm(facts):
    key = _api_key()
    if not key:
        return None
    from google import genai
    client = genai.Client(api_key=key)
    system = (
        f"You write short, warm, professional emails from the vendor-onboarding team at {COMPANY}. "
        "Use ONLY the facts in the JSON. Do not invent requirements, deadlines or reasons. Never mention fraud, risk, "
        "watchlists, internal checks, or other vendors. Never include bank account numbers. "
        "mode=welcome: confirm approval. mode=decline: neutral, brief decline with no reason. "
        "mode=verify_bank_change: say a request to change banking details was received, that for security we confirm by "
        "phone using the number already on file, and payments continue to the existing account until then. "
        "mode=request_info: list each request as a numbered item, and if resolved_since_last_time is non-empty, thank them "
        "for those. Under 150 words. Reply as: first line 'Subject: ...', blank line, then the body."
    )
    response = client.models.generate_content(
        model=MODEL,
        contents=json.dumps(facts),
        config=genai.types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=500,
            temperature=0.3,
        ),
    )
    text = response.text.strip()
    m = re.match(r"Subject:\s*(.+?)\n+(.*)", text, re.S)
    if not m:
        return None
    return m.group(1).strip(), m.group(2).strip()


def _safe(body, subj, sub, facts):
    low = (subj + " " + body).lower()
    if any(w in low for w in FORBIDDEN):
        return False
    if sub.get("account_number") and sub["account_number"] in body:
        return False
    if facts["mode"] == "request_info" and len(body.split()) < 20:
        return False
    return True


def draft_email(sub, decision):
    facts = _facts(sub, decision)
    by, subject, body = "template", None, None
    try:
        out = _llm(facts)
        if out and _safe(out[1], out[0], sub, facts):
            subject, body = out
            by = f"LLM ({MODEL})"
    except Exception as e:  # network, quota, bad key - never break the pipeline
        by = f"template (LLM unavailable: {type(e).__name__})"
    if subject is None:
        subject, body = _template(facts)
        if by == "template" and _api_key():
            by = "template (LLM output failed safety check)"
    return {"to": decision["email_to"], "to_note": decision.get("email_to_note", ""),
            "subject": subject, "body": body, "drafted_by": by, "mode": facts["mode"]}
