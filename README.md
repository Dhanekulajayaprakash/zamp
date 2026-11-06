# Vendor Onboarding Validator (Zamp ASA case study, PS-2)

A working process that takes a new-vendor submission, runs it through seven stages, decides
**Approved / Pending / Rejected**, and drafts the email back to the vendor. Every run is stored and
browsable in a dashboard.

**Principle: rules decide, the LLM only writes.** The decision is deterministic and auditable. The LLM is used
only to turn structured findings into a polite email, behind guardrails with a template fallback.

## Run locally
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your-key-here      # optional - without it emails use templates
streamlit run app.py
```

## Deploy (Streamlit Community Cloud, free)
1. Push this folder to a **public GitHub repo** (`runs.db` and secrets are git-ignored).
2. Go to share.streamlit.io -> **New app** -> pick the repo, branch `main`, main file `app.py`.
3. **Advanced settings -> Secrets**: paste `GEMINI_API_KEY = "your-key-here"`.
4. Deploy. Open the URL, click **Load demo history** in the sidebar, run one scenario to confirm.

> Storage is SQLite on the host's ephemeral disk: history is wiped when the app restarts or redeploys.
> The sidebar button reloads demo history in about a second. For durable history, point `db.py` at Postgres/Supabase.

## Stages
| # | Stage | Checks |
|---|---|---|
| 1 | Intake & completeness | required fields, 3-document checklist, email format |
| 2 | Tax ID validation | GSTIN (structure + checksum), EIN, UK VAT, DE VAT, SG UEN |
| 3 | Bank detail validation | IFSC, ABA checksum, UK sort code, IBAN mod-97, BIC country |
| 4 | Payee name match | normalise case/punctuation/legal suffixes, then fuzzy match |
| 5 | Cross-field consistency | tax-ID country vs. declared country, bank country vs. vendor country |
| 6 | Registry & watchlist | watchlist, duplicate, bank change on existing vendor, look-alike email domain |
| 7 | Decision | status, manual-review flag, next step, drafted email |

Outcome: any HARD STOP -> **Rejected**; any vendor-fixable or needs-review item -> **Pending**
(review items set the manual-review flag); otherwise **Approved**.

## Built-in test submissions (all fictional)
| Scenario | Expected |
|---|---|
| Happy path (Indian vendor) | Approved |
| Name differs only by legal suffix (Pvt Ltd vs Private Limited) | Approved |
| Bank account holder is a different company | Pending + manual review |
| UK vendor with a valid Indian GSTIN and Indian bank | Pending + manual review |
| Existing vendor, new IBAN, look-alike email domain | Pending + manual review, email goes to contact on file |
| Incomplete first attempt, then partial resubmission | Pending, with resolved / still-open diff |
| Account on internal watchlist | Rejected, neutral email |
| Duplicate of active vendor | Rejected |

## Assumptions
- "Buyer" is a fictional company; vendor master and watchlist are small synthetic datasets in `data.py`.
- Tax IDs are validated for format and checksum, **not existence**. Production would call GSTN, VIES and IRS TIN-matching.
- Bank ownership is checked by name only. Production would use penny-drop / Confirmation of Payee.
- Documents are a checklist (yes/no); their contents are not read.
- A name mismatch is *Pending + review* rather than *Reject*, since sole proprietors and trade names are legitimate.

## Files
`app.py` UI · `engine.py` rules and decision · `validators.py` tax/bank checks · `messages.py` email drafting ·
`db.py` run store · `data.py` synthetic data and test scenarios
