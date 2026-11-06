"""Vendor Onboarding Validator - Streamlit UI (live run view + dashboard of past runs)."""
from __future__ import annotations

import time
from collections import Counter

import pandas as pd
import streamlit as st

import db
from data import ALL_DOCS, DOC_LABELS, SCENARIOS, SCENARIOS_BY_KEY
from engine import iter_stages, decide, clean, run_pipeline
from messages import MODEL, _api_key, draft_email
from validators import COUNTRY_NAMES

st.set_page_config(page_title="Vendor Onboarding Validator", page_icon="🧾", layout="wide")

ICON = {"pass": "✅", "warn": "⚠️", "fail": "❌"}
STATUS_ICON = {"APPROVED": "🟢", "PENDING": "🟠", "REJECTED": "🔴"}
EFFECT_TAG = {"fix": "vendor to fix", "review": "needs human review", "block": "HARD STOP", "none": ""}
FIELDS = ["legal_name", "country", "tax_id", "address", "contact_name", "contact_email",
          "bank_country", "bank_name", "account_holder", "account_number", "bank_code", "documents"]
BLANK = {"legal_name": "", "country": "IN", "tax_id": "", "address": "", "contact_name": "", "contact_email": "",
         "bank_country": "IN", "bank_name": "", "account_holder": "", "account_number": "", "bank_code": "",
         "documents": list(ALL_DOCS)}
COUNTRIES = list(COUNTRY_NAMES)

