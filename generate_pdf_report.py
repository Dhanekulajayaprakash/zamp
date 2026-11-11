"""Generates a comprehensive 7-8 page executive PDF report for Zamp Vendor Onboarding Case Study."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas


# --------------- Page Decorations ---------------
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_decorations(n)
            super().showPage()
        super().save()

    def _draw_decorations(self, total):
        self.saveState()
        # Header (not on page 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(colors.HexColor("#94a3b8"))
            self.drawString(54, 752, "ZAMP AP — AUTONOMOUS VENDOR ONBOARDING INTELLIGENCE")
            self.drawRightString(558, 752, "IIT HYDERABAD  |  PS-2 CASE STUDY")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 745, 558, 745)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 46, 558, 46)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#94a3b8"))
        self.drawString(54, 33, "Confidential — For Evaluation Purposes Only  |  Author: Jayaprakash Dhanekula, B.Tech CSE, IIT Hyderabad")
        self.drawRightString(558, 33, f"Page {self._pageNumber} of {total}")
        self.restoreState()


# --------------- Style Factory ---------------
def make_styles():
    base = getSampleStyleSheet()
    OR = colors.HexColor("#ea580c")   # orange
    DK = colors.HexColor("#0f172a")   # dark slate
    SL = colors.HexColor("#475569")   # slate 600
    return {
        "title":    ParagraphStyle("T",  parent=base["Normal"], fontName="Helvetica-Bold",   fontSize=22, leading=27, textColor=OR,  spaceAfter=3),
        "subtitle": ParagraphStyle("St", parent=base["Normal"], fontName="Helvetica",        fontSize=10, leading=14, textColor=SL,  spaceAfter=5),
        "meta":     ParagraphStyle("M",  parent=base["Normal"], fontName="Helvetica",        fontSize=9,  leading=13, textColor=SL,  spaceAfter=10),
        "h1":       ParagraphStyle("H1", parent=base["Normal"], fontName="Helvetica-Bold",   fontSize=13, leading=17, textColor=DK,  spaceBefore=14, spaceAfter=5,  keepWithNext=True),
        "h2":       ParagraphStyle("H2", parent=base["Normal"], fontName="Helvetica-Bold",   fontSize=10.5,leading=14,textColor=OR,  spaceBefore=8,  spaceAfter=3,  keepWithNext=True),
        "h3":       ParagraphStyle("H3", parent=base["Normal"], fontName="Helvetica-Bold",   fontSize=9.5, leading=13, textColor=DK, spaceBefore=6,  spaceAfter=2,  keepWithNext=True),
        "body":     ParagraphStyle("B",  parent=base["Normal"], fontName="Helvetica",        fontSize=9,  leading=14, textColor=DK,  spaceAfter=5),
        "bullet":   ParagraphStyle("Bu", parent=base["Normal"], fontName="Helvetica",        fontSize=9,  leading=14, textColor=DK,  spaceAfter=3,   leftIndent=12, firstLineIndent=0),
        "callout":  ParagraphStyle("C",  parent=base["Normal"], fontName="Helvetica",        fontSize=9,  leading=14, textColor=DK),
        "th":       ParagraphStyle("Th", parent=base["Normal"], fontName="Helvetica-Bold",   fontSize=8.3,leading=11, textColor=DK),
        "tc":       ParagraphStyle("Tc", parent=base["Normal"], fontName="Helvetica",        fontSize=8,  leading=11, textColor=DK,  spaceAfter=0),
        "tc_small": ParagraphStyle("Ts", parent=base["Normal"], fontName="Helvetica",        fontSize=7.5,leading=10, textColor=DK),
        "caption":  ParagraphStyle("Ca", parent=base["Normal"], fontName="Helvetica-Oblique",fontSize=8,  leading=11, textColor=SL),
    }


def tbl(data, widths, border, hdr_bg="#f1f5f9", repeat=1, valign="TOP"):
    t = Table(data, colWidths=widths, repeatRows=repeat)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, repeat - 1), colors.HexColor(hdr_bg)),
        ("BOX",        (0, 0), (-1, -1), 0.6, border),
        ("INNERGRID",  (0, 0), (-1, -1), 0.4, border),
        ("VALIGN",     (0, 0), (-1, -1), valign),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return t


def callout_box(text, s, bg="#fff7ed", border="#fdba74", left_accent="#ea580c"):
    t = Table([[Paragraph(text, s["callout"])]], colWidths=[504])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
        ("BOX",        (0, 0), (-1, -1), 1,   colors.HexColor(border)),
        ("LINEBEFORE", (0, 0), (0,  -1), 4,   colors.HexColor(left_accent)),
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING",   (0, 0), (-1, -1), 11),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 11),
    ]))
    return t


# --------------- Main Builder ---------------
def build_pdf(filename="Zamp_Vendor_Onboarding_Evaluation_Report.pdf"):
    doc = SimpleDocTemplate(
        filename, pagesize=letter,
        leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=60,
    )
    s = make_styles()
    OR = colors.HexColor("#ea580c")
    BD = colors.HexColor("#cbd5e1")   # border
    story = []

    # ═══════════════════════════════════════════════════════════════
    # COVER PAGE
    # ═══════════════════════════════════════════════════════════════
    story += [
        Spacer(1, 0.4 * inch),
        Paragraph("Zamp AP", s["title"]),
        Paragraph("Autonomous Vendor Onboarding Intelligence Engine", ParagraphStyle(
            "cov", parent=s["subtitle"], fontSize=14, leading=18,
            textColor=colors.HexColor("#0f172a"), fontName="Helvetica-Bold", spaceAfter=6
        )),
        HRFlowable(width="100%", thickness=2, color=OR, spaceBefore=0, spaceAfter=12),
        Paragraph(
            "A fully deterministic, production-grade vendor onboarding pipeline with mathematical "
            "checksum validation, semantic entity resolution, BEC fraud defenses, composite risk "
            "scoring, and guardrailed Gemini 3.5 Flash-Lite email drafting — deployed live on Streamlit Cloud.",
            ParagraphStyle("cov2", parent=s["body"], fontSize=10.5, leading=16, spaceAfter=14)
        ),
    ]

    # Cover metadata table
    meta_data = [
        ["Author",          "Jayaprakash Dhanekula"],
        ["Degree",          "B.Tech, Computer Science & Engineering"],
        ["Institution",     "Indian Institute of Technology Hyderabad (IIT Hyderabad)"],
        ["Case Study",      "Problem Statement 2 — Autonomous Vendor Onboarding Intelligence"],
        ["Live Application", "https://jayaprakashzamp.streamlit.app/"],
        ["Source Repository","https://github.com/Dhanekulajayaprakash/zamp"],
        ["LLM Model",       "Gemini 3.5 Flash-Lite (primary) with gemini-3.8-flash fallback"],
        ["Pipeline Latency","~15 – 35 ms end-to-end (deterministic stages)"],
    ]
    meta_rows = [[Paragraph(f"<b>{k}</b>", s["tc"]), Paragraph(v, s["tc"])] for k, v in meta_data]
    story.append(tbl(meta_rows, [150, 354], BD, hdr_bg="#ffffff", repeat=0))
    story.append(Spacer(1, 14))

    story.append(callout_box(
        "<b>Core Architectural Principle — Rules Decide, the LLM Only Communicates.</b><br/>"
        "Every financial approval, rejection, and risk flag is produced by deterministic Python rules that apply "
        "real mathematical algorithms — not statistical predictions. Gemini 3.5 Flash-Lite is deployed strictly "
        "and exclusively to draft polite, professional vendor correspondence, operating behind four independent "
        "safety guardrails. The operational pipeline is designed never to stall: even without an API key, a "
        "structured fallback template is served in under one millisecond.",
        s
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SECTION 1 — EXECUTIVE SUMMARY
    # ═══════════════════════════════════════════════════════════════
    story.append(Paragraph("1. Executive Summary", s["h1"]))
    story.append(Paragraph(
        "Accounts Payable departments onboard dozens of new suppliers each quarter, manually reviewing company "
        "registrations, government tax credentials, banking details, and compliance certificates. Manual review is "
        "slow, fatigue-prone on high-volume days, and critically exposed to supply-chain fraud — particularly "
        "Business Email Compromise (BEC) payment redirection, which causes more than $2.7 billion in annual "
        "enterprise losses globally.",
        s["body"]
    ))
    story.append(Paragraph(
        "This project delivers an Autonomous Vendor Onboarding Intelligence Engine that automates the entire "
        "review process end-to-end. It evaluates submissions through six sequential verification gates, synthesizes "
        "a 0–100 Composite Risk Score, produces a fully auditable decision in under 35 milliseconds, and dispatches "
        "a Gemini-drafted vendor email — all without human intervention except when genuinely warranted.",
        s["body"]
    ))

    # Strength Summary Table
    story.append(Paragraph("Key Engineering Strengths", s["h2"]))
    str_data = [
        [Paragraph("Capability", s["th"]), Paragraph("What Makes It Stand Out", s["th"]), Paragraph("Demonstrated In", s["th"])],
        [Paragraph("Mathematical Checksum Validation", s["tc"]),
         Paragraph("Implements Mod-36 GSTIN, ABA Mod-10, and IBAN Mod-97 — not regex. Catches transposed digits that look syntactically valid.", s["tc"]),
         Paragraph("Stages 2 & 3", s["tc"])],
        [Paragraph("40-Institution Offline Bank Registry", s["tc"]),
         Paragraph("Resolves IFSC/ABA/SWIFT codes to official bank names and cross-checks against vendor-declared bank name without any external API.", s["tc"]),
         Paragraph("Stage 3", s["tc"])],
        [Paragraph("Semantic Entity Normalization", s["tc"]),
         Paragraph("Strips 24 international corporate suffixes, normalizes punctuation, and runs dual token-sorted fuzzy similarity to separate legitimate variants from mule accounts.", s["tc"]),
         Paragraph("Stage 4", s["tc"])],
        [Paragraph("BEC & Payment Fraud Defense", s["tc"]),
         Paragraph("Detects bank-change velocity on active vendors, routes confirmation emails to the contact ON FILE (not the submitter), and quarantines look-alike domains.", s["tc"]),
         Paragraph("Stage 6 / Edge 3", s["tc"])],
        [Paragraph("Composite Risk Score (0–100)", s["tc"]),
         Paragraph("Aggregates block / review / fix signal weights plus fraud-pattern multipliers into a four-band risk label for instant triage — displayed on a live visual gauge.", s["tc"]),
         Paragraph("Stage 7 / Dashboard", s["tc"])],
        [Paragraph("Differential Resubmission Engine", s["tc"]),
         Paragraph("Compares each resubmission against the prior SQLite record and classifies every flagged item as Resolved, Still Open, or New Anomaly — contextualising the follow-up email.", s["tc"]),
         Paragraph("Edge 4b", s["tc"])],
        [Paragraph("Guardrailed LLM + Deterministic Fallback", s["tc"]),
         Paragraph("Gemini 3.5 Flash-Lite receives only vendor-safe facts, passes output through 9 keyword + account-number filters, and falls back to structured templates without breaking the pipeline.", s["tc"]),
         Paragraph("All scenarios", s["tc"])],
        [Paragraph("Zero-Setup Auto-Seeded Dashboard", s["tc"]),
         Paragraph("All 9 benchmark scenarios are seeded and processed on the first deployment visit with KPI metrics, failure-reason charts, and row-level audit replay.", s["tc"]),
         Paragraph("Dashboard tab", s["tc"])],
    ]
    story.append(tbl(str_data, [140, 270, 94], BD))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SECTION 2 — PIPELINE ARCHITECTURE
    # ═══════════════════════════════════════════════════════════════
    story.append(Paragraph("2. Seven-Gate Deterministic Verification Pipeline", s["h1"]))
    story.append(Paragraph(
        "Every submission passes through six analytical stages followed by a decision & risk-scoring gate. "
        "Each stage produces structured check objects carrying a <b>rule label</b>, <b>status</b> (pass / warn / fail), "
        "<b>human-readable detail</b>, an <b>effect tag</b> (<i>none, fix, review, block</i>), and an optional "
        "<b>vendor_ask</b> — the exact phrasing used in the follow-up email. This schema makes the entire pipeline "
        "fully self-documenting and auditable.",
        s["body"]
    ))

    stage_data = [
        [Paragraph("Stage", s["th"]), Paragraph("Verification Target", s["th"]),
         Paragraph("Algorithmic Logic & Invariants Checked", s["th"]), Paragraph("Effect & Decision Impact", s["th"])],
        [Paragraph("<b>1.</b> Intake &amp;\nCompleteness", s["tc"]),
         Paragraph("Mandatory fields &amp; compliance certificates", s["tc"]),
         Paragraph("All required fields checked. Bank code requirement is dynamic — mandatory only for IN, US, GB jurisdictions. Email validated against RFC address pattern. All three compliance documents (tax certificate, incorporation cert, bank proof) verified.", s["tc"]),
         Paragraph("Missing field or doc → <b>PENDING (vendor to fix)</b>", s["tc"])],
        [Paragraph("<b>2.</b> Tax ID\nValidation", s["tc"]),
         Paragraph("National tax credential format &amp; jurisdiction", s["tc"]),
         Paragraph("India GSTIN: Luhn-variant Mod-36 checksum over 14 chars, state code vs. 38 jurisdictions, embedded PAN extraction.\nUS EIN: 2-digit IRS prefix table (all valid FedGov-issued prefixes coded).\nUK VAT: GB + 9/12 digits.\nDE USt-IdNr: DE + 9 digits.\nSG UEN: pattern + length. Detects valid foreign tax IDs and escalates to Stage 5.", s["tc_small"]),
         Paragraph("Checksum fail → <b>Fix</b>\nForeign ID detected → <b>Review</b>", s["tc"])],
        [Paragraph("<b>3.</b> Bank Detail\nValidation", s["tc"]),
         Paragraph("Routing checksums &amp; offline bank name cross-check", s["tc"]),
         Paragraph("Indian IFSC: 4-char alpha prefix + 7-char branch code format verified.\nUS ABA: 9-digit FedWire Mod-10 checksum (3·d1 + 7·d2 + 1·d3 … = 0 mod 10).\nEU/UK IBAN: ISO 7064 Mod-97 (integer conversion, N mod 97 = 1).\nBank code resolved against 40-entry offline registry; declared bank name cross-checked at ≥60% similarity.", s["tc_small"]),
         Paragraph("Bad format → <b>Fix</b>\nBank name clash → <b>Review</b>", s["tc"])],
        [Paragraph("<b>4.</b> Payee Entity\nResolution", s["tc"]),
         Paragraph("Fuzzy payee-name matching &amp; mule-account detection", s["tc"]),
         Paragraph("Step 1: Strip 24 international legal suffixes (Pvt, Ltd, Limited, LLC, GmbH, Inc, AG, Pte, Plc, Sarl, BV, NV, FZE, LP…).\nStep 2: Normalize punctuation, expand '&' → 'and', lower-case.\nStep 3: Max of linear SequenceMatcher ratio and token-sorted ratio.\n≥90% → PASS, 70–89% → partial review, <70% → mule-account flag.", s["tc_small"]),
         Paragraph("≥90% → <b>PASS</b>\n70–89% → <b>Review</b>\n<70% → <b>Mule Alert</b>", s["tc"])],
        [Paragraph("<b>5.</b> Cross-Field\nConsistency", s["tc"]),
         Paragraph("Multi-attribute invariance", s["tc"]),
         Paragraph("Tax ID country vs. declared country (escalates foreign ID detected in Stage 2).\nBank country vs. vendor country (offshore settlement flag).\nAddress must contain country-specific postal code: IN 6-digit PIN, US 5-digit ZIP, GB postcode regex, DE 5-digit PLZ, SG 6-digit, FR, BR.\nContact email domain checked for company name keyword alignment; free-mailbox advisory (Gmail, Yahoo, Outlook, Hotmail, iCloud).", s["tc_small"]),
         Paragraph("Mismatch → <b>Review</b>\nFree mail → <b>Advisory</b>", s["tc"])],
        [Paragraph("<b>6.</b> Registry &amp;\nWatchlist", s["tc"]),
         Paragraph("Internal fraud watchlist, duplicate detection &amp; BEC defense", s["tc"]),
         Paragraph("Internal watchlist scanned on 3 axes: account number, tax ID, normalized legal name.\nERP master registry checked: same tax ID → existing vendor.\nIf existing vendor + new bank account → bank-change velocity flag (BEC primary vector).\nLook-alike domain on existing vendor contact triggers contact domain change flag.\nEmail deliberately routed to contact ON FILE, not the submitter.", s["tc_small"]),
         Paragraph("Watchlist → <b>REJECTED</b>\nDuplicate → <b>REJECTED</b>\nBank change → <b>Review</b>", s["tc"])],
        [Paragraph("<b>7.</b> Decision &amp;\nRisk Scoring", s["tc"]),
         Paragraph("Final decision + 0–100 Composite Risk Score + resubmission delta", s["tc"]),
         Paragraph("Aggregates all effects: any block → REJECTED; any fix or review → PENDING; none → APPROVED.\nComposite Risk Score: +40 per block, +20 per review, +10 per fix, plus fraud multipliers (+50 watchlist, +25 bank change, +20 contact domain change, +15 offshore bank, +5 free mailbox). Capped at 100.\nDelta tracking: compares prior SQLite run → Resolved / Still Open / New Anomalies.\nSanitized facts dispatched to Gemini / template fallback.", s["tc_small"]),
         Paragraph("ERP Enable /\nOps Hold /\nHard Stop", s["tc"])],
    ]
    story.append(tbl(stage_data, [65, 97, 232, 110], BD))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SECTION 3 — CHECKSUM ENGINES
    # ═══════════════════════════════════════════════════════════════
    story.append(Paragraph("3. Mathematical Checksum Engines — Beyond Regex", s["h1"]))
    story.append(Paragraph(
        "A naive approach using only regular expressions verifies character shape — it confirms that a "
        "GSTIN looks like 15 characters in the right arrangement, but it cannot detect a single transposed digit. "
        "This engine implements the actual mathematical algorithms used by government and banking systems.",
        s["body"]
    ))

    story.append(Paragraph("3.1  Indian GSTIN — Luhn-Variant Mod-36 Checksum", s["h2"]))
    story.append(Paragraph(
        "The GSTIN is a 15-character alphanumeric identifier. The first two characters are a state code "
        "(verified against all 38 valid Indian GST jurisdictions), characters 3–12 are the PAN, character 13 "
        "is the entity sequence, character 14 is always 'Z', and character 15 is the check character.",
        s["body"]
    ))
    story.append(Paragraph(
        "The check character is computed by applying alternating weights of 1 and 2 to the base-36 values "
        "of the first 14 characters, summing (quotient × 36 + remainder), and taking (36 − total mod 36) mod 36 "
        "as the index into the 36-character set '0–9A–Z'. This catches every single-character substitution "
        "and most transpositions — the same algorithm the Indian GST system uses.",
        s["body"]
    ))
    story.append(Paragraph(
        "Additionally, the engine extracts the 2-digit state code and resolves it to the state name (e.g., "
        "36 → Telangana, 27 → Maharashtra, 29 → Karnataka), then extracts and displays the embedded 10-character "
        "PAN — giving the verifier two additional cross-check points with no extra API call.",
        s["body"]
    ))

    story.append(Paragraph("3.2  US ABA Routing — FedWire Mod-10 Weighted Checksum", s["h2"]))
    story.append(Paragraph(
        "The Federal Reserve requires all 9-digit ABA routing numbers to satisfy the weighted checksum: "
        "(3×d1 + 7×d2 + 1×d3 + 3×d4 + 7×d5 + 1×d6 + 3×d7 + 7×d8 + 1×d9) mod 10 = 0. "
        "This eliminates miskeyed routing numbers before any wire instruction is ever created.",
        s["body"]
    ))

    story.append(Paragraph("3.3  European & UK IBAN — ISO 7064 Mod-97 Checksum", s["h2"]))
    story.append(Paragraph(
        "IBAN verification rearranges the IBAN string (moving the first 4 characters to the end), "
        "converts all alphabetic characters to their numeric equivalents (A=10, B=11, …, Z=35), "
        "forms a large integer, and verifies that N mod 97 = 1. The engine applies this to German "
        "(DE), UK (GB), and all SEPA-region IBANs (22–34 characters), preventing disbursement to any "
        "miskeyed bank coordinate.",
        s["body"]
    ))

    # ═══════════════════════════════════════════════════════════════
    # SECTION 4 — OFFLINE BANK DIRECTORY
    # ═══════════════════════════════════════════════════════════════
    story.append(Paragraph("4. Offline 40-Institution Bank Registry", s["h1"]))
    story.append(Paragraph(
        "A common failure mode in vendor validation systems is complete reliance on third-party banking APIs "
        "for name resolution. When those APIs are unavailable — network latency, rate limits, or sandbox "
        "isolation — the validation step either fails entirely or silently skips. This engine eliminates that "
        "dependency by embedding a curated offline registry of 40 real financial institutions.",
        s["body"]
    ))

    bk_data = [
        [Paragraph("Region", s["th"]), Paragraph("Code Type", s["th"]), Paragraph("Sample Entries", s["th"])],
        [Paragraph("India", s["tc"]),
         Paragraph("IFSC Prefix (4 chars)", s["tc"]),
         Paragraph("SBIN → State Bank of India, HDFC → HDFC Bank, ICIC → ICICI Bank, UTIB → Axis Bank, PUNB → Punjab National Bank, BARB → Bank of Baroda, CNRB → Canara Bank, UBIN → Union Bank, KKBK → Kotak Mahindra, YESB → Yes Bank, INDB → IndusInd Bank, FDRL → Federal Bank, KARB → Karnataka Bank (20 entries)", s["tc"])],
        [Paragraph("United States", s["tc"]),
         Paragraph("ABA Prefix (4 digits)", s["tc"]),
         Paragraph("0210 → JPMorgan Chase, 0260 → Bank of America, 0710 & 1210 → Wells Fargo, 0740 → PNC Bank, 0440 → HSBC, 0312 → TD Bank, 0611 → US Bank, 0531 → Truist Bank (10 entries)", s["tc"])],
        [Paragraph("Singapore", s["tc"]),
         Paragraph("SWIFT/BIC (8 chars)", s["tc"]),
         Paragraph("DBSSSGSG → DBS Bank, OCBCSGSG → OCBC Bank, UOVBSGSG → UOB (3 entries)", s["tc"])],
        [Paragraph("Germany", s["tc"]),
         Paragraph("SWIFT/BIC (8 chars)", s["tc"]),
         Paragraph("INGDDEFF → ING Bank Germany, COBADEFF → Commerzbank, DEUTDEFF → Deutsche Bank (3 entries)", s["tc"])],
        [Paragraph("United Kingdom", s["tc"]),
         Paragraph("SWIFT/BIC (8 chars)", s["tc"]),
         Paragraph("BARCGB22 → Barclays, NWBKGB2L → NatWest, LOYDGB2L → Lloyds, HSBCGB2L → HSBC UK (4 entries)", s["tc"])],
    ]
    story.append(tbl(bk_data, [80, 115, 309], BD))
    story.append(Spacer(1, 7))
    story.append(Paragraph(
        "<b>Semantic Cross-Check:</b> After resolving a bank code, the engine computes string similarity between "
        "the resolved name and the vendor's declared bank name using SequenceMatcher. If the similarity falls "
        "below 60% — for example, a vendor declares 'HDFC Bank' but enters an IFSC code starting with 'SBIN' "
        "(which resolves to State Bank of India) — a <i>Semantic Bank Name Mismatch</i> review flag is raised "
        "immediately. This catches a class of fraud where a correct-format but wrong routing code is submitted "
        "to redirect payment to a different institution.",
        s["body"]
    ))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SECTION 5 — PAYEE ENTITY RESOLUTION & MULE DETECTION
    # ═══════════════════════════════════════════════════════════════
    story.append(Paragraph("5. Payee Entity Resolution & Mule Account Detection", s["h1"]))
    story.append(Paragraph(
        "Direct string comparison ('==') fails legitimate vendors routinely. A company incorporated as "
        "'Green Valley Foods Private Limited' may hold a bank account as 'GREEN VALLEY FOODS PVT LTD' — "
        "four differences in one field, all completely valid. Rejecting this outright would create false "
        "friction on a compliant supplier.",
        s["body"]
    ))
    story.append(Paragraph(
        "Conversely, a fraudulent submission from 'Brightpath Consulting LLC' presenting a bank account "
        "held by 'Sunrise Trading Co' is a textbook mule account — a third party's account used to intercept "
        "payment. These two cases demand opposite responses, and a fixed similarity threshold without normalization "
        "would likely misclassify both.",
        s["body"]
    ))
    story.append(Paragraph("Three-Step Normalization Pipeline:", s["h3"]))
    story.append(Paragraph(
        "<b>Step 1 — Legal Suffix Stripping:</b> Prunes 24 international corporate entity tokens: "
        "<i>private, pvt, limited, ltd, llc, llp, inc, incorporated, corp, corporation, co, company, "
        "gmbh, ag, pte, plc, sa, sarl, bv, nv, fze, fzco, lp, pllc.</i>",
        s["bullet"]
    ))
    story.append(Paragraph(
        "<b>Step 2 — Punctuation & Symbol Normalization:</b> Expands '&' to 'and', strips all "
        "non-word characters, and converts to lowercase — ensuring 'AT&T Corp.' and 'at and t' "
        "are compared fairly.",
        s["bullet"]
    ))
    story.append(Paragraph(
        "<b>Step 3 — Dual Similarity Scoring:</b> Computes two independent SequenceMatcher ratios — "
        "one on the linear normalized string, one on the alphabetically sorted tokens — and takes the "
        "maximum. This handles word-order variations common in trading names. Thresholds: ≥90% → PASS "
        "(normal variation); 70–89% → Partial match, human confirms; <70% → Mule account flag, "
        "payment blocked pending review.",
        s["bullet"]
    ))
    story.append(Paragraph(
        "Applied to the two scenarios: Green Valley's normalized names differ only on suffixes → 99% → PASS. "
        "Brightpath vs. Sunrise Trading → <20% → Mule Account Pattern → flagged for human review immediately, "
        "even though the ABA routing checksum passed and the bank itself (JPMorgan Chase) was legitimate.",
        s["body"]
    ))

    # ═══════════════════════════════════════════════════════════════
    # SECTION 6 — BEC DEFENSE
    # ═══════════════════════════════════════════════════════════════
    story.append(Paragraph("6. Business Email Compromise & Payment Fraud Defense", s["h1"]))
    story.append(callout_box(
        "Business Email Compromise (BEC) is the top financial fraud vector targeting Accounts Payable, "
        "responsible for over <b>$2.7 billion in annual enterprise losses</b> (FBI IC3 2023). The most "
        "common AP variant: an attacker compromises or spoofs a vendor email account, then submits a "
        "'bank detail update' request to redirect future payments to an attacker-controlled account.",
        s, bg="#fef2f2", border="#fca5a5", left_accent="#dc2626"
    ))
    story.append(Spacer(1, 7))
    story.append(Paragraph(
        "The <b>Orion Industrial Supplies (Edge Case 3)</b> scenario demonstrates four independent "
        "defenses against this attack vector:",
        s["body"]
    ))

    bec_data = [
        [Paragraph("Defense Mechanism", s["th"]), Paragraph("How It Works", s["th"]), Paragraph("Why It Matters", s["th"])],
        [Paragraph("<b>Bank-Change Velocity Flag</b>", s["tc"]),
         Paragraph("Engine detects that the submitted Tax ID matches active ERP vendor V-1042 (Orion Industrial GmbH) but presents a new IBAN (changing from …3000 to a new account).", s["tc"]),
         Paragraph("Any bank detail change on an existing vendor is the primary BEC attack vector. Automatic hold prevents unauthorized payment redirection.", s["tc"])],
        [Paragraph("<b>Look-Alike Domain Detection</b>", s["tc"]),
         Paragraph("Contact email domain 'orion-industrial.co' is compared against the registered domain 'orion-industrial.de'. A single character difference from the legitimate TLD is flagged.", s["tc"]),
         Paragraph("BEC attackers register look-alike domains (replacing .de with .co, .com with .co.uk) to intercept replies and appear credible.", s["tc"])],
        [Paragraph("<b>Pending Hold (not Auto-Reject)</b>", s["tc"]),
         Paragraph("The record is placed in PENDING + Manual Review with Risk Score 85/100 (Critical), not outright rejected.", s["tc"]),
         Paragraph("Legitimate vendors do change banks. Hard-rejecting all bank changes would block valid treasury updates. Human judgment resolves ambiguous cases.", s["tc"])],
        [Paragraph("<b>Contact-on-File Email Routing</b>", s["tc"]),
         Paragraph("The verification alert is emailed to 'procurement@orion-industrial.de' — the email registered in the ERP master record — not to the submitter's email.", s["tc"]),
         Paragraph("Replying to the submitter in an account-takeover scenario hands the confirmation directly to the attacker. Routing to the on-file contact ensures the legitimate vendor is notified.", s["tc"])],
        [Paragraph("<b>Zero Fraud Disclosure</b>", s["tc"]),
         Paragraph("Watchlist hit and fraud-flagged rejections (e.g., Quickpay Global Traders, 100/100 Critical) receive a neutral decline with no mention of fraud, risk, or watchlists.", s["tc"]),
         Paragraph("Disclosing exactly which signals triggered detection teaches threat actors how to evade those checks on the next attempt.", s["tc"])],
    ]
    story.append(tbl(bec_data, [120, 190, 194], BD))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SECTION 7 — COMPOSITE RISK SCORING
    # ═══════════════════════════════════════════════════════════════
    story.append(Paragraph("7. Composite Risk Scoring Framework (0–100 Gauge)", s["h1"]))
    story.append(Paragraph(
        "Every submission receives a 0–100 Composite Risk Score that aggregates the severity and "
        "type of every flagged check into a single operational triage signal. The score drives a "
        "four-band risk label displayed on a live visual gauge in the UI.",
        s["body"]
    ))

    risk_weight_data = [
        [Paragraph("Signal / Anomaly", s["th"]), Paragraph("Points Added", s["th"]), Paragraph("Operational Rationale", s["th"])],
        [Paragraph("Internal Watchlist Hit (account / tax ID / name)", s["tc"]), Paragraph("<b>+50 pts</b>", s["tc"]), Paragraph("Direct match to confirmed payment fraud or debarment case — immediate Critical classification.", s["tc"])],
        [Paragraph("Bank Detail Change on Active ERP Vendor", s["tc"]), Paragraph("<b>+25 pts</b>", s["tc"]), Paragraph("Primary BEC attack vector; payment redirection risk on an already-trusted vendor relationship.", s["tc"])],
        [Paragraph("Look-Alike Contact Email Domain", s["tc"]), Paragraph("<b>+20 pts</b>", s["tc"]), Paragraph("Strong indicator of domain spoofing combined with a bank-change submission.", s["tc"])],
        [Paragraph("Third-Party Payee / Mule Account Pattern", s["tc"]), Paragraph("<b>+20 pts</b>", s["tc"]), Paragraph("Account holder deviates from the incorporated legal entity — funds would flow to an unrelated party.", s["tc"])],
        [Paragraph("Bank Country Mismatch (Offshore Settlement Route)", s["tc"]), Paragraph("<b>+15 pts</b>", s["tc"]), Paragraph("Bank in a different country than the vendor's declared registration, common fraud-layering indicator.", s["tc"])],
        [Paragraph("Each Review-Effect Check (beyond above multipliers)", s["tc"]), Paragraph("<b>+20 pts</b>", s["tc"]), Paragraph("Human judgment needed; contributes to overall risk proportionally.", s["tc"])],
        [Paragraph("Each Fix-Effect Check (vendor error or omission)", s["tc"]), Paragraph("<b>+10 pts</b>", s["tc"]), Paragraph("Vendor clerical issue, missing document, or format error — lower risk weight.", s["tc"])],
        [Paragraph("Free-Mailbox Contact Domain (Gmail / Yahoo / Outlook)", s["tc"]), Paragraph("<b>+5 pts</b>", s["tc"]), Paragraph("Advisory signal indicating absence of corporate email infrastructure; not blocking alone.", s["tc"])],
    ]
    story.append(tbl(risk_weight_data, [188, 70, 246], BD))
    story.append(Spacer(1, 7))

    risk_band_data = [
        [Paragraph("Score Range", s["th"]), Paragraph("Risk Band", s["th"]), Paragraph("Typical Profile & Operational Action", s["th"])],
        [Paragraph("0 – 20", s["tc"]), Paragraph("<b>Low</b>", s["tc"]), Paragraph("All or nearly all checks passed. Routine approval — create ERP vendor record and enable for payment run.", s["tc"])],
        [Paragraph("21 – 45", s["tc"]), Paragraph("<b>Medium</b>", s["tc"]), Paragraph("Minor clerical issues or advisory flags. Vendor remediation request dispatched; re-run on correction.", s["tc"])],
        [Paragraph("46 – 70", s["tc"]), Paragraph("<b>High</b>", s["tc"]), Paragraph("Significant structural inconsistencies (e.g., Tax ID country mismatch, offshore bank route). Escalate to Vendor Master Data.", s["tc"])],
        [Paragraph("71 – 100", s["tc"]), Paragraph("<b>Critical</b>", s["tc"]), Paragraph("Active fraud signals (watchlist hit, BEC bank change + look-alike domain). Escalate to Fraud Ops; hold all payments.", s["tc"])],
    ]
    story.append(tbl(risk_band_data, [80, 80, 344], BD))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SECTION 8 — VERIFIED SCENARIO BENCHMARKS
    # ═══════════════════════════════════════════════════════════════
    story.append(Paragraph("8. Verified Scenario Benchmarks — 9 Test Cases", s["h1"]))
    story.append(Paragraph(
        "All nine benchmark scenarios are pre-loaded into the live application and auto-seeded on first deployment. "
        "The table below reflects results computed directly by running the pipeline against the production codebase.",
        s["body"]
    ))

    bench_data = [
        [Paragraph("Scenario", s["th"]), Paragraph("Country", s["th"]), Paragraph("Decision", s["th"]),
         Paragraph("Checks\nPassed", s["th"]), Paragraph("Risk\nScore", s["th"]), Paragraph("Risk Band", s["th"]),
         Paragraph("Key Judgment Demonstrated", s["th"])],
        [Paragraph("<b>Happy Path</b>\nApex Cloud Solutions", s["tc"]), Paragraph("IN", s["tc"]),
         Paragraph("APPROVED", s["tc"]), Paragraph("15 / 15", s["tc"]), Paragraph("0", s["tc"]),
         Paragraph("Low", s["tc"]),
         Paragraph("Full happy path: GSTIN Mod-36 + state 36 → Telangana + PAN, IFSC → HDFC Bank, PIN code, domain match.", s["tc"])],
        [Paragraph("<b>Edge 1a</b>\nGreen Valley Foods", s["tc"]), Paragraph("IN", s["tc"]),
         Paragraph("APPROVED", s["tc"]), Paragraph("15 / 15", s["tc"]), Paragraph("0", s["tc"]),
         Paragraph("Low", s["tc"]),
         Paragraph("'Private Limited' vs 'PVT LTD' — 24-suffix normalizer passes this without false friction.", s["tc"])],
        [Paragraph("<b>Edge 1b</b>\nBrightpath Consulting", s["tc"]), Paragraph("US", s["tc"]),
         Paragraph("PENDING", s["tc"]), Paragraph("13 / 14", s["tc"]), Paragraph("20", s["tc"]),
         Paragraph("Low", s["tc"]),
         Paragraph("ABA 021000021 passes Mod-10 and resolves to JPMorgan Chase. But 'Sunrise Trading Co' as payee → mule-account flag.", s["tc"])],
        [Paragraph("<b>Edge 2</b>\nSterling Bridge Consulting", s["tc"]), Paragraph("GB", s["tc"]),
         Paragraph("PENDING", s["tc"]), Paragraph("11 / 14", s["tc"]), Paragraph("55", s["tc"]),
         Paragraph("High", s["tc"]),
         Paragraph("Claims UK registration, presents valid GSTIN (India) and Axis Bank IFSC. Tax country mismatch + offshore bank route caught.", s["tc"])],
        [Paragraph("<b>Edge 3</b>\nOrion Industrial GmbH (BEC)", s["tc"]), Paragraph("DE", s["tc"]),
         Paragraph("PENDING", s["tc"]), Paragraph("13 / 15", s["tc"]), Paragraph("85", s["tc"]),
         Paragraph("Critical", s["tc"]),
         Paragraph("Active vendor V-1042, new IBAN, look-alike .co domain. Email routed to contact ON FILE. Classic BEC pattern quarantined.", s["tc"])],
        [Paragraph("<b>Edge 4a</b>\nNimbus Data Labs (1st attempt)", s["tc"]), Paragraph("US", s["tc"]),
         Paragraph("PENDING", s["tc"]), Paragraph("8 / 11", s["tc"]), Paragraph("30", s["tc"]),
         Paragraph("Medium", s["tc"]),
         Paragraph("Missing contact email and bank proof, EIN prefix '07' invalid (not in IRS prefix table). Three clear fix items dispatched.", s["tc"])],
        [Paragraph("<b>Edge 4b</b>\nNimbus Data Labs (resubmit)", s["tc"]), Paragraph("US", s["tc"]),
         Paragraph("PENDING", s["tc"]), Paragraph("12 / 13", s["tc"]), Paragraph("10", s["tc"]),
         Paragraph("Low", s["tc"]),
         Paragraph("Delta engine: email + bank proof → Resolved. EIN prefix → Still Open. Email thanks them for fixes, asks only for outstanding item.", s["tc"])],
        [Paragraph("<b>Bonus</b>\nQuickpay Global Traders (Watchlist)", s["tc"]), Paragraph("SG", s["tc"]),
         Paragraph("REJECTED", s["tc"]), Paragraph("12 / 14", s["tc"]), Paragraph("100", s["tc"]),
         Paragraph("Critical", s["tc"]),
         Paragraph("Perfect submission except account 0721983456 matches confirmed fraud case FR-2025-118. Hard stop. Neutral decline email — zero fraud disclosure.", s["tc"])],
        [Paragraph("<b>Bonus</b>\nKestrel Packaging Ltd (Duplicate)", s["tc"]), Paragraph("GB", s["tc"]),
         Paragraph("REJECTED", s["tc"]), Paragraph("11 / 12", s["tc"]), Paragraph("40", s["tc"]),
         Paragraph("Medium", s["tc"]),
         Paragraph("Tax ID and account number both match active ERP vendor V-1010 (onboarded 2024-11-02). Duplicate creation blocked.", s["tc"])],
    ]
    story.append(tbl(bench_data, [98, 38, 54, 38, 36, 44, 196], BD, valign="MIDDLE"))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SECTION 9 — GUARDRAILED LLM
    # ═══════════════════════════════════════════════════════════════
    story.append(Paragraph("9. Guardrailed LLM Communication Engine", s["h1"]))
    story.append(Paragraph(
        "Vendor communication is the one and only place where a language model is used. The model receives "
        "a sanitized JSON object of vendor-safe facts (vendor name, contact name, communication mode, and "
        "any vendor-facing item requests), never the internal decision reasoning, risk scores, watchlist "
        "matches, or fraud flags.",
        s["body"]
    ))

    llm_data = [
        [Paragraph("Guardrail Layer", s["th"]), Paragraph("Implementation", s["th"])],
        [Paragraph("<b>Data Isolation</b>", s["tc"]),
         Paragraph("Internal risk scores, watchlist match reasons, BEC flags, and fraud heuristic details are completely excluded from the LLM prompt. The model is structurally unable to disclose them.", s["tc"])],
        [Paragraph("<b>Forbidden Keyword Filter</b>", s["tc"]),
         Paragraph("Every LLM-drafted email is scanned for 9 forbidden terms: watchlist, blocklist, fraud, suspicious, sanction, debar, mule, risk score, compromise. Any hit invalidates the draft and falls back to template.", s["tc"])],
        [Paragraph("<b>Account Number Redaction</b>", s["tc"]),
         Paragraph("If the submitted account number (≥4 characters) appears anywhere in the generated body, the draft is rejected. Bank details are never echoed in outbound correspondence.", s["tc"])],
        [Paragraph("<b>Multi-Model Fallback Chain</b>", s["tc"]),
         Paragraph("Models tried in order: gemini-3.5-flash-lite → gemini-3.8-flash → gemini-2.5-flash-lite. The used model name is recorded and displayed in the UI (e.g., 'engine: LLM (gemini-3.5-flash-lite)').", s["tc"])],
        [Paragraph("<b>Deterministic Template Fallback</b>", s["tc"]),
         Paragraph("If all models fail (network error, quota exhaustion, any safety check failure), a pre-compiled structured template is served in <1 ms. The pipeline never stalls, errors, or exposes a broken email.", s["tc"])],
        [Paragraph("<b>Output Format Enforcement</b>", s["tc"]),
         Paragraph("The prompt requires 'Subject: ...' on the first line followed by the body. The response parser strips markdown fences and handles bolded Subject labels. If the format is unrecognized, template fallback activates.", s["tc"])],
        [Paragraph("<b>Four Communication Modes</b>", s["tc"]),
         Paragraph("welcome (APPROVED), request_info (PENDING — list vendor asks), verify_bank_change (PENDING — BEC flag, out-of-band call required), decline (REJECTED — no reason disclosed).", s["tc"])],
    ]
    story.append(tbl(llm_data, [145, 359], BD))
    story.append(Spacer(1, 7))
    story.append(Paragraph(
        "<b>Resubmission-Aware Email Context:</b> When generating a request_info email for a resubmission, "
        "the LLM is given the resolved items from the previous attempt and instructed to acknowledge them "
        "explicitly — thanking the vendor for what they fixed before listing what remains. This context-aware "
        "communication reduces vendor friction and reply cycles.",
        s["body"]
    ))

    # ═══════════════════════════════════════════════════════════════
    # SECTION 10 — DASHBOARD & SYSTEM DESIGN
    # ═══════════════════════════════════════════════════════════════
    story.append(Paragraph("10. Executive Dashboard, System Design & Production Roadmap", s["h1"]))

    story.append(Paragraph("10.1  Executive Audit Dashboard", s["h2"]))
    story.append(Paragraph(
        "The <b>Executive Dashboard</b> tab is fully operational from the first deployment visit with no "
        "manual data entry required. On cold start, the application auto-seeds all 9 benchmark scenarios "
        "through the full pipeline and persists results to SQLite. The dashboard presents:",
        s["body"]
    ))
    for bullet in [
        "Live KPI strip — Total Ingestions, Approved / Pending / Rejected counts with percentages, Average Latency.",
        "Decision Breakdown bar chart and Top Failure & Review Reasons chart (top 6 rule codes by frequency).",
        "Historical Audit Trail with server-side filtering by decision status and free-text vendor name search.",
        "Deep Inspection on row click — full pipeline stage replay, risk gauge, and guardrailed vendor email, all without leaving the page.",
    ]:
        story.append(Paragraph(f"• {bullet}", s["bullet"]))

    story.append(Paragraph("10.2  System Architecture Decisions", s["h2"]))
    for item in [
        ("<b>Deterministic over Probabilistic:</b>",
         "Financial approval decisions are never delegated to a statistical model. Every rule emits an auditable structured result. This is not a constraint — it is the correct architectural choice for money-movement automation."),
        ("<b>Offline-First Design:</b>",
         "The 40-bank registry, all tax ID validators, all postal code patterns, and all entity normalization logic run entirely in-process with no network calls. The system works in air-gapped, sandboxed, or latency-sensitive environments."),
        ("<b>SQLite for Prototyping, Clean Migration Path:</b>",
         "SQLite persistence handles the prototype's ephemeral Streamlit Cloud filesystem with auto-seed on cold start. The schema is clean and production-ready for direct migration to PostgreSQL or Supabase with no logic changes."),
        ("<b>Effect-Tag Schema:</b>",
         "Every check carries an 'effect' field (none / fix / review / block). The decision engine reads effects, not raw pass/fail, enabling precise aggregation into decision + risk score + email mode without duplicating business logic."),
    ]:
        story.append(Paragraph(item[0], s["h3"]))
        story.append(Paragraph(item[1], s["body"]))

    story.append(Paragraph("10.3  Intellectual Honesty — Current Boundaries", s["h2"]))
    story.append(Paragraph(
        "The following limitations are deliberate and acknowledged as part of a production-honest evaluation:",
        s["body"]
    ))
    prod_data = [
        [Paragraph("Current Prototype", s["th"]), Paragraph("Production Extension", s["th"])],
        [Paragraph("Tax IDs verified by checksum and prefix — not live government registry lookup.", s["tc"]),
         Paragraph("Connect to GSTN (India), IRS TIN Matching (US), EU VIES, and ACRA (Singapore) for real-time entity existence verification.", s["tc"])],
        [Paragraph("Bank account ownership resolved via entity name matching — not penny-drop.", s["tc"]),
         Paragraph("Integrate real-time penny-drop APIs (RazorpayX, Cashfree for India) or UK/EU Confirmation of Payee for account ownership verification.", s["tc"])],
        [Paragraph("Documents validated by checklist presence — not content extraction.", s["tc"]),
         Paragraph("Apply multimodal OCR to extract values from uploaded tax certificates, incorporation documents, and bank letters, then cross-verify against submitted form fields.", s["tc"])],
        [Paragraph("SQLite on ephemeral Streamlit Cloud filesystem.", s["tc"]),
         Paragraph("PostgreSQL or Supabase with structured vendor-review queue, SLA timers, and human-review assignment workflows.", s["tc"])],
    ]
    story.append(tbl(prod_data, [235, 269], BD))

    story.append(Spacer(1, 10))
    story.append(callout_box(
        "<b>Conclusion.</b> This project delivers a production-grade vendor onboarding intelligence engine "
        "with real mathematical fraud-detection algorithms, an offline financial institution registry covering "
        "five major payment corridors, enterprise-grade BEC defense with correct email routing, differential "
        "resubmission tracking, a composite risk scoring framework, and a fully guardrailed Gemini 3.5 Flash-Lite "
        "communication pipeline — all operational live at <b>https://jayaprakashzamp.streamlit.app/</b>.",
        s
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Report compiled: {filename}")


if __name__ == "__main__":
    build_pdf()
