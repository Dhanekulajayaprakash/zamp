# 5-Minute Demo Script — Zamp AP: Autonomous Vendor Onboarding Intelligence
# Jayaprakash Dhanekula | B.Tech, Computer Science & Engineering | IIT Hyderabad
# Target: 4:30 | Hard Limit: 5:00

---

## Before You Start Recording (Off-Camera Setup)
1. Open **https://jayaprakashzamp.streamlit.app/** in a fresh browser tab.
2. Check the sidebar confirms **LLM Active — gemini-3.5-flash-lite** is showing.
3. Click **Reload Demo** in the sidebar to ensure all 9 scenarios are freshly seeded.
4. Reload the page so the **Intake & Verification** tab opens clean on "Pipeline Ready".
5. Keep this script nearby — speak naturally in your own words, not word-for-word.

---

## 0:00 – 0:30 | Personal Introduction & Problem Statement

**Say something like:**

> "Hi, I'm Jayaprakash — I'm a B.Tech student in Computer Science and Engineering at IIT Hyderabad.
>
> For this case study, I chose Problem Statement 2: Autonomous Vendor Onboarding Intelligence for Accounts Payable.
>
> Here's the problem: when a new vendor — a supplier, a contractor — submits their company registration, tax details, bank account, and compliance documents to get paid, someone has to review all of that and decide: **Approve**, **Pending**, or **Reject**. And if there's something wrong, someone has to write them a professional email explaining what's missing.
>
> Doing that manually for dozens of submissions every quarter is slow, error-prone, and frankly, a fraud risk.
>
> My solution automates all of it — deterministically, in under 35 milliseconds, with a live Gemini-drafted vendor email at the end."

**Show the UI:** Point at the three tabs (**Intake & Verification**, **Executive Dashboard**, **System Architecture**) and the **ERP Vendors on File** registry panel in the sidebar.

**One line design philosophy:**

> "My core principle: **Rules make every financial decision. Gemini only writes the email.** Money movement has to be auditable. An AI prompt deciding whether to approve a vendor payment is a liability — my rules engine handles that; the LLM just communicates."

---

## 0:30 – 1:50 | Happy Path — Clean Indian Vendor (Apex Cloud Solutions)

**Select:** `[Happy path] Happy path - clean Indian vendor` → **Load Payload into Form**

*Briefly show the form is populated — company name, Telangana, GSTIN, HDFC Bank IFSC, 3 compliance documents attached.*

**Click:** **Run Autonomous Verification**

*While the stages animate, narrate each one:*

> **Stage 1 — Intake & Completeness:**
> "Checks all mandatory fields are filled, three compliance certificates are attached — tax certificate, incorporation cert, bank proof — and the contact email passes RFC format validation. All green."

> **Stage 2 — Tax ID Validation:**
> "This is where I went beyond simple regex. The engine runs the actual Mod-36 GSTIN checksum over all 14 characters, extracts the state code — here, `36` maps to Telangana — and pulls out the embedded PAN number. It's doing the same math the Indian GST system does. That means transposed digits that look fine to regex get caught here."

> **Stage 3 — Bank Detail Validation:**
> "The IFSC code `HDFC0001234` passes the format check — and then the engine looks up the first four characters `HDFC` in an offline registry of 40 real financial institutions I embedded in the app. It resolves to HDFC Bank, cross-checks against what the vendor wrote in the bank name field, and they match. No external API, no failure risk."

> **Stage 4 — Payee Name Match:**
> "The company name is `Apex Cloud Solutions Pvt Ltd` and the account holder is `Apex Cloud Solutions Pvt. Ltd.` — the only difference is a full stop. A naive string comparison would flag that. The engine strips 24 international corporate suffixes — Pvt, Ltd, Private, Limited, LLC, GmbH — normalizes punctuation, and computes fuzzy similarity. 98% match. Passes cleanly."

> **Stage 5 — Cross-Field Consistency:**
> "Verifies the Indian GSTIN is consistent with the Indian company declaration. Checks the bank is in the same country. Validates the address contains a proper 6-digit Indian PIN code — `500081` for HITEC City. And checks the contact domain `apexcloud.in` aligns with the company name."

> **Stage 6 — Registry & Watchlist:**
> "Scans an internal fraud watchlist — no account, tax ID, or entity name hit. No duplicate active vendor in the ERP. This is a brand new vendor."

**Land on Decision:**

