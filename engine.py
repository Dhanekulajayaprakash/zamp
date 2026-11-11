"""Deterministic vendor-onboarding rule engine.

Pipeline (each stage yields a result the UI can animate):
  1. Intake & completeness
  2. Tax ID validation
  3. Bank detail validation  (+ bank name lookup & cross-check)
  4. Payee name match (legal name vs. bank account holder)
  5. Cross-field consistency  (+ address postal code, email domain)
  6. Vendor registry & watchlist
  7. Decision  (+ risk score)

Every check has an `effect`:
  none   - informational / already covered elsewhere
  fix    - vendor can fix it  -> PENDING, ask the vendor
  review - needs a human      -> PENDING + manual-review flag
  block  - hard stop          -> REJECTED
"""
from __future__ import annotations

import re
import time
from difflib import SequenceMatcher

from data import ALL_DOCS, DOC_LABELS, REGISTRY, WATCHLIST
from validators import (COUNTRY_NAMES, TAX_VALIDATORS, bank_validate,
                         lookup_bank_name, validate_address,
                         validate_email_domain, extract_gstin_state)

FIELD_LABELS = {
    "legal_name": "legal business name", "country": "country of registration", "tax_id": "tax ID",
    "address": "registered address", "contact_name": "contact person name",
    "contact_email": "contact email address", "account_holder": "bank account holder name",
    "account_number": "bank account number / IBAN", "bank_code": "bank code (IFSC / routing / sort code)",
    "bank_country": "bank country",
}
REQUIRED = ["legal_name", "country", "tax_id", "address", "contact_name", "contact_email",
            "account_holder", "account_number", "bank_country"]
BANK_CODE_REQUIRED = {"IN", "US", "GB"}

SUFFIXES = {
    "private", "pvt", "limited", "ltd", "llc", "llp", "inc", "incorporated", "corp", "corporation",
    "co", "company", "gmbh", "ag", "pte", "plc", "sa", "sarl", "bv", "nv", "fze", "fzco", "lp", "pllc",
}
FREE_MAIL = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "proton.me", "icloud.com", "aol.com"}
SEVERITY = {"fail": 2, "warn": 1, "pass": 0}


# ---------------------------------------------------------------- helpers
def clean(sub: dict) -> dict:
    s = {k: (v.strip() if isinstance(v, str) else v) for k, v in sub.items()}
    s["country"] = (s.get("country") or "").upper()
    s["bank_country"] = (s.get("bank_country") or s["country"]).upper()
    s["tax_id"] = re.sub(r"\s+", "", (s.get("tax_id") or "")).upper()
    s["account_number"] = re.sub(r"[\s]", "", (s.get("account_number") or "")).upper()
    s["bank_code"] = (s.get("bank_code") or "").replace(" ", "").upper()
    s["documents"] = list(s.get("documents") or [])
    return s


def norm_name(name: str) -> str:
    s = name.lower().replace("&", " and ")
    s = re.sub(r"[^\w\s]", " ", s)
    tokens = s.split()
    kept = [t for t in tokens if t not in SUFFIXES]
    return " ".join(kept or tokens)


def name_similarity(a: str, b: str) -> float:
    na, nb = norm_name(a), norm_name(b)
    if not na or not nb:
        return 0.0
    plain = SequenceMatcher(None, na, nb).ratio()
    sorted_ = SequenceMatcher(None, " ".join(sorted(na.split())), " ".join(sorted(nb.split()))).ratio()
    return max(plain, sorted_)


def mask(account: str) -> str:
    return "•••• " + account[-4:] if len(account) > 4 else account


def domain(email: str) -> str:
    return email.split("@")[-1].lower() if "@" in email else ""


def chk(code, rule, status, detail, effect="none", vendor_ask=None):
    return {"code": code, "rule": rule, "status": status, "detail": detail,
            "effect": effect if status != "pass" else "none", "vendor_ask": vendor_ask}


def detect_tax_country(tax_id: str):
    for cc, (label, fn) in TAX_VALIDATORS.items():
        if fn(tax_id)[0]:
            return cc, label
    return None, None


def find_registry_vendor(sub):
    for v in REGISTRY:
        if v["tax_id"] == sub["tax_id"]:
            return v
    return None


