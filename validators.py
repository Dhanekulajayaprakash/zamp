"""Pure validation helpers: tax IDs, bank details, IBAN/ABA/GSTIN checksums, address patterns.

Everything here is deterministic - no AI involved. Money-moving decisions should
rest on rules you can audit; the LLM is only used later to draft the vendor email.
"""
from __future__ import annotations

import re

GSTIN_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

COUNTRY_NAMES = {
    "IN": "India", "US": "United States", "GB": "United Kingdom", "DE": "Germany",
    "SG": "Singapore", "AE": "United Arab Emirates", "FR": "France", "BR": "Brazil",
}

# --------- Bank directory: maps code prefixes → real bank names ----------
BANK_DIRECTORY: dict[str, str] = {
    # Indian IFSC prefixes (first 4 chars)
    "SBIN": "State Bank of India", "HDFC": "HDFC Bank", "ICIC": "ICICI Bank",
    "UTIB": "Axis Bank", "PUNB": "Punjab National Bank", "BARB": "Bank of Baroda",
    "CNRB": "Canara Bank", "UBIN": "Union Bank of India", "IOBA": "Indian Overseas Bank",
    "IDIB": "Indian Bank", "BKID": "Bank of India", "KKBK": "Kotak Mahindra Bank",
    "YESB": "Yes Bank", "INDB": "IndusInd Bank", "FDRL": "Federal Bank",
    "SIBL": "South Indian Bank", "KARB": "Karnataka Bank", "CBIN": "Central Bank of India",
    "ALLA": "Allahabad Bank", "MAHB": "Bank of Maharashtra",
    # US ABA routing prefixes (first 4 digits)
    "0210": "JPMorgan Chase", "0260": "Bank of America", "0710": "Wells Fargo",
    "1210": "Wells Fargo", "0740": "PNC Bank", "0440": "HSBC",
    "0312": "TD Bank", "0360": "KeyBank", "0611": "US Bank", "0531": "Truist Bank",
    # SWIFT/BIC codes (Singapore)
    "DBSSSGSG": "DBS Bank (Singapore)", "OCBCSGSG": "OCBC Bank (Singapore)",
    "UOVBSGSG": "UOB (Singapore)",
    # SWIFT/BIC codes (Germany)
    "INGDDEFF": "ING Bank (Germany)", "COBADEFF": "Commerzbank (Germany)",
    "DEUTDEFF": "Deutsche Bank (Germany)",
    # SWIFT/BIC codes (UK)
    "BARCGB22": "Barclays (UK)", "NWBKGB2L": "NatWest (UK)",
    "LOYDGB2L": "Lloyds (UK)", "HSBCGB2L": "HSBC (UK)",
}

# --------- Postal / ZIP code patterns by country ----------
POSTAL_PATTERNS = {
    "IN": (r"\d{6}", "6-digit PIN code"),
    "US": (r"\d{5}(-\d{4})?", "5-digit ZIP (or ZIP+4)"),
    "GB": (r"[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}", "UK postcode"),
    "DE": (r"\d{5}", "5-digit PLZ"),
    "SG": (r"\d{6}", "6-digit postal code"),
    "FR": (r"\d{5}", "5-digit code postal"),
    "BR": (r"\d{5}-?\d{3}", "8-digit CEP"),
}

# --------- Indian state codes in GSTIN ----------
GSTIN_STATES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
    "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan",
    "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram", "16": "Tripura",
    "17": "Meghalaya", "18": "Assam", "19": "West Bengal", "20": "Jharkhand",
    "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "26": "Dadra & Nagar Haveli", "27": "Maharashtra", "29": "Karnataka",
    "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
    "34": "Puducherry", "35": "Andaman & Nicobar", "36": "Telangana",
    "37": "Andhra Pradesh", "38": "Ladakh",
}


def lookup_bank_name(country: str, bank_code: str) -> tuple[bool, str | None]:
    """Resolve a bank name from bank_code using BANK_DIRECTORY."""
    if not bank_code:
        return False, None
    code = bank_code.strip().upper()
    if country in ("IN", "US"):
        prefix = code[:4]
        name = BANK_DIRECTORY.get(prefix)
        return (True, name) if name else (False, None)
    # For other countries try full code, then without trailing "XXX"
    name = BANK_DIRECTORY.get(code)
    if name:
        return True, name
    if len(code) > 3 and code.endswith("XXX"):
        name = BANK_DIRECTORY.get(code[:-3])
        if name:
            return True, name
    return False, None


def validate_address(country: str, address: str) -> tuple[bool, str]:
    """Check if address contains a postal/ZIP code matching the country pattern."""
    if not address:
        return False, "Address is empty"
    if country in POSTAL_PATTERNS:
        pattern, label = POSTAL_PATTERNS[country]
        if re.search(pattern, address.upper() if country == "GB" else address):
            return True, f"Contains a valid {label}"
        return False, f"No {label} found in the address"
    return True, "No postal code pattern check available for this country"


def extract_gstin_state(gstin: str) -> str | None:
    """Extract state name from a valid GSTIN."""
    if len(gstin) >= 2:
        return GSTIN_STATES.get(gstin[:2])
    return None


def validate_email_domain(email: str, legal_name: str) -> tuple[str, str]:
    """Check if email domain looks consistent with company name."""
    if "@" not in email:
        return "skip", ""
    domain_part = email.split("@")[-1].lower()
    # Extract company keywords (ignore short words)
    name_words = set(w.lower() for w in re.findall(r"[a-zA-Z]+", legal_name) if len(w) > 3)
    domain_base = domain_part.split(".")[0]
    # Check if any significant company word appears in domain
    matches = [w for w in name_words if w in domain_base]
    if matches:
        return "match", f"Email domain '{domain_part}' contains company keyword(s): {', '.join(matches)}"
    return "no_match", f"Email domain '{domain_part}' does not contain any keywords from '{legal_name}'"