> "15 out of 15 checks passed. APPROVED. Risk Score: 0 — Low. And the LLM-drafted welcome email at the bottom says `engine: LLM (gemini-3.5-flash-lite)` — Gemini wrote a polite onboarding welcome in context."

---

## 1:50 – 3:40 | High-Judgment Edge Cases (3 Scenarios)

---

### Scenario A: BEC Fraud Defense — Orion Industrial Supplies, Germany (~55 sec)

**Select:** `[Edge 3] Existing vendor 'changes' bank details` → **Load** → **Run**

> "This is my favourite scenario — and the most important one for AP fraud prevention.
>
> Same VAT ID as an active ERP vendor, same legal name. But a new IBAN and a contact email coming from `orion-industrial.co` instead of the registered `orion-industrial.de`. This is exactly how Business Email Compromise works — the attacker registers a look-alike domain, one character different, and submits a fake bank change.
>
> The engine flags this as a Critical risk — **85 out of 100** — sets it to **Pending with Manual Review**, and raises a bank-change velocity flag."

*Point at the email recipient field:*

> "Here's the critical security judgment. The confirmation email is sent to `procurement@orion-industrial.de` — the contact **on file in the ERP** — not to the submitter. If I replied to `k.brandt@orion-industrial.co`, I'd be handing the confirmation to the attacker. This one routing decision can prevent millions in fraudulent payments."

---

### Scenario B: Smart Name Normalization vs. Mule Account (~35 sec)

> "Let me show two contrasting cases back to back — one that should pass, and one that should not.
>
> **Edge 1a:** `Green Valley Foods Private Limited` submits with account holder `GREEN VALLEY FOODS PVT LTD`. A naive string compare fails that immediately. My engine strips both down to their core name, computes similarity — 99% — and approves it without a second thought. No false friction on a valid vendor.
>
> **Edge 1b:** `Brightpath Consulting LLC` submits a bank account held by `Sunrise Trading Co`. That's a completely different company on the payment account. The ABA routing number `021000021` passes my Mod-10 checksum and resolves to JPMorgan Chase — so the bank itself is real. But the payee name similarity is under 20%. That's a third-party mule account pattern. Flagged for review."

---

### Scenario C: Differential Resubmission Tracking (~30 sec)

**Open from Dashboard:** or quickly load Edge 4b:

> "When a vendor corrects some issues and resubmits, I don't just re-run the same checks. The engine pulls their previous run from SQLite and does a differential analysis.
>
> Here, Nimbus Data Labs fixed their missing contact email and uploaded the bank proof. Resolved — the system acknowledges that. But their EIN still has an invalid IRS prefix — `07` is not a recognized prefix. Still Open.
>
> The resubmission email doesn't re-list everything from scratch. It thanks them for what they fixed and asks only for what's still missing."

---

## 3:40 – 4:30 | Executive Dashboard, Risk Framework & Honest Scope

**Switch to Executive Dashboard tab:**

> "The dashboard auto-seeds all 9 benchmark scenarios on first launch — so anyone who opens the link immediately sees real data. Total ingestions, approval rates, failure reason charts, average latency.
>
> Click any row — this shows Deep Inspection — the full audit trail of every check, the risk gauge, and the guardrailed email. Every financial decision is completely reproducible."

*Click the Orion or Quickpay row to show 100/100 Critical.*

> "The Quickpay Global Traders scenario here is a watchlist hit — bank account flagged in a confirmed fraud case. Hard REJECTED, 100 out of 100 risk. And the vendor email? A polite neutral decline with no mention of fraud, watchlists, or internal flags. Educating a fraudster on exactly how they were caught makes the next attempt easier for them."

**Close with honest engineering reflection (20 sec):**

> "To be honest about scope: the tax IDs are verified mathematically, not through live government APIs — production would connect to GSTN, IRS TIN-Match, and EU VIES. Bank ownership is algorithmically resolved; production would use penny-drop or Confirmation of Payee. And documents are checklist-validated right now — not OCR-read.
>
> But the core pipeline, the judgment calls, the fraud heuristics, and the LLM guardrails are all production-grade. Thank you."

---

## Recording Checklist
- [ ] Live URL open: `https://jayaprakashzamp.streamlit.app/`
- [ ] Sidebar shows: **LLM Active — gemini-3.5-flash-lite**
- [ ] Clicked **Reload Demo** off-camera to populate the dashboard
- [ ] Under **5:00** total (aim for **4:30**)
- [ ] Own voice only, no AI narration, 1080p
- [ ] Video link set to **"Anyone with the link can view"** before submitting
