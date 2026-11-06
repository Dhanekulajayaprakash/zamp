"""Synthetic vendor master, watchlist and test submissions (all fictional)."""
from __future__ import annotations

from validators import make_gstin, make_iban

# ---------------- existing vendor master (the "procurement system") ----------------
ORION_OLD_IBAN = "DE89370400440532013000"
ORION_NEW_IBAN = make_iban("DE", "500105175407324931")

REGISTRY = [
    {"id": "V-1042", "name": "Orion Industrial Supplies GmbH", "country": "DE", "tax_id": "DE811234567",
     "account_number": ORION_OLD_IBAN, "contact_name": "Katrin Vogel",
     "contact_email": "procurement@orion-industrial.de", "onboarded": "2025-03-14"},
    {"id": "V-1010", "name": "Kestrel Packaging Ltd", "country": "GB", "tax_id": "GB284917365",
     "account_number": "12345678", "contact_name": "Tom Hardy",
     "contact_email": "accounts@kestrelpackaging.co.uk", "onboarded": "2024-11-02"},
    {"id": "V-1077", "name": "Harbor Freight Logistics Inc", "country": "US", "tax_id": "52-1827364",
     "account_number": "7788990011", "contact_name": "Lena Ortiz",
     "contact_email": "ar@harborfreightlogistics.com", "onboarded": "2025-07-21"},
]

# Internal watchlist: known-fraud accounts, sanctioned / debarred entities.
WATCHLIST = [
    {"type": "account", "value": "0721983456", "reason": "Account linked to a previously confirmed payment-fraud case (case FR-2025-118)"},
    {"type": "tax_id", "value": "99-9999999", "reason": "Debarred supplier"},
    {"type": "name", "value": "northbridge holdings", "reason": "Entity on internal debarment list"},
]

# ---------------- test submissions ----------------
ALL_DOCS = ["tax_certificate", "incorporation_cert", "bank_proof"]

