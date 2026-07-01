"""
Hand-curated seed chunks standing in for IRS form instructions, so the RAG
demo works out-of-the-box with no external downloads. Replace/extend with
real instruction text from irs.gov for a production version.
"""

SEED_CHUNKS = [
    {
        "id": "w2-box12-d",
        "source": "W-2 Instructions, Box 12 Codes",
        "text": (
            "Box 12 Code D reports elective deferrals to a 401(k) cash or "
            "deferred arrangement. This is a pre-tax retirement contribution "
            "and is not included in Box 1 wages, but is included in Box 3 "
            "and Box 5 (Social Security and Medicare wages)."
        ),
    },
    {
        "id": "w2-box12-dd",
        "source": "W-2 Instructions, Box 12 Codes",
        "text": (
            "Box 12 Code DD reports the total cost of employer-sponsored "
            "health coverage. This amount is informational only and is not "
            "taxable income to the employee."
        ),
    },
    {
        "id": "w2-box1-vs-box3",
        "source": "W-2 Instructions, General",
        "text": (
            "Box 1 (federal taxable wages) is often lower than Box 3 "
            "(Social Security wages) because pre-tax deductions like 401(k) "
            "contributions and some health/dental premiums reduce Box 1 but "
            "do not reduce Box 3 or Box 5."
        ),
    },
    {
        "id": "1099-nec-vs-misc",
        "source": "1099-NEC vs 1099-MISC Guidance",
        "text": (
            "Form 1099-NEC is used to report nonemployee compensation of "
            "$600 or more paid to a contractor or freelancer. Form 1099-MISC "
            "covers other types of payments such as rents, prizes, and "
            "awards. Nonemployee compensation should never appear on a "
            "1099-MISC for tax years 2020 and later."
        ),
    },
    {
        "id": "1099-int-box1",
        "source": "1099-INT Instructions",
        "text": (
            "Box 1 of Form 1099-INT reports taxable interest income of $10 "
            "or more paid by a bank, brokerage, or other payer during the "
            "tax year. This amount is reported on Schedule B if total "
            "interest exceeds $1,500."
        ),
    },
    {
        "id": "k1-box1-vs-box2",
        "source": "Schedule K-1 (Form 1065) Instructions",
        "text": (
            "Box 1 of a partnership K-1 reports ordinary business income or "
            "loss. Box 2 reports net rental real estate income or loss. "
            "These are reported on different lines of the partner's Schedule "
            "E and should not be combined."
        ),
    },
    {
        "id": "validation-ssn-format",
        "source": "Internal Validation Rule",
        "text": (
            "A valid SSN/EIN on a tax document should match the pattern "
            "XXX-XX-XXXX (SSN) or XX-XXXXXXX (EIN). Extracted values that "
            "don't match either pattern should be flagged as a possible OCR "
            "error for human review."
        ),
    },
    {
        "id": "validation-wage-sanity",
        "source": "Internal Validation Rule",
        "text": (
            "Box 1 wages on a W-2 should generally not exceed Box 3 Social "
            "Security wages by more than typical pre-tax deduction amounts. "
            "A Box 1 value significantly higher than Box 3 may indicate an "
            "OCR misread and should be flagged."
        ),
    },
]