# ---------------------------------------------------------------- stages
def stage_completeness(sub):
    out = []
    missing = [f for f in REQUIRED if not sub.get(f)]
    if sub["bank_country"] in BANK_CODE_REQUIRED and not sub.get("bank_code"):
        missing.append("bank_code")
    for f in missing:
        out.append(chk(f"missing:{f}", f"Required field: {FIELD_LABELS[f]}", "fail",
                       f"{FIELD_LABELS[f].capitalize()} was not provided.", "fix",
                       f"Please provide your {FIELD_LABELS[f]}."))
    if not missing:
        out.append(chk("fields_ok", "Required fields", "pass", "All required fields are filled in."))
    for d in ALL_DOCS:
        if d not in sub["documents"]:
            out.append(chk(f"missing_doc:{d}", f"Document: {DOC_LABELS[d]}", "fail",
                           f"{DOC_LABELS[d]} was not uploaded.", "fix",
                           f"Please upload: {DOC_LABELS[d]}."))
    if all(d in sub["documents"] for d in ALL_DOCS):
        out.append(chk("docs_ok", "Documents checklist", "pass", "All 3 required documents are attached."))
    email = sub.get("contact_email", "")
    if email:
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", email):
            out.append(chk("bad_email", "Contact email format", "fail", f"'{email}' is not a valid email address.",
                           "fix", "The contact email address you gave looks invalid - please send a working one."))
        else:
            out.append(chk("email_ok", "Contact email format", "pass", "Email address is well-formed."))
    return out


def stage_tax(sub):
    cc, t = sub["country"], sub["tax_id"]
    if not t:
        return [chk("tax_skipped", "Tax ID format", "warn", "Skipped - no tax ID provided (flagged in stage 1).")]
    if cc not in TAX_VALIDATORS:
        return [chk("tax_unsupported", "Tax ID format", "warn",
                    f"No automated tax-ID validator for {COUNTRY_NAMES.get(cc, cc)}; needs manual verification.", "review")]
    label, fn = TAX_VALIDATORS[cc]
    ok, why = fn(t)
    if ok:
        out = [chk("tax_ok", f"{label} validity ({cc})", "pass", f"{t}: {why}.")]
        # For Indian GSTIN, extract and show the state
        if cc == "IN":
            state = extract_gstin_state(t)
            if state:
                out.append(chk("gstin_state", "GSTIN state code", "pass",
                               f"State code {t[:2]} → {state}. PAN embedded: {t[2:12]}."))
        return out
    other_cc, other_label = detect_tax_country(t)
    if other_cc and other_cc != cc:
        return [chk("tax_format_other", f"{label} validity ({cc})", "fail",
                    f"{t} is not a valid {label}. It IS a valid {other_label} ({COUNTRY_NAMES[other_cc]}) - escalated in the cross-field check.")]
    return [chk("tax_invalid", f"{label} validity ({cc})", "fail", f"{t}: {why}.", "fix",
                f"The tax ID you entered ({t}) does not look like a valid {label}: {why}. "
                f"Please re-check it and attach your tax registration certificate.")]


def stage_bank(sub):
    if not sub.get("account_number"):
        return [chk("bank_skipped", "Bank detail format", "warn", "Skipped - no bank account provided (flagged in stage 1).")]
    supported, ok, why = bank_validate(sub["bank_country"], sub["account_number"], sub["bank_code"])
    if not supported:
        return [chk("bank_unsupported", "Bank detail format", "warn", why + "; needs manual verification.", "review")]
    if ok:
        out = [chk("bank_ok", f"Bank detail format ({sub['bank_country']})", "pass", why + ".")]
        # Bank name lookup and cross-check
        country = sub["bank_country"]
        found, resolved_name = lookup_bank_name(country, sub["bank_code"])
        if found and resolved_name:
            prefix = sub["bank_code"][:4]
            prefix_labels = {"IN": f"IFSC prefix {prefix}", "US": f"Routing prefix {prefix}",
                             "SG": f"SWIFT code {sub['bank_code']}"}
            prefix_label = prefix_labels.get(country, f"Bank code {sub['bank_code']}")
            out.append(chk("bank_name_resolved", "Bank name lookup", "pass",
                           f"{prefix_label} → {resolved_name}."))
            # Cross-check with vendor-provided bank_name
            vendor_bank = (sub.get("bank_name") or "").strip()
            if vendor_bank:
                sim = SequenceMatcher(None, resolved_name.lower(), vendor_bank.lower()).ratio()
                if sim >= 0.60:
                    out.append(chk("bank_name_match", "Bank name cross-check", "pass",
                                   f"Vendor said '{vendor_bank}', lookup says '{resolved_name}' (similarity {sim:.0%}). Consistent."))
                else:
                    out.append(chk("bank_name_mismatch", "Bank name cross-check", "warn",
                                   f"Vendor said '{vendor_bank}' but code resolves to '{resolved_name}' (similarity {sim:.0%}). "
                                   f"Possible wrong bank code or typo.", "review"))
        return out
    return [chk("bank_invalid", f"Bank detail format ({sub['bank_country']})", "fail", why + ".", "fix",
                f"The bank details did not pass our format checks: {why}. Please re-check and resend, with a bank letter or cancelled cheque.")]