SCENARIOS = [
    {
        "key": "happy", "kind": "Happy path",
        "label": "Happy path - clean Indian vendor",
        "description": "Everything is present, valid and consistent. Expect APPROVED with no flags.",
        "submission": {
            "legal_name": "Apex Cloud Solutions Pvt Ltd", "country": "IN",
            "tax_id": make_gstin("36", "ABCCA1234F"),
            "address": "Plot 14, HITEC City, Hyderabad, Telangana 500081",
            "contact_name": "Ravi Menon", "contact_email": "ravi.menon@apexcloud.in",
            "bank_country": "IN", "bank_name": "HDFC Bank, HITEC City",
            "account_holder": "Apex Cloud Solutions Pvt. Ltd.", "account_number": "50200012345678",
            "bank_code": "HDFC0001234", "documents": ALL_DOCS,
        },
    },
    {
        "key": "name_suffix", "kind": "Edge 1a",
        "label": "Edge 1a - Name differs only by legal suffix",
        "description": "'Private Limited' vs 'PVT LTD' and different casing. A naive string compare would flag it; a good one should not.",
        "submission": {
            "legal_name": "Green Valley Foods Private Limited", "country": "IN",
            "tax_id": make_gstin("27", "AAGCG5678K"),
            "address": "Survey 88, Baner Road, Pune, Maharashtra 411045",
            "contact_name": "Sunita Rao", "contact_email": "accounts@greenvalleyfoods.in",
            "bank_country": "IN", "bank_name": "ICICI Bank, Baner",
            "account_holder": "GREEN VALLEY FOODS PVT LTD", "account_number": "123456789012",
            "bank_code": "ICIC0002345", "documents": ALL_DOCS,
        },
    },
    {
        "key": "name_mismatch", "kind": "Edge 1b",
        "label": "Edge 1b - Bank account belongs to a different company",
        "description": "Everything validates, but the payee on the bank account is a different business. Classic third-party / mule account pattern.",
        "submission": {
            "legal_name": "Brightpath Consulting LLC", "country": "US", "tax_id": "84-3920417",
            "address": "1200 Market St, Suite 400, Wilmington, DE 19801",
            "contact_name": "Dana Whitfield", "contact_email": "dana@brightpathconsulting.com",
            "bank_country": "US", "bank_name": "JPMorgan Chase",
            "account_holder": "Sunrise Trading Co", "account_number": "483920175531",
            "bank_code": "021000021", "documents": ALL_DOCS,
        },
    },
    {
        "key": "country_mismatch", "kind": "Edge 2",
        "label": "Edge 2 - Tax ID is valid, but for a different country",
        "description": "Vendor claims to be a UK company, but the tax ID is a valid Indian GSTIN and the bank is in India.",
        "submission": {
            "legal_name": "Sterling Bridge Consulting Ltd", "country": "GB",
            "tax_id": make_gstin("29", "BSTCS4321M"),
            "address": "27 Old Gloucester Street, London WC1N 3AX",
            "contact_name": "James Hale", "contact_email": "james.hale@sterlingbridge.co.uk",
            "bank_country": "IN", "bank_name": "Axis Bank, Bengaluru",
            "account_holder": "Sterling Bridge Consulting Ltd", "account_number": "917020045671234",
            "bank_code": "UTIB0000789", "documents": ALL_DOCS,
        },
    },
    {
        "key": "bank_change", "kind": "Edge 3",
        "label": "Edge 3 - Existing vendor 'changes' bank details",
        "description": "Same VAT ID and legal name as active vendor V-1042, but a new IBAN and a look-alike email domain. Looks like business-email-compromise fraud.",
        "submission": {
            "legal_name": "Orion Industrial Supplies GmbH", "country": "DE", "tax_id": "DE811234567",
            "address": "Hafenstrasse 22, 20457 Hamburg",
            "contact_name": "Klaus Brandt", "contact_email": "k.brandt@orion-industrial.co",
            "bank_country": "DE", "bank_name": "ING Germany",
            "account_holder": "Orion Industrial Supplies GmbH", "account_number": ORION_NEW_IBAN,
            "bank_code": "INGDDEFFXXX", "documents": ALL_DOCS,
        },
    },
    {
        "key": "first_attempt", "kind": "Edge 4a",
        "label": "Edge 4a - Incomplete first attempt",
        "description": "Missing contact email and bank proof, and the EIN has an invalid prefix. Expect PENDING with a clear vendor request.",
        "submission": {
            "legal_name": "Nimbus Data Labs Inc", "country": "US", "tax_id": "07-1234567",
            "address": "500 Howard St, San Francisco, CA 94105",
            "contact_name": "Priya Nair", "contact_email": "",
            "bank_country": "US", "bank_name": "Bank of America",
            "account_holder": "Nimbus Data Labs, Inc.", "account_number": "3250198764",
            "bank_code": "026009593", "documents": ["tax_certificate", "incorporation_cert"],
        },
    },
    {
        "key": "resubmission", "kind": "Edge 4b",
        "label": "Edge 4b - Partial resubmission",
        "description": "Vendor fixes the email and uploads the bank proof but re-enters the same bad EIN. The process should say what was resolved and what is still open.",
        "previous_scenario": "first_attempt",
        "submission": {
            "legal_name": "Nimbus Data Labs Inc", "country": "US", "tax_id": "07-1234567",
            "address": "500 Howard St, San Francisco, CA 94105",
            "contact_name": "Priya Nair", "contact_email": "priya@nimbusdatalabs.io",
            "bank_country": "US", "bank_name": "Bank of America",
            "account_holder": "Nimbus Data Labs, Inc.", "account_number": "3250198764",
            "bank_code": "026009593", "documents": ALL_DOCS,
        },
    },
    {
        "key": "watchlist", "kind": "Bonus",
        "label": "Bonus - Bank account on internal fraud watchlist",
        "description": "Otherwise perfect submission whose account number matches a known-fraud case. Hard REJECT, and the vendor email must not reveal why.",
        "submission": {
            "legal_name": "Quickpay Global Traders Pte Ltd", "country": "SG", "tax_id": "201912345K",
            "address": "10 Anson Road #20-05, Singapore 079903",
            "contact_name": "Li Wei", "contact_email": "liwei@quickpayglobal.sg",
            "bank_country": "SG", "bank_name": "DBS Bank",
            "account_holder": "Quickpay Global Traders Pte Ltd", "account_number": "0721983456",
            "bank_code": "DBSSSGSG", "documents": ALL_DOCS,
        },
    },
    {
        "key": "duplicate", "kind": "Bonus",
        "label": "Bonus - Duplicate of an active vendor",
        "description": "Exact re-submission of vendor V-1010 that is already onboarded.",
        "submission": {
            "legal_name": "Kestrel Packaging Ltd", "country": "GB", "tax_id": "GB284917365",
            "address": "Unit 4, Severn Trading Estate, Bristol BS11 0YA",
            "contact_name": "Tom Hardy", "contact_email": "accounts@kestrelpackaging.co.uk",
            "bank_country": "GB", "bank_name": "Barclays",
            "account_holder": "Kestrel Packaging Ltd", "account_number": "12345678",
            "bank_code": "20-45-45", "documents": ALL_DOCS,
        },
    },
]

SCENARIOS_BY_KEY = {s["key"]: s for s in SCENARIOS}
DOC_LABELS = {
    "tax_certificate": "Tax registration certificate",
    "incorporation_cert": "Certificate of incorporation / business registration",
    "bank_proof": "Bank proof (cancelled cheque or bank letter)",
}