st.markdown(
    """<style>
    .block-container {padding-top: 2rem; max-width: 1200px;}
    .pill {display:inline-block; padding:2px 10px; border-radius:999px; font-size:.8rem; font-weight:600;}
    .pill.APPROVED {background:#d1fae5; color:#065f46;} .pill.PENDING {background:#ffedd5; color:#9a3412;}
    .pill.REJECTED {background:#fee2e2; color:#991b1b;}
    </style>""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------ core processing
def process(sub: dict, scenario: str | None = None) -> int:
    """Run the whole pipeline once for a submission and persist it. Returns run id."""
    t0 = time.perf_counter()
    sub = clean(sub)
    prev_run = db.latest_run_for(sub["legal_name"], sub["country"])
    previous = prev_run["result"]["decision"] if prev_run and prev_run["status"] == "PENDING" else None
    result = run_pipeline(sub, previous)
    email = draft_email(sub, result["decision"])
    ms = (time.perf_counter() - t0) * 1000
    return db.save_run(sub, result["stages"], result["decision"], email, scenario, round(ms, 1))


def load_scenario():
    key = st.session_state.scenario_pick
    data = BLANK if key == "blank" else SCENARIOS_BY_KEY[key]["submission"]
    for f in FIELDS:
        st.session_state[f"f_{f}"] = list(data[f]) if f == "documents" else data.get(f, "")
    st.session_state.loaded_scenario = None if key == "blank" else key


def seed_history():
    for s in SCENARIOS:
        process(s["submission"], s["key"])


for f in FIELDS:
    st.session_state.setdefault(f"f_{f}", BLANK[f])
st.session_state.setdefault("loaded_scenario", None)
st.session_state.setdefault("last_run_id", None)
st.session_state.setdefault("animate", False)


# ------------------------------------------------------------------ renderers
def render_stage(stage: dict, container):
    with container.container(border=True):
        st.markdown(f"**{ICON[stage['status']]} {stage['title']}** &nbsp; <span style='color:gray;font-size:.8rem'>{stage['ms']} ms</span>",
                    unsafe_allow_html=True)
        for c in stage["checks"]:
            tag = EFFECT_TAG[c["effect"]]
            tag = f" &nbsp;`{tag}`" if tag else ""
            st.markdown(f"{ICON[c['status']]} **{c['rule']}**{tag}  \n<span style='color:gray'>{c['detail']}</span>",
                        unsafe_allow_html=True)


def render_decision(d: dict):
    box = {"APPROVED": st.success, "PENDING": st.warning, "REJECTED": st.error}[d["status"]]
    box(f"### {STATUS_ICON[d['status']]} {d['status']}\n{d['headline']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Checks passed", f"{d['n_passed']}/{d['n_checks']}")
    c2.metric("Manual review needed", "Yes" if d["manual_review"] else "No")
    c3.metric("Matched existing vendor", d["matched_vendor"] or "-")
    st.markdown(f"**Next step:** {d['next_step']}")
    if "resolved" in d:
        st.markdown("**Compared with the previous submission from this vendor**")
        a, b, c = st.columns(3)
        a.markdown("✅ **Resolved**\n\n" + ("\n".join(f"- {x}" for x in d["resolved"]) or "- none"))
        b.markdown("⏳ **Still open**\n\n" + ("\n".join(f"- {x}" for x in d["still_open"]) or "- none"))
        c.markdown("🆕 **New issues**\n\n" + ("\n".join(f"- {x}" for x in d["new_issues"]) or "- none"))
    if d["reasons"]:
        st.markdown("**Why**")
        for r in d["reasons"]:
            st.markdown(f"- `{EFFECT_TAG[r['effect']]}` **{r['rule']}** - {r['detail']}")


def render_email(e: dict | None):
    if not e:
        return
    with st.container(border=True):
        st.markdown(f"**✉️ Drafted vendor email** &nbsp; <span style='color:gray;font-size:.8rem'>drafted by: {e['drafted_by']}</span>",
                    unsafe_allow_html=True)
        st.markdown(f"**To:** {e['to']}" + (f"  \n<span style='color:#b45309'>⚠ {e['to_note']}</span>" if e.get("to_note") else ""),
                    unsafe_allow_html=True)
        st.markdown(f"**Subject:** {e['subject']}")
        st.text(e["body"])


def render_run(run: dict, animate: bool):
    sub, res = run["submission"], run["result"]
    st.subheader(f"{run['legal_name']}  ·  {COUNTRY_NAMES.get(run['country'], run['country'])}")
    st.caption(f"Run #{run['id']} · {run['created_at']} · {run['duration_ms']:.0f} ms total")
    for stg in res["stages"]:
        slot = st.empty()
        if animate:
            slot.info(f"⏳ Running {stg['title']} ...")
            time.sleep(0.55)
        render_stage(stg, slot)
    if animate:
        time.sleep(0.3)
    render_decision(res["decision"])
    render_email(run["email"])
    with st.expander("Raw submission (JSON)"):
        st.json(sub)


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.title("🧾 Vendor Onboarding")
    st.caption("Validates a new-vendor submission, decides Approve / Pending / Reject, and drafts the vendor email.")
    if _api_key():
        st.success(f"Email drafting: LLM ({MODEL}) with safety checks")
    else:
        st.info("Email drafting: template mode (no API key set)")
    st.divider()
    count_ph = st.empty()
    if st.button("Load demo history (all 9 scenarios)", width="stretch"):
        with st.spinner("Running scenarios..."):
            seed_history()
        st.rerun()
    with st.expander("Danger zone"):
        if st.button("Delete all runs"):
            db.clear()
            st.session_state.last_run_id = None
            st.rerun()

tab_run, tab_dash, tab_design = st.tabs(["▶️ Run a submission", "📊 Dashboard", "📐 Rules & design"])

# ------------------------------------------------------------------ RUN TAB
with tab_run:
    left, right = st.columns([2, 3], gap="large")
    with left:
        st.markdown("### New vendor submission")
        labels = {"blank": "- blank form -"} | {s["key"]: s["label"] for s in SCENARIOS}
        st.selectbox("Load a test submission", list(labels), format_func=labels.get, key="scenario_pick")
        st.button("Load into form", on_click=load_scenario, width="stretch")
        pick = st.session_state.scenario_pick
        if pick != "blank":
            st.caption(SCENARIOS_BY_KEY[pick]["description"])

        with st.form("vendor_form"):
            st.markdown("**Company**")
            st.text_input("Legal business name", key="f_legal_name")
            c1, c2 = st.columns(2)
            c1.selectbox("Country", COUNTRIES, format_func=lambda c: f"{c} - {COUNTRY_NAMES[c]}", key="f_country")
            c2.text_input("Tax ID (GSTIN/EIN/VAT/UEN)", key="f_tax_id")
            st.text_input("Registered address", key="f_address")
            c1, c2 = st.columns(2)
            c1.text_input("Contact person", key="f_contact_name")
            c2.text_input("Contact email", key="f_contact_email")
            st.markdown("**Bank**")
            c1, c2 = st.columns(2)
            c1.selectbox("Bank country", COUNTRIES, format_func=lambda c: f"{c} - {COUNTRY_NAMES[c]}", key="f_bank_country")
            c2.text_input("Bank name", key="f_bank_name")
            st.text_input("Account holder name", key="f_account_holder")
            c1, c2 = st.columns(2)
            c1.text_input("Account number / IBAN", key="f_account_number")
            c2.text_input("Bank code (IFSC/ABA/sort/BIC)", key="f_bank_code")
            st.multiselect("Documents attached", ALL_DOCS, format_func=DOC_LABELS.get, key="f_documents")
            submitted = st.form_submit_button("Run onboarding", type="primary", width="stretch")

        if submitted:
            sub = {f: st.session_state[f"f_{f}"] for f in FIELDS}
            scen = st.session_state.loaded_scenario
            # a resubmission needs a prior attempt on record: create it if the history is empty
            if scen and SCENARIOS_BY_KEY[scen].get("previous_scenario"):
                prev_sub = SCENARIOS_BY_KEY[SCENARIOS_BY_KEY[scen]["previous_scenario"]]["submission"]
                if not db.latest_run_for(prev_sub["legal_name"], prev_sub["country"]):
                    process(prev_sub, SCENARIOS_BY_KEY[scen]["previous_scenario"])
            st.session_state.last_run_id = process(sub, scen)
            st.session_state.animate = True

    with right:
        run = db.get_run(st.session_state.last_run_id) if st.session_state.last_run_id else None
        if run:
            animate = st.session_state.animate
            st.session_state.animate = False
            render_run(run, animate)
        else:
            st.markdown("### Live run view")
            st.info("Pick a test submission on the left (or fill the form), then click **Run onboarding**. "
                    "Each stage appears here as it executes, followed by the decision and the drafted vendor email.")

# ------------------------------------------------------------------ DASHBOARD TAB
with tab_dash:
    runs = db.list_runs()
    if not runs:
        st.info("No runs yet. Submit one on the first tab, or click **Load demo history** in the sidebar.")
    else:
        df = pd.DataFrame(runs)
        total = len(df)
        n = df["status"].value_counts()
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total runs", total)
        k2.metric("🟢 Approved", f"{int(n.get('APPROVED', 0))} ({n.get('APPROVED', 0) / total:.0%})")
        k3.metric("🟠 Pending", f"{int(n.get('PENDING', 0))} ({n.get('PENDING', 0) / total:.0%})")
        k4.metric("🔴 Rejected", f"{int(n.get('REJECTED', 0))} ({n.get('REJECTED', 0) / total:.0%})")
        k5.metric("Avg time / run", f"{df['duration_ms'].mean():.0f} ms")

        ca, cb = st.columns(2)
        with ca:
            st.markdown("**Runs by decision**")
            st.bar_chart(n.reindex(["APPROVED", "PENDING", "REJECTED"]).fillna(0), horizontal=True)
        with cb:
            st.markdown("**Most common reasons for non-approval**")
            cnt = Counter()
            for r in runs:
                full = db.get_run(r["id"])
                for reason in full["result"]["decision"]["reasons"]:
                    cnt[reason["rule"]] += 1
            if cnt:
                st.bar_chart(pd.Series(cnt).sort_values(), horizontal=True)
            else:
                st.caption("No issues recorded yet.")

        st.markdown("### Past runs")
        f1, f2 = st.columns([2, 3])
        status_f = f1.multiselect("Decision", ["APPROVED", "PENDING", "REJECTED"], default=["APPROVED", "PENDING", "REJECTED"])
        q = f2.text_input("Search vendor name")
        view = df[df["status"].isin(status_f)]
        if q:
            view = view[view["legal_name"].str.contains(q, case=False, na=False)]
        table = view[["id", "created_at", "legal_name", "country", "status", "manual_review", "n_passed", "n_checks", "headline"]].copy()
        table["manual_review"] = table["manual_review"].map({1: "yes", 0: "no"})
        table["checks"] = table["n_passed"].astype(str) + "/" + table["n_checks"].astype(str)
        table = table.drop(columns=["n_passed", "n_checks"])
        event = st.dataframe(table, width="stretch", hide_index=True, on_select="rerun",
                             selection_mode="single-row", key="runs_table")
        sel = event.selection.rows if event and event.selection else []
        if sel:
            run = db.get_run(int(table.iloc[sel[0]]["id"]))
            st.divider()
            render_run(run, animate=False)
        else:
            st.caption("Click a row to see every stage, the reasoning and the drafted email for that run.")

# ------------------------------------------------------------------ DESIGN TAB
with tab_design:
    st.markdown(
        """
### How it works
**Rules decide. The LLM only writes.** Approve/Pending/Reject comes from deterministic, auditable rules - an LLM
making a payment-risk call would be unexplainable and could be talked into a different answer. The model's only job is turning
structured findings into a polite vendor email, behind guardrails (no internal reasons, no account numbers, template fallback).

| # | Stage | What it checks |
|---|---|---|
| 1 | Intake & completeness | Required fields, 3-document checklist, email format |
| 2 | Tax ID validation | GSTIN (structure + checksum), US EIN (prefix), UK VAT, German VAT, Singapore UEN |
| 3 | Bank detail validation | IFSC, ABA routing checksum, UK sort code, IBAN mod-97, SWIFT/BIC country |
| 4 | Payee name match | Legal name vs. account holder after stripping case, punctuation and legal suffixes, then fuzzy similarity |
| 5 | Cross-field consistency | Tax-ID country vs. declared country, bank country vs. vendor country, free-mail contact |
| 6 | Registry & watchlist | Internal watchlist, duplicates, **bank-detail change on an existing vendor**, look-alike email domains |
| 7 | Decision | Approve / Pending / Reject, manual-review flag, next step, vendor email |

**Outcome logic.** Any `HARD STOP` -> Rejected. Otherwise any `vendor to fix` or `needs human review` -> Pending
(review items also set the manual-review flag). Otherwise Approved.

### Judgment calls worth knowing about
- *Name mismatch is Pending + manual review, not Reject.* Sole proprietors and trade names are legitimate; a human decides.
- *Bank-change emails go to the contact on file,* never the submitter - if the request is a business-email-compromise attempt,
  replying to the submitter would hand the attacker the confirmation channel.
- *Rejection emails never say why.* Telling a fraudster which control caught them teaches them how to evade it.
- *Duplicates are rejected,* since a second vendor record is how duplicate payments happen.
- *Resubmissions are diffed* against the vendor's last run: resolved vs. still open vs. new.

### Limits (v1, by design)
Tax IDs are checked for **format and checksum, not for existence** - production would call GSTN / VIES / IRS TIN-matching APIs.
Bank ownership is checked by name only; production would use a penny-drop or Confirmation-of-Payee check.
Document contents are not read (the checklist is a yes/no here). Watchlist and vendor master are small synthetic datasets.
Data in this demo is fictional. SQLite storage is ephemeral on free hosting.
"""
    )

count_ph.caption(f"Runs stored: **{db.count()}**")