def stage_name_match(sub):
    a, b = sub.get("legal_name", ""), sub.get("account_holder", "")
    if not a or not b:
        return [chk("name_skipped", "Payee name match", "warn", "Skipped - a name is missing (flagged in stage 1).")]
    na, nb = norm_name(a), norm_name(b)
    sim = name_similarity(a, b)
    norm_note = f"Compared as '{na}' vs '{nb}' after ignoring case, punctuation and legal suffixes (Pvt/Ltd/LLC/Inc/GmbH...)."
    if na == nb:
        return [chk("holder_ok", "Payee name match", "pass", f"Match. {norm_note}")]
    if sim >= 0.9:
        return [chk("holder_ok", "Payee name match", "pass", f"Near-identical (similarity {sim:.0%}). {norm_note}")]
    if sim >= 0.7:
        return [chk("holder_name_partial", "Payee name match", "warn",
                    f"Partial match (similarity {sim:.0%}) between '{a}' and '{b}'. Possible abbreviation or trade name; human should confirm.",
                    "review", f"Please send a bank letter confirming the account is held in the name of {a}.")]
    return [chk("holder_name_mismatch", "Payee name match", "fail",
                f"Bank account holder '{b}' does not match legal name '{a}' (similarity {sim:.0%}). Payment would go to a different party - third-party/mule-account pattern.",
                "review", f"The bank account must be in the name of your registered business, {a}. "
                          f"Please send a bank letter confirming this, or give us a different account.")]


def stage_cross(sub):
    out = []
    cc, t = sub["country"], sub["tax_id"]

    # Tax ID vs country
    if t and cc in TAX_VALIDATORS and not TAX_VALIDATORS[cc][1](t)[0]:
        other_cc, other_label = detect_tax_country(t)
        if other_cc and other_cc != cc:
            out.append(chk("tax_country_mismatch", "Tax ID country vs. vendor country", "fail",
                           f"Vendor claims to be registered in {COUNTRY_NAMES.get(cc, cc)}, but the tax ID is a valid {other_label} "
                           f"for {COUNTRY_NAMES[other_cc]}. Either a data-entry error or a misrepresented entity.",
                           "review", f"The tax ID on your form is in {COUNTRY_NAMES[other_cc]} format, but you gave "
                                     f"{COUNTRY_NAMES.get(cc, cc)} as your country of registration. Please confirm which is correct and attach your registration certificate."))
    elif t:
        out.append(chk("tax_country_ok", "Tax ID country vs. vendor country", "pass",
                       "Tax ID format is consistent with the declared country."))

    # Bank country vs vendor country
    if sub["bank_country"] != cc:
        out.append(chk("bank_country_mismatch", "Bank country vs. vendor country", "warn",
                       f"Vendor is in {COUNTRY_NAMES.get(cc, cc)} but the bank account is in {COUNTRY_NAMES.get(sub['bank_country'], sub['bank_country'])}. "
                       "Legitimate sometimes (offshore accounts) but a common fraud signal.",
                       "review", f"Your bank account is in {COUNTRY_NAMES.get(sub['bank_country'], sub['bank_country'])}, outside your country of registration. "
                                 "Please tell us why and attach supporting documents."))
    else:
        out.append(chk("bank_country_ok", "Bank country vs. vendor country", "pass", "Bank is in the same country as the vendor."))

    # Address postal code check
    address = sub.get("address", "")
    if address:
        addr_ok, addr_why = validate_address(cc, address)
        if addr_ok:
            out.append(chk("address_postal_ok", "Address postal code", "pass", f"{addr_why} for {COUNTRY_NAMES.get(cc, cc)}."))
        else:
            out.append(chk("address_postal_missing", "Address postal code", "warn",
                           f"{addr_why} for {COUNTRY_NAMES.get(cc, cc)}. Advisory - may need manual check.", "none"))

    # Email domain vs company name
    email = sub.get("contact_email", "")
    d = domain(email)
    if d in FREE_MAIL:
        out.append(chk("free_mail", "Contact email domain", "warn",
                       f"Business contact uses a free mailbox ({d}). Advisory only.", "none"))
    elif email:
        match_type, match_detail = validate_email_domain(email, sub.get("legal_name", ""))
        if match_type == "match":
            out.append(chk("email_domain_match", "Email domain vs. company name", "pass", match_detail))
        elif match_type == "no_match":
            out.append(chk("email_domain_no_match", "Email domain vs. company name", "warn",
                           f"{match_detail}. Could be legitimate (holding company, DBA), but worth verifying.", "none"))
    return out


