"""
Configuration for the annual-report financial extractor.

Defines, per CSV column, the label variants that show up in Nigerian
audited financial statements (NGX filings), grouped by entity type since
banks and non-banks report different line items.
"""

# Columns in the master CSV that are never extracted from a PDF.
NON_EXTRACTED_COLUMNS = ["ticker", "period_end", "period_type", "audited", "source_doc", "extracted_by"]

# All extractable numeric/text columns, in CSV order.
EXTRACTABLE_COLUMNS = [
    "revenue",
    "cost_of_sales",
    "gross_profit",
    "operating_profit",
    "ebitda",
    "net_interest_income",
    "impairment_charge",
    "pbt",
    "tax",
    "pat",
    "total_assets",
    "total_equity",
    "total_debt",
    "cash",
    "customer_deposits",
    "loans_advances",
    "eps",
    "dps",
]

# Columns expressed in Naira per share, not raw amounts -> no unit scaling applied.
PER_SHARE_COLUMNS = {"eps", "dps"}

# Ticker -> entity type. "bank" statements use net_interest_income /
# impairment_charge / customer_deposits / loans_advances instead of
# cost_of_sales / gross_profit / operating_profit / ebitda.
ENTITY_TYPE = {
    "GTCO": "bank",
    "ACCESSCORP": "bank",
    "ARADEL": "nonbank",
    "BUAFOODS": "nonbank",
}

# Columns that should be left blank (not applicable) for each entity type,
# used to auto-blank fields rather than guess at them.
NOT_APPLICABLE_BY_ENTITY_TYPE = {
    "bank": {"cost_of_sales", "gross_profit", "operating_profit", "ebitda"},
    "nonbank": {"net_interest_income", "impairment_charge", "customer_deposits", "loans_advances"},
}

# Label regex patterns (case-insensitive) used to locate each line item in
# extracted table rows or text lines. Order matters: earlier patterns are
# tried first. Add more variants here as you encounter new report layouts.
LABEL_PATTERNS = {
    "revenue": [
        r"^revenue$",
        r"^revenue\s+from\s+contracts?\s+with\s+customers$",
        r"^gross\s+earnings$",
        r"^turnover$",
    ],
    "cost_of_sales": [
        r"^cost\s+of\s+sales$",
        r"^cost\s+of\s+goods\s+sold$",
    ],
    "gross_profit": [
        r"^gross\s+profit$",
    ],
    "operating_profit": [
        r"^operating\s+profit$",
        r"^profit\s+from\s+operations$",
        r"^results?\s+from\s+operating\s+activities$",
    ],
    "ebitda": [
        r"^ebitda$",
        r"^earnings\s+before\s+interest,?\s+tax,?\s+depreciation\s+and\s+amortisation$",
    ],
    "net_interest_income": [
        r"^net\s+interest\s+income$",
    ],
    "impairment_charge": [
        r"^impairment\s+charge",
        r"^credit\s+loss\s+expense",
        r"^impairment\s+losses?\s+on\s+financial\s+assets",
        r"^net\s+impairment\s+(loss|charge)",
    ],
    "pbt": [
        r"^profit\s+before\s+(income\s+)?tax(ation)?$",
        r"^profit\s+before\s+tax\s+from\s+continuing\s+operations$",
    ],
    "tax": [
        r"^(income\s+)?tax\s+expense$",
        r"^taxation$",
    ],
    "pat": [
        r"^profit\s+for\s+the\s+year$",
        r"^profit\s+after\s+tax(ation)?$",
        r"^profit\s+for\s+the\s+period$",
    ],
    "total_assets": [
        r"^total\s+assets$",
    ],
    "total_equity": [
        r"^total\s+equity$",
        r"^equity\s+attributable\s+to\s+(the\s+)?owners",
        r"^total\s+shareholders.?\s+funds$",
    ],
    "total_debt": [
        r"^borrowings$",
        r"^total\s+borrowings$",
        r"^interest[\s-]bearing\s+loans\s+and\s+borrowings$",
        r"^debt\s+securities\s+issued$",
    ],
    "cash": [
        r"^cash\s+and\s+cash\s+equivalents$",
        r"^cash\s+and\s+balances\s+with\s+central\s+bank",
    ],
    "customer_deposits": [
        r"^deposits\s+from\s+customers$",
        r"^customer\s+deposits$",
    ],
    "loans_advances": [
        r"^loans\s+and\s+advances\s+to\s+customers$",
        r"^loans\s+to\s+customers$",
    ],
    "eps": [
        r"^basic\s+earnings\s+per\s+share",
        r"^earnings\s+per\s+share",
    ],
    "dps": [
        r"^dividend\s+per\s+share$",
        r"^proposed\s+dividend\s+per\s+share$",
    ],
}

# Phrases indicating the reporting unit of the statement/page, used to
# normalize every extracted figure back to full Naira amounts.
UNIT_SCALE_PATTERNS = [
    (r"in\s+millions?\s+of\s+naira", 1_000_000),
    (r"n\s*'?\s*million", 1_000_000),
    (r"\bn'?m\b", 1_000_000),
    (r"in\s+thousands?\s+of\s+naira", 1_000),
    (r"n\s*'?\s*000", 1_000),
    (r"\bn'?000\b", 1_000),
]
