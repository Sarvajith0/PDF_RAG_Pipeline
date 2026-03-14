
import pdfplumber
import json
import re
PDF_PATH = r".\sample-tables.pdf"
OUTPUT_PATH = r".\knowledge_base.json"
# Map of (page_number, table_index_on_page) → table name
# Detected by reading page text alongside table positions
TABLE_NAME_MAP = {
    (1, 0): "Table 1: Basic header structure example",
    (1, 1): "Table 2: Expenditure by function with footnotes (2009-2011)",
    (1, 2): "Table 3: Film credits style layout without column headers",
    (2, 0): "Table 4: Film credits with column headers (Role and Actor)",
    (2, 1): "Table 5: Year-end financial statement in pounds thousands (2008-2010)",
    (2, 2): "Table 6: Rainfall by continent with multi-level headers (2009-2010)",
    (3, 0): "Table 7: Year-end statement non-current assets in pounds thousands (2008-2010)",
    (3, 1): "Table 8: Year-end statement current assets in pounds thousands (2008-2010)",
    (3, 2): "Table 9: Rainfall by continent 2009",
    (4, 0): "Table 10: Self-contained year-end statement with layout problems (2011)",
    (4, 1): "Table 11: Self-contained year-end statement resolved layout (2011)",
    (5, 0): "Table 12: Merged data cells example (2008-2009)",
    (5, 1): "Table 13: Use of graphic symbols for survey responses",
    (5, 2): "Table 14: Survey responses with real text instead of symbols",
    (5, 3): "Table 15: Courses offered by Institution X by degree type (2006-2009)",
    (6, 0): "Table 16: Masters courses offered by Institution X (2006-2009)",
    (6, 1): "Table 17: Accounts 2011 in pounds thousands with subtotals",
    (6, 2): "Table 18: Accounts 2011 in pounds thousands with negative costs",
    (7, 0): "Table 19: Human Development Index HDI trends 1980 to 2010",
    (7, 1): "Table 20: Expenditure by function with footnotes referenced",
    (8, 0): "Table 21: Expenditure by function footnotes replaced by summary",
    (8, 1): "Table 22: Expenditure with multiple endnotes referenced",
    (8, 2): "Table 23: Simulated table using tabs (2008-2009)",
    (9, 0): "Table 24: Year-end financial statement with liabilities in pounds thousands",
    (9, 1): "Table 25: Competition entries and wins (2008-2009)",
    (9, 2): "Table 26: Courses offered by Institution X updated (2006-2009)",
    (10, 0): "Table 27: Simulated table using tab stops for fruit counts",
    (10, 1): "Table 28: Year-end financial table with headings problem revisited",
    (11, 0): "Table 29: Rainfall by continent with multiple header attributes (2008-2010)",
}

def clean(value):
    if value is None:
        return ""
    return re.sub(r'\s+', ' ', str(value)).strip()

def serialize_table_to_text(name, headers, rows):
    """Convert table headers and rows into a readable text summary for the LLM."""
    lines = [f"Table name: {name}"]
    lines.append(f"Headers: {' | '.join([clean(h) for h in headers if clean(h)])}")
    for row in rows:
        cleaned_row = [clean(c) for c in row]
        if any(cleaned_row):
            lines.append("Row: " + " | ".join(cleaned_row))
    return " || ".join(lines)

def extract_keywords(name, headers, rows):
    """Extract searchable keywords from table name, headers and row values."""
    text = name + " " + " ".join([clean(h) for h in headers])
    for row in rows:
        text += " " + " ".join([clean(c) for c in row])
    # Extract meaningful words (length > 2, not just numbers)
    words = re.findall(r'[a-zA-Z]{3,}', text.lower())
    return list(set(words))

# extracting data
tables_data = []

with pdfplumber.open(PDF_PATH) as pdf:
    for page_num, page in enumerate(pdf.pages, start=1):
        tables = page.extract_tables()

        for table_idx, table in enumerate(tables):
            if not table or len(table) < 1:
                continue

            # Get table name from map
            name = TABLE_NAME_MAP.get((page_num, table_idx), f"Table on page {page_num} index {table_idx}")

            # First row as headers
            headers = [clean(h) for h in table[0]]
            rows = [[clean(c) for c in row] for row in table[1:] if any(clean(c) for c in row)]

            # Build text summary for LLM context
            text_summary = serialize_table_to_text(name, headers, rows)

            # Build keywords for retrieval
            keywords = extract_keywords(name, headers, rows)

            table_entry = {
                "id": f"table_{len(tables_data) + 1}",
                "name": name,
                "page": page_num,
                "headers": headers,
                "rows": rows,
                "text_summary": text_summary,
                "keywords": keywords
            }

            tables_data.append(table_entry)
            print(f"Extracted: {name} ({len(rows)} rows)")

#To json
knowledge_base = {
    "document": "sample-tables.pdf",
    "description": "Accessible PDF tables sample document — contains 29 tables of various types including financial statements, rainfall data, course listings, and survey results.",
    "total_tables": len(tables_data),
    "tables": tables_data
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(knowledge_base, f, indent=2, ensure_ascii=False)

print(f"\nDone {len(tables_data)} tables saved to knowledge_base.json")