def stage_registry(sub):
    out = []
    hits = []
    for w in WATCHLIST:
        if w["type"] == "account" and sub["account_number"] == w["value"]:
            hits.append(w)
        elif w["type"] == "tax_id" and sub["tax_id"] == w["value"]:
            hits.append(w)
        elif w["type"] == "name" and norm_name(sub.get("legal_name", "")) == w["value"]:
            hits.append(w)
    if hits:
        out.append(chk("watchlist", "Internal watchlist", "fail",
                       "HIT - " + "; ".join(h["reason"] for h in hits) + ". Do NOT disclose the reason to the vendor.", "block"))
    else:
        out.append(chk("watchlist_ok", "Internal watchlist", "pass", "No match on account, tax ID or entity name."))

    v = find_registry_vendor(sub)
    if v:
        same_acct = v["account_number"] == sub["account_number"]
        if same_acct:
            out.append(chk("duplicate", "Duplicate vendor", "fail",
                           f"Tax ID {sub['tax_id']} and bank account already belong to active vendor {v['id']} ({v['name']}, onboarded {v['onboarded']}).",
                           "block"))
        else:
            out.append(chk("bank_change", "Bank details changed on existing vendor", "fail",
                           f"Tax ID matches active vendor {v['id']} ({v['name']}) but the bank account changed from {mask(v['account_number'])} "
                           f"to {mask(sub['account_number'])}. Bank-detail change requests are the #1 vector for payment fraud (BEC); "
                           f"verify by call-back to the number ON FILE before changing anything.", "review"))
        if domain(sub.get("contact_email", "")) != domain(v["contact_email"]):
            out.append(chk("contact_domain_change", "Contact email domain vs. vendor on file", "fail",
                           f"Submitter's email domain '{domain(sub['contact_email'])}' differs from the registered domain "
                           f"'{domain(v['contact_email'])}' (look-alike domain?).", "review"))
        if same_acct is False and norm_name(sub["legal_name"]) != norm_name(v["name"]):
            out.append(chk("name_change", "Legal name vs. vendor on file", "warn",
                           f"Name differs from the record on file ('{v['name']}').", "review"))
    else:
        out.append(chk("registry_new", "Existing vendor lookup", "pass", "No existing vendor with this tax ID - new vendor."))
        for r in REGISTRY:
            if name_similarity(sub.get("legal_name", ""), r["name"]) >= 0.92:
                out.append(chk("similar_vendor", "Similar existing vendor name", "warn",
                               f"Name is almost identical to existing vendor {r['id']} ({r['name']}) but with a different tax ID.", "review"))
    return out


STAGES = [
    ("completeness", "1. Intake & completeness", stage_completeness),
    ("tax", "2. Tax ID validation", stage_tax),
    ("bank", "3. Bank detail validation", stage_bank),
    ("name", "4. Payee name match", stage_name_match),
    ("cross", "5. Cross-field consistency", stage_cross),
    ("registry", "6. Registry & watchlist", stage_registry),
]


# ---------------------------------------------------------------- risk score
def _compute_risk(sub, checks):
    score = 0
    for c in checks:
        if c["status"] == "pass":
            continue
        eff = c["effect"]
        if eff == "block":
            score += 40
        elif eff == "review":
            score += 20
        elif eff == "fix":
            score += 10
        code = c["code"]
        if code == "free_mail":
            score += 5
        if code == "bank_country_mismatch":
            score += 15
        if code == "bank_change":
            score += 25
        if code == "contact_domain_change":
            score += 20
        if code == "watchlist":
            score += 50
    return min(score, 100)


