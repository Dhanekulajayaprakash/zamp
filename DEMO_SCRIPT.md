# 5-Minute Demo Script (Target: 4:30 | Hard Limit: 5:00)

Record in your **own voice** (AI narration is not allowed). Loom or OBS at 1080p, no editing needed.

## Pre-Recording Prep (Do Off-Camera)
1. Open `https://jayaprakashzamp.streamlit.app/` in a clean browser tab.
2. Check the sidebar: confirm it says **LLM Active — gemini-3.5-flash-lite**.
3. Click **Reload Demo** in the sidebar if any older runs are present, so every run in the dashboard uses the latest engine and `gemini-3.5-flash-lite`.
4. Reload the browser page once so **Intake & Verification** starts fresh on **Pipeline Ready**.
5. Do NOT read word-for-word — hit the talking points naturally in your own words.

---

## 0:00 – 0:35 | Problem Statement & Core Architecture
- **Say:** "I chose Problem Statement 2 — Autonomous Vendor Onboarding Intelligence for Accounts Payable. When a new supplier submits registration, tax, bank, and compliance documents, we need an instant, auditable decision: **Approve**, **Pending**, or **Reject**, plus safe vendor communication."
- **Highlight design choice:** "My core rule is **Rules Decide, the LLM Only Communicates**. Money movement has to be deterministic and explainable. Six verification stages run pure Python math and heuristics, calculate a 0–100 Risk Score, and **Gemini 3.5 Flash-Lite** only drafts the vendor email behind strict safety guardrails."
- **Show UI briefly:** Point at the three clean tabs (**Intake & Verification**, **Executive Dashboard**, **System Architecture**) and the **ERP Vendors on File** panel in the sidebar.

---

## 0:35 – 1:55 | Happy Path (Apex Cloud Solutions, India)
- **Click:** Select **`[Happy path] Happy path - clean Indian vendor`** → click **Load Payload into Form** → scroll briefly to show fields + 3 compliance attachments → click **Run Autonomous Verification**.
- **Narrate while stages animate:**
  1. **Intake & Completeness:** Checks mandatory fields, 3 compliance docs, email format.
  2. **Tax ID Validation:** Not naive regex — runs the **Mod-36 GSTIN checksum**, validates state code `36 → Telangana`, and extracts the embedded PAN.
  3. **Bank Detail Validation:** Checks the Indian IFSC format AND looks up `HDFC` in an **offline 40-institution bank directory**, cross-checking that the vendor's declared bank name ("HDFC Bank") matches the code.
  4. **Payee Name Match:** Strips suffixes (`Pvt Ltd` vs `Pvt. Ltd.`) so normal punctuation differences pass cleanly.
  5. **Cross-Field Consistency:** Checks tax country, bank country, Indian 6-digit PIN code (`500081`), and verifies `apexcloud.in` aligns with the company name.
  6. **Registry & Watchlist:** No internal watchlist hit, no duplicate vendor.
- **Land on Decision:**
  - Point to **APPROVED**, **15/15 Checks Passed**, **Risk Score: LOW (0/100)**.
  - Scroll to **Automated Vendor Dispatch**: point out `engine: LLM (gemini-3.5-flash-lite)` and the polite welcome email.

---

## 1:55 – 3:45 | High-Judgment Edge Cases (Pick 3 Quick Demos)

### 1. Business Email Compromise Defense (`Edge 3` — Orion Industrial Supplies, Germany) — ~50 sec
- **Click:** Load **`[Edge 3] Edge 3 - Existing vendor 'changes' bank details`** → **Run Autonomous Verification**.
- **Explain judgment:** "Same VAT ID (`DE811234567`) and legal name as active vendor `V-1042`, **but** a new German IBAN and a look-alike email domain `orion-industrial.co` instead of `.de`. That's classic BEC fraud."
- **Point out Risk & Routing:**
  - Lands on **PENDING** with **Manual Review Required** and **CRITICAL (85/100)** risk score (not auto-rejected, in case it's a legitimate bank switch).
  - Point at the **Recipient warning** in the email box: **"Sent to `procurement@orion-industrial.de` — the contact ON FILE, not the submitter."** Explain: "If an attacker hijacked or spoofed the email, replying to the submitter would hand confirmation straight to them."

### 2. Legal Suffix Normalization vs. Third-Party Mule (`Edge 1a` or `Edge 1b`) — ~35 sec
- **Click:** Load **`[Edge 1b] Edge 1b - Bank account belongs to a different company`** → **Run Autonomous Verification** (mention `Edge 1a` quickly in one sentence).
- **Say:** "A naive string compare fails on `Private Limited` vs `PVT LTD` (`Edge 1a` passes cleanly after stripping 24 international corporate suffixes). Meanwhile here in `Edge 1b`, `Brightpath Consulting LLC` submits a bank account held by `Sunrise Trading Co` — flagged immediately as a third-party/mule-account pattern for human review, even though the US ABA routing `0210` passes Mod-10 checksum and resolves to JPMorgan Chase."

### 3. Differential Resubmission OR Watchlist Zero-Leak (`Edge 4b` or `Bonus`) — ~25 sec
- *Option A (Recommended — shows memory & delta tracking):* Load **`[Edge 4b] Edge 4b - Partial resubmission`** → **Run Autonomous Verification**.
  - Point at **Delta Analysis — Previous Submission**: "Compared against Nimbus Data Labs' first attempt in SQLite — it automatically isolates **Resolved** (Contact Email, Bank Proof), **Still Open** (invalid US EIN prefix `07`), and **New Anomalies**."
- *Option B (if faster, open from Dashboard instead):* Mention **Watchlist Hit** (`Quickpay Global Traders`) gets **REJECTED (100/100 Critical)**, while the outbound email stays completely neutral with **zero fraud keywords leaked**.

---

## 3:45 – 4:30 | Executive Dashboard, Guardrails & Honest Production Scope
- **Switch to `Executive Dashboard` tab:**
  - Show top KPIs (auto-seeded on first visit — Total Ingestions, Approved/Pending/Rejected split, Avg Latency), Decision Breakdown & Top Failure Reasons charts.
  - Click any row (e.g., `Quickpay Global Traders` or `Orion`) to show the **Deep Inspection** audit replay + guardrailed email.
- **Close with engineering honesty (20 sec):**
  - "Every check today is self-contained and deterministic — mathematical checksums, an offline 40-bank directory, and SQLite audit persistence, with graceful template fallback if the LLM is ever unavailable."
  - "In production, the next three layers plug right in: live government APIs (GSTN, IRS TIN-Match, EU VIES), real-time penny-drop / Confirmation-of-Payee ownership checks, and document OCR to verify uploaded PDFs match form inputs."

---

## Recording Checklist
- [ ] Live URL (`https://jayaprakashzamp.streamlit.app/`) open, sidebar shows `LLM Active — gemini-3.5-flash-lite`
- [ ] Clicked **Reload Demo** off-camera so all seeded dashboard runs show `LLM (gemini-3.5-flash-lite)`
- [ ] Under **5:00** total (target **4:30**)
- [ ] Own voice only, 1080p, "Anyone with the link can view" enabled before submitting
