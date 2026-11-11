"""Vendor Onboarding Intelligence Engine - Streamlit UI.
Theme: High-contrast Dark & Cyber Orange
Features:
  - Multi-stage deterministic risk pipeline
  - Offline bank registry resolution (IFSC, ABA, SWIFT)
  - Postal code & state cross-verification
  - Real-time animated pipeline stages
  - Risk scoring (0-100) & risk radar gauge
  - Auto-seeded historical dashboard (ready on first visit)
  - LLM-assisted polite vendor email generator with guardrails
"""
from __future__ import annotations

import time
from collections import Counter

import pandas as pd
import streamlit as st

import db
from data import ALL_DOCS, DOC_LABELS, SCENARIOS, SCENARIOS_BY_KEY, REGISTRY
from engine import iter_stages, decide, clean, run_pipeline
from messages import MODEL, _api_key, draft_email
from validators import COUNTRY_NAMES

st.set_page_config(
    page_title="Zamp AP | Vendor Onboarding Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- Orange & Black Custom Styling -----------------
st.markdown(
    """<style>
    /* Dark & Orange Theme Overrides */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    .block-container {
        padding-top: 1.8rem;
        max-width: 1250px;
    }

    /* Gradient Header Accent */
    .brand-header {
        background: linear-gradient(135deg, #ff5500 0%, #ff8c00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 0.2rem;
    }
    
    .brand-sub {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    /* Custom Cards */
    .dark-card {
        background: #141820;
        border: 1px solid #232936;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }

    .dark-card:hover {
        border-color: #ff6a00;
        transition: border-color 0.2s ease-in-out;
    }

    /* Orange Glowing Pills */
    .pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }
    .pill.APPROVED {
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(74, 222, 128, 0.4);
    }
    .pill.PENDING {
        background: rgba(255, 136, 0, 0.18);
        color: #ff9d3b;
        border: 1px solid rgba(255, 157, 59, 0.45);
    }
    .pill.REJECTED {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(248, 113, 113, 0.4);
    }

    /* Risk Score Gauge */
    .risk-container {
        background: #11141c;
        border: 1px solid #1f2533;
        border-radius: 10px;
        padding: 14px;
        margin: 12px 0;
    }
    .risk-bar-bg {
        width: 100%;
        height: 12px;
        background: #232938;
        border-radius: 6px;
        overflow: hidden;
        margin-top: 8px;
    }
    .risk-bar-fill {
        height: 100%;
        border-radius: 6px;
        transition: width 0.6s ease;
    }
    .risk-Low {
        background: linear-gradient(90deg, #10b981, #34d399);
    }
    .risk-Medium {
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
    }
    .risk-High {
        background: linear-gradient(90deg, #f97316, #ea580c);
    }
    .risk-Critical {
        background: linear-gradient(90deg, #ef4444, #dc2626);
    }

    /* Metric cards orange accent */
    div[data-testid="stMetricValue"] {
        color: #ff8533 !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #cbd5e1 !important;
        font-weight: 600;
    }

    /* Sidebar header styling */
    .sidebar-badge {
        background: linear-gradient(135deg, #261608 0%, #151821 100%);
        border: 1px solid #ff6600;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 14px;
    }

    /* Form submit button bright orange */
    div.stButton > button:first-child[kind="primary"] {
        background: linear-gradient(135deg, #ff5500 0%, #ff8800 100%) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 15px rgba(255, 85, 0, 0.4) !important;
    }
    div.stButton > button:first-child[kind="primary"]:hover {
        background: linear-gradient(135deg, #ff6600 0%, #ffa020 100%) !important;
        box-shadow: 0 6px 20px rgba(255, 102, 0, 0.6) !important;
    }
    </style>""",
    unsafe_allow_html=True,
)

ICON = {"pass": "✅", "warn": "⚠️", "fail": "❌"}
STATUS_ICON = {"APPROVED": "🟢", "PENDING": "🟠", "REJECTED": "🔴"}
EFFECT_TAG = {"fix": "vendor to fix", "review": "needs human review", "block": "HARD STOP", "none": ""}
FIELDS = ["legal_name", "country", "tax_id", "address", "contact_name", "contact_email",
          "bank_country", "bank_name", "account_holder", "account_number", "bank_code", "documents"]
BLANK = {"legal_name": "", "country": "IN", "tax_id": "", "address": "", "contact_name": "", "contact_email": "",
         "bank_country": "IN", "bank_name": "", "account_holder": "", "account_number": "", "bank_code": "",
         "documents": list(ALL_DOCS)}
COUNTRIES = list(COUNTRY_NAMES)


# ------------------------------------------------------------------ auto-seed
def ensure_seeded_data():
    """Auto-load historical demo scenarios so the dashboard is immediately populated on link click."""
    if db.count() == 0:
        for s in SCENARIOS:
            sub = clean(s["submission"])
            res = run_pipeline(sub)
            email = draft_email(sub, res["decision"])
            db.save_run(sub, res["stages"], res["decision"], email, s["key"], 28.5)


ensure_seeded_data()


# ------------------------------------------------------------------ core processing
def process(sub: dict, scenario: str | None = None) -> int:
    """Run pipeline end-to-end and persist to SQLite."""
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


for f in FIELDS:
    st.session_state.setdefault(f"f_{f}", BLANK[f])
st.session_state.setdefault("loaded_scenario", None)
st.session_state.setdefault("last_run_id", None)
st.session_state.setdefault("animate", False)


# ------------------------------------------------------------------ UI Renderers
def render_risk_gauge(score: int, label: str):
    """Render modern glowing cyber-risk progress bar."""
    colors = {
        "Low": "#10b981",
        "Medium": "#f59e0b",
        "High": "#f97316",
        "Critical": "#ef4444"
    }
    fill_color = colors.get(label, "#ff7700")
    st.markdown(
        f"""
        <div class="risk-container">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:0.85rem; font-weight:600; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px;">
                    🛡️ Composite Risk Analysis
                </span>
                <span style="color:{fill_color}; font-weight:800; font-size:1.05rem;">
                    {label.upper()} ({score}/100)
                </span>
            </div>
            <div class="risk-bar-bg">
                <div class="risk-bar-fill risk-{label}" style="width: {max(score, 4)}%;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:6px; font-size:0.75rem; color:#64748b;">
                <span>0 (Clean)</span>
                <span>25 (Guarded)</span>
                <span>50 (Elevated)</span>
                <span>75 (High)</span>
                <span>100 (Hard Reject)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stage(stage: dict, container):
    with container.container(border=True):
        st.markdown(
            f"**{ICON[stage['status']]} {stage['title']}** &nbsp; "
            f"<span style='color:#ff8800; font-family:monospace; font-size:0.78rem; background:#221508; padding:2px 6px; border-radius:4px;'>{stage['ms']} ms</span>",
            unsafe_allow_html=True
        )
        for c in stage["checks"]:
            tag = EFFECT_TAG[c["effect"]]
            tag_badge = f" &nbsp;<span style='background:#2a1b14; color:#ff944d; padding:2px 8px; border-radius:4px; font-size:0.75rem;'>{tag}</span>" if tag else ""
            st.markdown(
                f"{ICON[c['status']]} **{c['rule']}**{tag_badge}  \n"
                f"<span style='color:#94a3b8; font-size:0.88rem;'>{c['detail']}</span>",
                unsafe_allow_html=True
            )


def render_decision(d: dict):
    status = d["status"]
    pill_html = f"<span class='pill {status}'>{STATUS_ICON[status]} {status}</span>"
    
    st.markdown(
        f"""
        <div class="dark-card" style="border-left: 4px solid {'#10b981' if status=='APPROVED' else '#ff8800' if status=='PENDING' else '#ef4444'};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 style="margin:0; font-weight:800; color:#f8fafc;">Verification Result</h3>
                {pill_html}
            </div>
            <p style="margin: 8px 0 0 0; color:#cbd5e1; font-size:1rem;">{d['headline']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Checks Passed", f"{d['n_passed']}/{d['n_checks']}")
    c2.metric("Manual Review", "Required" if d["manual_review"] else "Not Needed")
    c3.metric("Existing Match", d["matched_vendor"] or "None (New)")
    c4.metric("Risk Level", f"{d.get('risk_label', 'Low')}")

    render_risk_gauge(d.get("risk_score", 0), d.get("risk_label", "Low"))

    st.markdown(f"**Action Item / Next Step:** `{d['next_step']}`")
    
    if "resolved" in d:
        st.markdown("#### 🔄 Delta Analysis vs Previous Submission")
        a, b, c = st.columns(3)
        a.markdown("✅ **Resolved**\n\n" + ("\n".join(f"- {x}" for x in d["resolved"]) or "- none"))
        b.markdown("⏳ **Still Open**\n\n" + ("\n".join(f"- {x}" for x in d["still_open"]) or "- none"))
        c.markdown("🆕 **New Anomalies**\n\n" + ("\n".join(f"- {x}" for x in d["new_issues"]) or "- none"))
        
    if d["reasons"]:
        st.markdown("#### 🔍 Rule Trigger Breakdown")
        for r in d["reasons"]:
            st.markdown(f"- `{EFFECT_TAG[r['effect']]}` **{r['rule']}** — {r['detail']}")


def render_email(e: dict | None):
    if not e:
        return
    with st.container(border=True):
        st.markdown(
            f"**✉️ Automated Vendor Dispatch** &nbsp; "
            f"<span style='background:#1b2333; color:#60a5fa; padding:2px 8px; border-radius:4px; font-size:0.75rem;'>engine: {e['drafted_by']}</span>",
            unsafe_allow_html=True
        )
        st.markdown(f"**Recipient:** `{e['to']}`" + (f"  \n<span style='color:#f59e0b;'>⚠️ {e['to_note']}</span>" if e.get("to_note") else ""),
                    unsafe_allow_html=True)
        st.markdown(f"**Subject:** `{e['subject']}`")
        st.text_area("Email Content (Guardrailed)", value=e["body"], height=160, disabled=True)


def render_run(run: dict, animate: bool):
    sub, res = run["submission"], run["result"]
    st.markdown(f"### {run['legal_name']} &nbsp;·&nbsp; `{COUNTRY_NAMES.get(run['country'], run['country'])}`")
    st.caption(f"Run ID #{run['id']} · Timestamp: {run['created_at']} UTC · Latency: {run['duration_ms']:.1f}ms")
    
    for stg in res["stages"]:
        slot = st.empty()
        if animate:
            slot.info(f"⚡ Processing {stg['title']} ...")
            time.sleep(0.4)
        render_stage(stg, slot)
    if animate:
        time.sleep(0.2)
    render_decision(res["decision"])
    render_email(run["email"])
    with st.expander("📄 View Normalized Payload (JSON)"):
        st.json(sub)


# ------------------------------------------------------------------ Sidebar
with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
            <span style="font-size:2rem;">⚡</span>
            <div>
                <h2 style="margin:0; font-size:1.3rem; font-weight:800; color:#ff7700;">ZAMP AP</h2>
                <span style="font-size:0.78rem; color:#94a3b8; font-weight:600;">Autonomous Vendor Verification</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Architecture Info Box
    st.markdown("""
        <div class="sidebar-badge">
            <div style="font-weight:700; color:#ff8800; font-size:0.85rem; margin-bottom:4px;">🏗️ ARCHITECTURE PRINCIPLE</div>
            <div style="font-size:0.78rem; color:#cbd5e1; line-height:1.4;">
                • <strong>Deterministic Rules Engine:</strong> Validates format, checksums, bank code prefixes & entity identity.<br>
                • <strong>Semantic Cross-Matching:</strong> Entity name suffix fuzzy match, postal format & look-alike domain checks.<br>
                • <strong>Guardrailed LLM:</strong> Generates polite vendor email without leaking internal fraud flags.
            </div>
        </div>
    """, unsafe_allow_html=True)

    if _api_key():
        st.success(f"🤖 LLM Drafting: Active ({MODEL})")
    else:
        st.info("⚡ LLM Mode: Template Fallback (key-optional)")

    st.divider()

    # Reset / reload demo history
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("🔄 Reload Demo", use_container_width=True):
            db.clear()
            ensure_seeded_data()
            st.session_state.last_run_id = None
            st.rerun()
    with c_btn2:
        if st.button("🗑️ Clear DB", use_container_width=True):
            db.clear()
            st.session_state.last_run_id = None
            st.rerun()

    st.markdown(f"**Database Runs Stored:** `{db.count()}`")

    # Master vendor database on file
    st.divider()
    st.markdown("<span style='font-size:0.85rem; font-weight:700; color:#94a3b8;'>📋 EXISTING ERP VENDORS ON FILE</span>", unsafe_allow_html=True)
    for v in REGISTRY:
        st.markdown(
            f"""<div style="background:#11151e; border:1px solid #1e2636; border-radius:6px; padding:6px 10px; margin:4px 0; font-size:0.78rem;">
                <strong style="color:#ff8800;">{v['id']}</strong> &nbsp;{v['name']}<br>
                <span style="color:#64748b;">{v['country']} · {v['tax_id']} · Contact: {v['contact_email']}</span>
            </div>""",
            unsafe_allow_html=True
        )


# ------------------------------------------------------------------ Tabs
st.markdown('<div class="brand-header">Vendor Onboarding Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-sub">Real-time cross-validation pipeline with checksum validation, bank registry resolution & risk decisioning.</div>', unsafe_allow_html=True)

tab_run, tab_dash, tab_design = st.tabs(["⚡ Intake & Verification Run", "📊 Executive Audit Dashboard", "📐 System Logic & Specs"])


# ------------------------------------------------------------------ Tab 1: Run
with tab_run:
    left, right = st.columns([2, 3], gap="large")
    with left:
        st.markdown("#### 1. Select or Input Vendor Payload")
        labels = {"blank": "— [Blank Custom Form] —"} | {s["key"]: f"[{s['kind']}] {s['label']}" for s in SCENARIOS}
        st.selectbox("Select Pre-configured Scenario", list(labels), format_func=labels.get, key="scenario_pick")
        
        c_load1, c_load2 = st.columns([2, 1])
        with c_load1:
            st.button("📥 Load Selected Payload into Form", on_click=load_scenario, use_container_width=True)
        with c_load2:
            st.caption("Auto-fills form fields")

        pick = st.session_state.scenario_pick
        if pick != "blank":
            st.info(f"💡 **Scenario Context:** {SCENARIOS_BY_KEY[pick]['description']}")

        with st.form("vendor_form"):
            st.markdown("<span style='color:#ff8800; font-weight:700; font-size:0.9rem;'>🏢 COMPANY REGISTRATION</span>", unsafe_allow_html=True)
            st.text_input("Legal Business Name", key="f_legal_name")
            c1, c2 = st.columns(2)
            c1.selectbox("Country of Incorporation", COUNTRIES, format_func=lambda c: f"{c} - {COUNTRY_NAMES[c]}", key="f_country")
            c2.text_input("Tax ID (GSTIN / EIN / VAT / UEN)", key="f_tax_id")
            st.text_input("Registered Business Address (must contain postal code)", key="f_address")
            
            c1, c2 = st.columns(2)
            c1.text_input("Authorized Contact Person", key="f_contact_name")
            c2.text_input("Contact Email Address", key="f_contact_email")

            st.markdown("<span style='color:#ff8800; font-weight:700; font-size:0.9rem;'>🏦 BANK ACCOUNT & SETTLEMENT</span>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c1.selectbox("Bank Jurisdiction", COUNTRIES, format_func=lambda c: f"{c} - {COUNTRY_NAMES[c]}", key="f_bank_country")
            c2.text_input("Bank Name", key="f_bank_name")
            st.text_input("Account Holder Name (Payee)", key="f_account_holder")
            
            c1, c2 = st.columns(2)
            c1.text_input("Account Number / IBAN", key="f_account_number")
            c2.text_input("Bank Code (IFSC / ABA / Sort / BIC)", key="f_bank_code")

            st.markdown("<span style='color:#ff8800; font-weight:700; font-size:0.9rem;'>📎 COMPLIANCE ATTACHMENTS</span>", unsafe_allow_html=True)
            st.multiselect("Uploaded Documents", ALL_DOCS, format_func=DOC_LABELS.get, key="f_documents")

            submitted = st.form_submit_button("⚡ Run Autonomous Verification", type="primary", use_container_width=True)

        if submitted:
            sub = {f: st.session_state[f"f_{f}"] for f in FIELDS}
            scen = st.session_state.loaded_scenario
            
            # Ensure prior attempt exists for resubmission diffing
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
            st.markdown("#### 2. Live Verification Pipeline Stream")
            st.markdown("""
                <div style="border: 2px dashed #232a3b; border-radius:12px; padding:40px; text-align:center; background:#10131a;">
                    <span style="font-size:2.5rem;">⚡</span>
                    <h4 style="color:#f8fafc; margin:10px 0 6px 0;">Pipeline Ready</h4>
                    <p style="color:#64748b; font-size:0.9rem; max-width:400px; margin:0 auto;">
                        Select a test scenario on the left and click <strong>Run Autonomous Verification</strong> to observe each verification gate execute live.
                    </p>
                </div>
            """, unsafe_allow_html=True)


# ------------------------------------------------------------------ Tab 2: Dashboard
with tab_dash:
    runs = db.list_runs()
    if not runs:
        st.info("No runs logged yet. Click **Reload Demo** in the sidebar to populate.")
    else:
        df = pd.DataFrame(runs)
        total = len(df)
        n = df["status"].value_counts()

        # Top Executive Metrics
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total Ingestions", total)
        k2.metric("🟢 Approved", f"{int(n.get('APPROVED', 0))} ({(n.get('APPROVED', 0)/total)*100:.0f}%)")
        k3.metric("🟠 Pending / Manual", f"{int(n.get('PENDING', 0))} ({(n.get('PENDING', 0)/total)*100:.0f}%)")
        k4.metric("🔴 Blocked / Reject", f"{int(n.get('REJECTED', 0))} ({(n.get('REJECTED', 0)/total)*100:.0f}%)")
        k5.metric("Avg Latency", f"{df['duration_ms'].mean():.1f} ms")

        st.markdown("<br>", unsafe_allow_html=True)
        ca, cb = st.columns(2)
        with ca:
            st.markdown("**Decision Breakdown**")
            chart_series = n.reindex(["APPROVED", "PENDING", "REJECTED"]).fillna(0)
            st.bar_chart(chart_series, color="#ff7700")

        with cb:
            st.markdown("**Top Failure & Review Reasons**")
            cnt = Counter()
            for r in runs:
                full = db.get_run(r["id"])
                for reason in full["result"]["decision"]["reasons"]:
                    cnt[reason["rule"]] += 1
            if cnt:
                st.bar_chart(pd.Series(cnt).sort_values(ascending=False).head(6), color="#ea580c")
            else:
                st.caption("No non-approved runs yet.")

        st.markdown("### Historical Audit Trail")
        f1, f2 = st.columns([1, 2])
        status_f = f1.multiselect("Filter Decision", ["APPROVED", "PENDING", "REJECTED"], default=["APPROVED", "PENDING", "REJECTED"])
        q = f2.text_input("🔍 Search Vendor Name")

        view = df[df["status"].isin(status_f)]
        if q:
            view = view[view["legal_name"].str.contains(q, case=False, na=False)]

        table = view[["id", "created_at", "legal_name", "country", "status", "manual_review", "n_passed", "n_checks", "headline"]].copy()
        table["manual_review"] = table["manual_review"].map({1: "Yes", 0: "No"})
        table["score"] = table["n_passed"].astype(str) + "/" + table["n_checks"].astype(str)
        table = table.drop(columns=["n_passed", "n_checks"])

        event = st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="runs_table"
        )

        sel = event.selection.rows if event and event.selection else []
        if sel:
            selected_id = int(table.iloc[sel[0]]["id"])
            st.divider()
            st.markdown(f"#### 🔍 Deep Inspection for Run #{selected_id}")
            render_run(db.get_run(selected_id), animate=False)
        else:
            st.caption("💡 Tip: Click any row above to inspect the step-by-step audit reasoning and generated vendor email.")


# ------------------------------------------------------------------ Tab 3: Design
with tab_design:
    st.markdown("""
### 🧠 System Architecture & Decision Boundary

```
                     ┌────────────────────────────────┐
                     │    New Vendor Submission       │
                     └───────────────┬────────────────┘
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
┌─────────────────────────────────┐             ┌─────────────────────────────────┐
│ Stage 1: Intake & Completeness  │             │ Stage 2: Tax ID Format Checks   │
│ • Required fields present       │             │ • GSTIN (state code + checksum) │
│ • 3 Compliance docs attached    │             │ • US EIN / UK VAT / DE VAT      │
│ • Valid email format            │             │ • Cross-country tax detection   │
└────────────────┬────────────────┘             └────────────────┬────────────────┘
                 │                                               │
         ┌───────┴───────────────────────────────────────────────┴───────┐
         ▼                                                               ▼
┌─────────────────────────────────┐             ┌─────────────────────────────────┐
│ Stage 3: Bank Detail Validation │             │ Stage 4: Payee Entity Resolution│
│ • IFSC / ABA / IBAN checksum    │             │ • Normalize Pvt/Ltd/LLC/Inc     │
│ • Offline Bank Registry Lookup  │             │ • SequenceMatcher fuzzy ratio   │
│ • Bank Name semantic cross-check│             │ • Flag mule accounts & mismatch │
└────────────────┬────────────────┘             └────────────────┬────────────────┘
                 │                                               │
         ┌───────┴───────────────────────────────────────────────┴───────┐
         ▼                                                               ▼
┌─────────────────────────────────┐             ┌─────────────────────────────────┐
│ Stage 5: Cross-Field Invariance │             │ Stage 6: Registry & Watchlist   │
│ • Tax country vs Vendor country │             │ • Internal fraud watchlist hit  │
│ • Bank country vs Vendor country│             │ • Duplicate active vendor check │
│ • Address postal code by country│             │ • Bank change velocity alarm    │
│ • Domain vs Company name match  │             │ • Look-alike email domain check │
└────────────────┬────────────────┘             └────────────────┬────────────────┘
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │       Stage 7: Risk Scoring & Decision        │
                 │   • Hard Stop (Block)  ──► REJECTED           │
                 │   • Review / Fix item ──► PENDING (Manual)   │
                 │   • All Checks Passed  ──► APPROVED           │
                 │   • Risk Score Gauge (0 - 100)                │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │       LLM Dispatch with Security Filters      │
                 │   • Polished, respectful follow-up email      │
                 │   • Strips internal fraud & risk keywords     │
                 │   • Bank changes sent to CONTACT ON FILE      │
                 └───────────────────────────────────────────────┘
```

---

### Key Judgment Calls
1. **Why Name Mismatches are PENDING, not REJECTED:**
   Sole proprietors, DBAs, and regional trading names often operate bank accounts with slight entity deviations. Hard-rejecting them loses valid business. Routing them to human review with an auto-drafted request for a bank authorization letter strikes the right balance between fraud prevention and commercial enablement.
2. **Bank Detail Changes & BEC Defense:**
   When an active vendor submits a new IBAN/bank account, email confirmation is deliberately routed to the **contact email already on file**, not the newly submitted address. If a vendor's supply chain rep has suffered an email account takeover, replying to the new email would confirm fraudulent payment routing.
3. **No Internal Reason Disclosure on Watchlist Hits:**
   When an entity matches a debarred or fraud-linked watchlist, the email uses a neutral decline template. Revealing exact fraud checks educates threat actors on how to evade detection on subsequent attempts.
4. **Offline Semantic Bank Directory:**
   Rather than failing when 3rd-party banking APIs are unavailable, the engine includes an offline directory of 40+ bank code prefixes (e.g., IFSC `SBIN` → State Bank of India, `HDFC` → HDFC Bank; ABA `0210` → JPMorgan Chase) to cross-verify the vendor's declared bank name without external dependencies.
""")