def _risk_label(score: int) -> str:
    if score <= 20:
        return "Low"
    elif score <= 45:
        return "Medium"
    elif score <= 70:
        return "High"
    return "Critical"


# ---------------------------------------------------------------- decision
def decide(sub, stages, previous=None):
    checks = [c for s in stages for c in s["checks"]]
    blocks = [c for c in checks if c["status"] != "pass" and c["effect"] == "block"]
    fixes = [c for c in checks if c["status"] != "pass" and c["effect"] == "fix"]
    reviews = [c for c in checks if c["status"] != "pass" and c["effect"] == "review"]
    advisories = [c for c in checks if c["status"] != "pass" and c["effect"] == "none" and c["code"] not in
                  ("tax_format_other", "tax_skipped", "bank_skipped", "name_skipped")]
    vendor = find_registry_vendor(sub)

    if blocks:
        status = "REJECTED"
        headline = f"Rejected: {blocks[0]['rule'].lower()}."
        next_step = "Stop. No vendor record is created. Escalate to Vendor Master Data / Risk; send the vendor a neutral decline."
    elif fixes or reviews:
        status = "PENDING"
        parts = []
        if fixes:
            parts.append(f"{len(fixes)} item(s) need the vendor to fix or provide")
        if reviews:
            parts.append(f"{len(reviews)} item(s) need internal review")
        headline = "Pending: " + " and ".join(parts) + "."
        if reviews:
            next_step = ("Hold payment enablement. Route to Vendor Master Data / Fraud Ops for manual review"
                         + (" (verify bank change by call-back to the number on file)." if any(c["code"] == "bank_change" for c in reviews) else "."))
        else:
            next_step = "Waiting on the vendor. Auto-re-run the pipeline when they respond."
    else:
        status = "APPROVED"
        headline = "Approved: all checks passed."
        next_step = "Create the vendor record in the ERP and enable for payment run."

    reasons = [c for c in blocks + reviews + fixes]
    codes = [c["code"] for c in reasons]
    risk_score = _compute_risk(sub, checks)
    risk_label = _risk_label(risk_score)

    d = {
        "status": status, "manual_review": bool(reviews or blocks), "headline": headline, "next_step": next_step,
        "reasons": reasons, "advisories": advisories, "issue_codes": codes,
        "matched_vendor": vendor["id"] if vendor else None,
        "n_checks": len(checks), "n_passed": sum(1 for c in checks if c["status"] == "pass"),
        "risk_score": risk_score, "risk_label": risk_label,
    }
    if vendor and any(c in codes for c in ("bank_change", "contact_domain_change")):
        d["email_to"] = vendor["contact_email"]
        d["email_to_name"] = vendor["contact_name"]
        d["email_to_note"] = "Sent to the contact ON FILE, not the submitter (possible account takeover)."
    else:
        d["email_to"] = sub.get("contact_email") or "(no email provided)"
        d["email_to_name"] = sub.get("contact_name") or "there"
        d["email_to_note"] = "" if sub.get("contact_email") else "No contact email was provided - route via the procurement owner."
    if previous:
        prev_reasons = previous.get("reasons", [])
        d["resolved"] = [r["rule"] for r in prev_reasons if r["code"] not in codes]
        d["still_open"] = [r["rule"] for r in prev_reasons if r["code"] in codes]
        d["new_issues"] = [c["rule"] for c in reasons if c["code"] not in {r["code"] for r in prev_reasons}]
    return d


def stage_status(checks):
    worst = max((SEVERITY[c["status"]] for c in checks), default=0)
    return {2: "fail", 1: "warn", 0: "pass"}[worst]


def iter_stages(submission):
    """Yield one finished stage at a time (UI animates between yields)."""
    sub = clean(submission)
    for key, title, fn in STAGES:
        t0 = time.perf_counter()
        checks = fn(sub)
        yield {"key": key, "title": title, "checks": checks, "status": stage_status(checks),
               "ms": round((time.perf_counter() - t0) * 1000, 2)}


def run_pipeline(submission, previous=None):
    """One-shot run. Returns {'submission','stages','decision'}."""
    sub = clean(submission)
    stages = list(iter_stages(submission))
    return {"submission": sub, "stages": stages, "decision": decide(sub, stages, previous)}