# ---------- checksums ----------
def gstin_checksum_char(first14: str) -> str:
    total = 0
    for i, ch in enumerate(first14):
        v = GSTIN_CHARS.index(ch)
        prod = v * (1 if i % 2 == 0 else 2)
        total += prod // 36 + prod % 36
    return GSTIN_CHARS[(36 - total % 36) % 36]


def make_gstin(state: str, pan: str, entity: str = "1") -> str:
    body = f"{state}{pan}{entity}Z"
    return body + gstin_checksum_char(body)


def _iban_digits(s: str) -> int:
    return int("".join(str(int(c, 36)) for c in s))


def iban_ok(iban: str) -> bool:
    s = iban.replace(" ", "").upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", s):
        return False
    return _iban_digits(s[4:] + s[:4]) % 97 == 1


def make_iban(cc: str, bban: str) -> str:
    check = 98 - _iban_digits(bban + cc + "00") % 97
    return f"{cc}{check:02d}{bban}"


def aba_ok(routing: str) -> bool:
    if not re.fullmatch(r"\d{9}", routing):
        return False
    w = [3, 7, 1] * 3
    return sum(int(d) * k for d, k in zip(routing, w)) % 10 == 0


# ---------- tax IDs ----------
_EIN_VALID_PREFIX = (
    set(range(1, 7)) | set(range(10, 17)) | set(range(20, 28)) | set(range(30, 49))
    | set(range(50, 69)) | set(range(71, 78)) | set(range(80, 89)) | set(range(90, 96)) | {98, 99}
)


def tax_in(t: str):
    if not re.fullmatch(r"\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]", t):
        return False, "expected a 15-character GSTIN (state code + PAN + entity digit + 'Z' + check character)"
    if not 1 <= int(t[:2]) <= 38:
        return False, f"state code {t[:2]} does not exist"
    if gstin_checksum_char(t[:14]) != t[14]:
        return False, "check character is wrong - most likely a typo in the number"
    return True, "valid GSTIN structure and checksum"


def tax_us(t: str):
    if not re.fullmatch(r"\d{2}-\d{7}", t):
        return False, "expected an EIN in the form NN-NNNNNNN"
    if int(t[:2]) not in _EIN_VALID_PREFIX:
        return False, f"prefix {t[:2]} is not an IRS-issued EIN prefix"
    return True, "valid EIN format and prefix"


def tax_gb(t: str):
    if not re.fullmatch(r"GB(\d{9}|\d{12}|GD\d{3}|HA\d{3})", t):
        return False, "expected a UK VAT number: 'GB' followed by 9 or 12 digits"
    return True, "valid UK VAT number format"


def tax_de(t: str):
    if not re.fullmatch(r"DE\d{9}", t):
        return False, "expected a German VAT ID: 'DE' followed by 9 digits"
    return True, "valid German USt-IdNr format"


def tax_sg(t: str):
    if not re.fullmatch(r"(\d{8}[A-Z]|\d{9}[A-Z]|[TSR]\d{2}[A-Z]{2}\d{4}[A-Z])", t):
        return False, "expected a Singapore UEN (e.g. 201912345K)"
    return True, "valid UEN format"


TAX_VALIDATORS = {
    "IN": ("GSTIN", tax_in),
    "US": ("EIN", tax_us),
    "GB": ("UK VAT number", tax_gb),
    "DE": ("German VAT ID", tax_de),
    "SG": ("UEN", tax_sg),
}


# ---------- bank details ----------
_BIC = r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?"


def _bic_ok(bic: str, country: str):
    if not bic:
        return True, ""
    if not re.fullmatch(_BIC, bic):
        return False, "SWIFT/BIC code is malformed"
    if bic[4:6] != country:
        return False, f"SWIFT/BIC country letters '{bic[4:6]}' do not match bank country {country}"
    return True, ""


def bank_validate(country: str, account: str, code: str):
    """Return (supported, ok, why)."""
    if country == "IN":
        if not re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", code):
            return True, False, "IFSC must be 4 letters, a zero, then 6 characters"
        if not re.fullmatch(r"\d{9,18}", account):
            return True, False, "Indian account numbers are 9-18 digits"
        return True, True, "IFSC and account number formats are valid"
    if country == "US":
        if not aba_ok(code):
            return True, False, "routing number fails the ABA checksum"
        if not re.fullmatch(r"\d{4,17}", account):
            return True, False, "US account numbers are 4-17 digits"
        return True, True, "ABA routing checksum and account format are valid"
    if country == "GB":
        if not re.fullmatch(r"\d{2}-?\d{2}-?\d{2}", code):
            return True, False, "UK sort code must be 6 digits"
        if not re.fullmatch(r"\d{8}", account):
            return True, False, "UK account numbers are 8 digits"
        return True, True, "sort code and account number formats are valid"
    if country in ("DE", "AE"):
        want_len = {"DE": 22, "AE": 23}[country]
        if not account.startswith(country) or len(account) != want_len:
            return True, False, f"expected a {country} IBAN of {want_len} characters"
        if not iban_ok(account):
            return True, False, "IBAN checksum (mod-97) failed - likely a typo"
        ok, why = _bic_ok(code, country)
        return True, ok, why or "IBAN checksum valid"
    if country == "SG":
        if not re.fullmatch(r"\d{7,14}", account):
            return True, False, "Singapore account numbers are 7-14 digits"
        ok, why = _bic_ok(code, country)
        return True, ok, why or "account number format is valid"
    return False, False, f"no automated bank validator for {country}"
