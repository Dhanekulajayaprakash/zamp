"""Generates a professional executive PDF report for Zamp Vendor Onboarding Case Study."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Adds running headers and footers with Page X of Y."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        if self._pageNumber > 1:
            self.drawString(54, 750, "ZAMP AP — AUTONOMOUS VENDOR ONBOARDING INTELLIGENCE REPORT")
            self.drawRightString(612 - 54, 750, "PROBLEM STATEMENT 2")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 612 - 54, 742)

        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 612 - 54, 45)

        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Confidential — For Evaluation Purposes Only | Author: Jayaprakash Dhanekula")
        self.drawRightString(612 - 54, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def _styled_table(data, col_widths, border_color, header_bg="#f1f5f9", valign="TOP"):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
        ("BOX", (0, 0), (-1, -1), 0.6, border_color),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
        ("VALIGN", (0, 0), (-1, -1), valign),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def build_pdf(filename="Zamp_Vendor_Onboarding_Evaluation_Report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    c_primary = colors.HexColor("#ea580c")
    c_dark = colors.HexColor("#0f172a")
    c_sub = colors.HexColor("#475569")
    c_border = colors.HexColor("#cbd5e1")

    style_title = ParagraphStyle(
        "DocTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=19, leading=23, textColor=c_primary, spaceAfter=4
    )
    style_subtitle = ParagraphStyle(
        "DocSubtitle", parent=styles["Normal"], fontName="Helvetica",
        fontSize=10.5, leading=14, textColor=c_sub, spaceAfter=10
    )
    style_h1 = ParagraphStyle(
        "SectionH1", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=12.5, leading=16, textColor=c_dark, spaceBefore=12, spaceAfter=5, keepWithNext=True
    )
    style_h2 = ParagraphStyle(
        "SectionH2", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=10, leading=13.5, textColor=c_primary, spaceBefore=7, spaceAfter=3, keepWithNext=True
    )
    style_body = ParagraphStyle(
        "BodyDark", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9, leading=13.5, textColor=colors.HexColor("#1e293b"), spaceAfter=5
    )
    style_callout = ParagraphStyle(
        "CalloutText", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9, leading=13.5, textColor=c_dark
    )
    style_th = ParagraphStyle(
        "TableHead", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=8.3, leading=11, textColor=c_dark
    )
    style_tc = ParagraphStyle(
        "TableCell", parent=styles["Normal"], fontName="Helvetica",
        fontSize=8, leading=11, textColor=colors.HexColor("#1e293b")
    )

    story = []

    # Header
    story.append(Paragraph("Zamp AP — Autonomous Vendor Onboarding Intelligence", style_title))
    story.append(Paragraph(
        "System Architecture, Risk Engineering &amp; Verification Capabilities Report (Problem Statement 2)",
        style_subtitle
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=0, spaceAfter=10))

    # Core Principle Box
    principle_text = (
        "<b>Core Architectural Principle: Rules Decide, the LLM Only Communicates.</b><br/>"
        "In enterprise Accounts Payable, automated money movement and vendor enablement demand 100% deterministic, "
        "auditable, and reproducible decisions. This engine executes 6 automated validation stages plus a weighted "
        "decision &amp; risk-scoring gate using mathematical checksums, semantic entity normalization, and BEC fraud "
        "heuristics. An LLM (Gemini 3.5 Flash-Lite) is never allowed to decide approval or rejection; it operates strictly "
        "behind safety guardrails solely to compose polite vendor correspondence."
    )
    t_callout = Table([[Paragraph(principle_text, style_callout)]], colWidths=[504])
    t_callout.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff7ed")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#fdba74")),
        ("LINEBEFORE", (0, 0), (0, -1), 4, c_primary),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_callout)
    story.append(Spacer(1, 8))

    # 1. Executive Strengths Highlights
    story.append(Paragraph("1. Key Project Strengths at a Glance", style_h1))
    strengths_data = [
        [Paragraph("Capability Pillar", style_th), Paragraph("Why It Stands Out", style_th)],
        [
            Paragraph("<b>Deterministic Decisioning</b>", style_tc),
            Paragraph("Every rule emits a structured effect tag (<i>none / fix / review / block</i>). Decisions are 100% explainable, fast (~30 ms pipeline latency), and immune to LLM hallucinations.", style_tc)
        ],
        [
            Paragraph("<b>True Mathematical Checksums</b>", style_tc),
            Paragraph("Validates Indian GSTIN (Mod-36 + 38 states + PAN), US ABA routing (FedWire Mod-10), and EU/UK/DE IBANs (ISO 7064 Mod-97) rather than superficial regex pattern checks.", style_tc)
        ],
        [
            Paragraph("<b>Offline 40-Bank Directory</b>", style_tc),
            Paragraph("Maps 40 IFSC, ABA, and SWIFT/BIC prefixes to official bank names without external API failure risk, catching mismatched bank names vs. routing codes automatically.", style_tc)
        ],
        [
            Paragraph("<b>Smart Entity Normalization</b>", style_tc),
            Paragraph("Strips 24 global corporate suffixes (<i>Pvt Ltd, LLC, GmbH, Inc, Sarl</i>) and runs dual SequenceMatcher similarity so valid suffix variants pass while third-party mule accounts are stopped.", style_tc)
        ],
        [
            Paragraph("<b>BEC &amp; Account-Takeover Defense</b>", style_tc),
            Paragraph("Detects bank-detail changes and look-alike domains on active ERP vendors, mandates out-of-band phone callback, and routes confirmation emails strictly to the <b>contact ON FILE</b>—never the submitter.", style_tc)
        ],
        [
            Paragraph("<b>Differential Resubmission Diffing</b>", style_tc),
            Paragraph("Tracks SQLite run history per legal entity and computes exact deltas across attempts: <i>Resolved</i>, <i>Still Open</i>, and <i>New Anomalies</i>.", style_tc)
        ],
        [
            Paragraph("<b>0–100 Composite Risk Score</b>", style_tc),
            Paragraph("Aggregates severity and fraud signals into Low / Medium / High / Critical risk bands with a visual progress gauge for instant ops triage.", style_tc)
        ],
        [
            Paragraph("<b>Guardrailed LLM + Fallback</b>", style_tc),
            Paragraph("Uses Gemini 3.5 Flash-Lite (with multi-model fallback) behind 9 forbidden-term filters, account-number redaction, and deterministic template fallback so onboarding never halts.", style_tc)
        ],
        [
            Paragraph("<b>Zero-Setup Executive Dashboard</b>", style_tc),
            Paragraph("Auto-seeds all 9 benchmark runs on first launch with live KPIs, top failure charts, status/vendor filtering, and one-click Deep Inspection replay.", style_tc)
        ],
    ]
    story.append(_styled_table(strengths_data, [145, 359], c_border))
    story.append(Spacer(1, 8))

    # 2. 7-Stage Pipeline
    story.append(Paragraph("2. Multi-Stage Verification Architecture", style_h1))
    stages_data = [
        [Paragraph("Stage", style_th), Paragraph("Verification Focus", style_th), Paragraph("Core Logic &amp; Cross-Checks", style_th), Paragraph("Decision Effect", style_th)],
        [
            Paragraph("<b>1. Intake</b>", style_tc),
            Paragraph("Mandatory fields &amp; 3 compliance docs", style_tc),
            Paragraph("Validates company/banking inputs, dynamic jurisdiction-aware bank code requirement (IN/US/GB), RFC-style email format, and 3 required documents.", style_tc),
            Paragraph("Missing &rarr; <b>PENDING (Fix)</b>", style_tc)
        ],
        [
            Paragraph("<b>2. Tax ID</b>", style_tc),
            Paragraph("Checksums &amp; jurisdiction extraction", style_tc),
            Paragraph("Runs GSTIN Mod-36 checksum (plus state name &amp; PAN extraction), IRS EIN prefix validation, and UK/DE VAT + SG UEN verification. Detects valid foreign tax IDs.", style_tc),
            Paragraph("Bad check &rarr; <b>Fix</b><br/>Foreign ID &rarr; <b>Stage 5</b>", style_tc)
        ],
        [
            Paragraph("<b>3. Bank Detail</b>", style_tc),
            Paragraph("Routing math &amp; semantic bank lookup", style_tc),
            Paragraph("Executes IFSC/ABA Mod-10/IBAN Mod-97 checks, resolves bank code via 40-institution offline directory, and checks &ge;60% similarity with declared bank name.", style_tc),
            Paragraph("Bad format &rarr; <b>Fix</b><br/>Name clash &rarr; <b>Review</b>", style_tc)
        ],
        [
            Paragraph("<b>4. Payee Match</b>", style_tc),
            Paragraph("Entity resolution &amp; mule detection", style_tc),
            Paragraph("Prunes 24 legal suffixes, normalizes punctuation, and compares sorted &amp; linear token similarity (&ge;90% pass, 70–89% partial review, &lt;70% mule alert).", style_tc),
            Paragraph("&ge;90% &rarr; <b>PASS</b><br/>&lt;90% &rarr; <b>Review</b>", style_tc)
        ],
        [
            Paragraph("<b>5. Cross-Field</b>", style_tc),
            Paragraph("Multi-attribute consistency", style_tc),
            Paragraph("Matches Tax ID country vs. vendor country, flags offshore bank countries, verifies country postal codes (PIN/ZIP/PLZ/postcode), and checks domain-name alignment.", style_tc),
            Paragraph("Country clash &rarr; <b>Review</b><br/>Free-mail &rarr; <b>Advisory</b>", style_tc)
        ],
        [
            Paragraph("<b>6. Registry</b>", style_tc),
            Paragraph("Watchlist, duplicates &amp; BEC", style_tc),
            Paragraph("Screens internal fraud/debarment watchlist (account, tax ID, normalized name), detects duplicate active vendors, and flags bank changes or look-alike domains.", style_tc),
            Paragraph("Watchlist/Dup &rarr; <b>REJECT</b><br/>Bank change &rarr; <b>Review</b>", style_tc)
        ],
        [
            Paragraph("<b>7. Decision</b>", style_tc),
            Paragraph("Risk scoring &amp; dispatch", style_tc),
            Paragraph("Aggregates block/review/fix signals into APPROVED, PENDING, or REJECTED, computes 0–100 risk score, runs resubmission diffing, and dispatches email.", style_tc),
            Paragraph("ERP Enable, Hold, or Stop", style_tc)
        ],
    ]
    story.append(_styled_table(stages_data, [68, 102, 232, 102], c_border))
    story.append(PageBreak())

    # 3. Deep Technical Strengths
    story.append(Paragraph("3. Mathematical Checksums &amp; Offline Banking Intelligence", style_h1))
    story.append(Paragraph(
        "Simple regular expressions only check character shape, allowing transposed digits to enter Accounts Payable. "
        "This engine validates true check digits across major payment corridors:",
        style_body
    ))
    story.append(Paragraph("<b>• Indian GSTIN (Luhn-Variant Mod-36 + State &amp; PAN Extraction):</b>", style_h2))
    story.append(Paragraph(
        "Applies alternating weights (1, 2) in base-36 across the first 14 characters to verify the 15th check digit, "
        "validates against all 38 official Indian GST state codes (e.g., 36 &rarr; Telangana, 27 &rarr; Maharashtra), and "
        "isolates the embedded 10-character PAN.",
        style_body
    ))
    story.append(Paragraph("<b>• US FedWire ABA Routing (Weighted Mod-10) &amp; European IBAN (ISO 7064 Mod-97):</b>", style_h2))
    story.append(Paragraph(
        "Verifies 9-digit US routing numbers via (3·d1 + 7·d2 + 1·d3 + ... + 1·d9) mod 10 = 0, and transforms EU/UK/DE "
        "IBANs into integer streams enforcing (N mod 97 = 1).",
        style_body
    ))
    story.append(Paragraph("<b>• Offline 40-Institution Bank Registry &amp; Semantic Mismatch Detection:</b>", style_h2))
    story.append(Paragraph(
        "Embeds 40 verified prefixes (20 Indian IFSC codes such as SBIN, HDFC, ICIC, UTIB; 10 US ABA prefixes such as 0210 JPMorgan Chase, "
        "0260 Bank of America; and 10 SWIFT/BIC codes across SG, DE, GB). Even if a vendor enters a valid checksum, declaring "
        "'HDFC Bank' alongside an 'SBIN...' IFSC triggers an immediate semantic bank-name review flag—with zero third-party API dependency.",
        style_body
    ))

    # 4. BEC Defense & Guardrailed LLM
    story.append(Paragraph("4. Business Email Compromise (BEC) Defense &amp; LLM Guardrails", style_h1))
    story.append(Paragraph(
        "Invoice and bank-change redirection is one of the costliest AP attack vectors. When an active vendor's Tax ID matches "
        "the master registry but presents a new bank account (such as <b>Orion Industrial Supplies GmbH</b> submitting a new IBAN "
        "from look-alike domain <i>orion-industrial.co</i> instead of <i>orion-industrial.de</i>):",
        style_body
    ))
    story.append(Paragraph(
        "1. <b>Pending Hold Instead of Hard Reject:</b> Avoids blocking legitimate treasury switches while freezing automated payouts.<br/>"
        "2. <b>Safe Target Routing:</b> Confirmation emails are routed strictly to the <b>verified email ON FILE</b> (<i>procurement@orion-industrial.de</i>), "
        "never the incoming submitter, preventing an attacker with a spoofed or compromised mailbox from confirming the redirect.<br/>"
        "3. <b>Zero-Leak Watchlist Declines:</b> Debarred or fraud-linked submissions receive a neutral decline without revealing detection logic.<br/>"
        "4. <b>Sanitized LLM Dispatch (Gemini 3.5 Flash-Lite):</b> The LLM receives only vendor-safe facts (never internal fraud flags or watchlist notes), "
        "passes output through 9 forbidden-keyword checks (<i>watchlist, blocklist, fraud, suspicious, sanction, debar, mule, risk score, compromise</i>) "
        "plus account-number leakage checks, and falls back across <i>gemini-3.8-flash</i> / <i>gemini-2.5-flash-lite</i> or deterministic templates on any failure.",
        style_body
    ))

    # 5. Composite Risk Scoring & Live Benchmark Results
    story.append(Paragraph("5. Composite Risk Scoring &amp; Verified Scenario Benchmarks", style_h1))
    story.append(Paragraph(
        "The engine synthesizes every check into a bounded 0–100 Composite Risk Score (<b>0–20 Low</b>, <b>21–45 Medium</b>, "
        "<b>46–70 High</b>, <b>71–100 Critical</b>): base severity adds +40 for <i>block</i>, +20 for <i>review</i>, and +10 for <i>fix</i>, "
        "layered with fraud-specific multipliers (+50 watchlist, +25 bank change, +20 look-alike contact domain, +15 offshore bank country, +5 free mailbox).",
        style_body
    ))

    bench_data = [
        [Paragraph("Scenario", style_th), Paragraph("Decision", style_th), Paragraph("Checks", style_th), Paragraph("Risk Score", style_th), Paragraph("Key Judgment Demonstrated", style_th)],
        [Paragraph("<b>Happy Path</b> (Apex Cloud, IN)", style_tc), Paragraph("APPROVED", style_tc), Paragraph("15/15", style_tc), Paragraph("0 / Low", style_tc), Paragraph("GSTIN Mod-36 + state 36, IFSC &rarr; HDFC match, PIN &amp; domain verified.", style_tc)],
        [Paragraph("<b>Edge 1a</b> (Green Valley, IN)", style_tc), Paragraph("APPROVED", style_tc), Paragraph("15/15", style_tc), Paragraph("0 / Low", style_tc), Paragraph("Normalizes 'Private Limited' vs 'PVT LTD' without false friction.", style_tc)],
        [Paragraph("<b>Edge 1b</b> (Brightpath, US)", style_tc), Paragraph("PENDING", style_tc), Paragraph("13/14", style_tc), Paragraph("20 / Low", style_tc), Paragraph("Valid ABA 0210 (Chase), catches third-party payee 'Sunrise Trading Co'.", style_tc)],
        [Paragraph("<b>Edge 2</b> (Sterling Bridge, GB)", style_tc), Paragraph("PENDING", style_tc), Paragraph("11/14", style_tc), Paragraph("55 / High", style_tc), Paragraph("Detects Indian GSTIN &amp; Axis Bank on a claimed UK incorporation.", style_tc)],
        [Paragraph("<b>Edge 3</b> (Orion Supplies, DE)", style_tc), Paragraph("PENDING", style_tc), Paragraph("13/15", style_tc), Paragraph("85 / Critical", style_tc), Paragraph("BEC bank change + .co look-alike domain; email routed to contact ON FILE.", style_tc)],
        [Paragraph("<b>Edge 4a</b> (Nimbus Labs, US)", style_tc), Paragraph("PENDING", style_tc), Paragraph("8/11", style_tc), Paragraph("30 / Medium", style_tc), Paragraph("Missing email, missing bank proof, invalid IRS EIN prefix '07'.", style_tc)],
        [Paragraph("<b>Edge 4b</b> (Nimbus Resubmit)", style_tc), Paragraph("PENDING", style_tc), Paragraph("12/13", style_tc), Paragraph("10 / Low", style_tc), Paragraph("Delta engine isolates 2 Resolved items vs 1 Still Open bad EIN.", style_tc)],
        [Paragraph("<b>Bonus</b> (Quickpay, SG)", style_tc), Paragraph("REJECTED", style_tc), Paragraph("12/14", style_tc), Paragraph("100 / Critical", style_tc), Paragraph("Hard-stops fraud-linked account 0721983456; neutral zero-leak email.", style_tc)],
        [Paragraph("<b>Bonus</b> (Kestrel, GB)", style_tc), Paragraph("REJECTED", style_tc), Paragraph("11/12", style_tc), Paragraph("40 / Medium", style_tc), Paragraph("Prevents duplicate ERP record creation for active vendor V-1010.", style_tc)],
    ]
    story.append(_styled_table(bench_data, [118, 60, 44, 62, 220], c_border, valign="MIDDLE"))
    story.append(Spacer(1, 8))

    # 6. Honest Boundaries & Production Roadmap
    story.append(Paragraph("6. Scope Boundaries &amp; Enterprise Production Roadmap", style_h1))
    story.append(Paragraph(
        "The prototype intentionally maintains clear engineering boundaries while keeping integration seams clean for production:<br/>"
        "• <b>Live Tax &amp; Entity Registries:</b> Mathematical checksums and prefix tables serve as fast local gates; production connects directly to GSTN (India), IRS TIN Matching (US), EU VIES, and ACRA (Singapore).<br/>"
        "• <b>Account Ownership Verification:</b> Algorithmic entity resolution pairs cleanly with real-time penny-drop APIs (RazorpayX / Cashfree) and UK/EU Confirmation of Payee.<br/>"
        "• <b>Document OCR &amp; Persistence:</b> Uploaded document checklists upgrade directly to multimodal OCR extraction against form fields, backed by PostgreSQL + analyst SLA queues in place of ephemeral SQLite.",
        style_body
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Report successfully compiled to {filename}")


if __name__ == "__main__":
    build_pdf()
