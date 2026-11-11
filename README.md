# ⚡ Zamp AP — Autonomous Vendor Onboarding Intelligence (PS-2)

A production-grade verification pipeline that takes vendor submissions, passes them through **7 deterministic verification gates**, produces **Approved / Pending / Rejected** decisions with full auditability, calculates a **0–100 composite risk score**, and auto-drafts polite, guardrailed vendor communications.

🎨 **UI Theme:** High-contrast Dark Mode with Cyber Orange accents (`#ff7700` / `#0d1117`).

---

## 🚀 Key Improvements & Intelligence Features

1. **Offline Semantic Bank Directory (Zero 3rd-Party API Dependency):**
   - Built-in resolution of 40+ bank code prefixes:
     - **India (IFSC):** `SBIN` → State Bank of India, `HDFC` → HDFC Bank, `ICIC` → ICICI Bank, `UTIB` → Axis Bank, `PUNB`, `BARB`, `CNRB`, etc.
     - **US (ABA Routing):** `0210` → JPMorgan Chase, `0260` → Bank of America, `0710` → Wells Fargo, etc.
     - **Singapore / Germany / UK (SWIFT/BIC):** `DBSSSGSG`, `INGDDEFF`, `BARCGB22`, etc.
   - Automatically cross-checks whether the vendor's declared bank name matches their bank code prefix!

2. **Geographical & Entity Cross-Verification:**
   - **GSTIN State & PAN Verification:** Extracts the 2-digit state code (e.g. `36` → Telangana, `27` → Maharashtra) and isolates the PAN.
   - **Address Postal Code Validation:** Verifies country-specific postal patterns (6-digit PIN for India, 5-digit ZIP for US, UK Postcode, German PLZ, etc.).
   - **Look-Alike Domain & Email Entity Consistency:** Checks if the submitter's domain aligns with company keywords or flags suspicious domain changes.

3. **Composite Risk Score (0–100) & Visual Gauge:**
   - Real-time gauge: **Low** (0–20), **Medium** (21–45), **High** (46–70), **Critical** (71–100).
   - Weighted by severity: Watchlist hits (+50), Bank changes (+25), Domain look-alikes (+20), Mule account flags (+20).

4. **Auto-Populated Dashboard (Zero Empty State):**
   - Automatically seeds historical runs on app launch so any interviewer opening the link immediately sees populated analytics, decision distributions, and audit trails.

5. **Guardrailed LLM Email Dispatch:**
   - Powered by **Gemini 2.0 Flash** (with fallback template).
   - Strict output sanitization: strips internal fraud keywords (`fraud`, `mule`, `watchlist`) and never discloses account numbers to the vendor.

---

## 📐 Verification Stages

| Gate | Stage | Verification Logic |
|---|---|---|
| **1** | Intake & Completeness | Mandatory fields check, 3 compliance documents, RFC 5322 email syntax |
| **2** | Tax ID Format & Checksums | GSTIN (mod-36 checksum + state lookup), US EIN prefix validity, UK/DE VAT, SG UEN |
| **3** | Bank Settlement Check | IFSC/ABA/IBAN checksums + **Offline Bank Registry Lookup & Bank Name match** |
| **4** | Payee Entity Match | Strip legal suffixes (`Pvt Ltd`, `LLC`, `GmbH`) + fuzzy ratio comparison |
| **5** | Cross-Field Consistency | Tax country vs declared country, offshore bank warnings, postal code match |
| **6** | Registry & Watchlist | Sanction/fraud watchlist, duplicate vendor detection, **BEC bank change alert** |
| **7** | Decision & Risk Score | Approved / Pending / Rejected + Composite Risk Score (0–100) |

---

## 🏃 Local Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
*(Streamlit Cloud automatically reads secrets and theme configurations from `.streamlit/`)*
