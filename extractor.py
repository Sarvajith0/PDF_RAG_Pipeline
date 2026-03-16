
import pdfplumber
import json
import re
import os

PDF_PATH = "sample-tables.pdf"
OUTPUT_PATH = "knowledge_base.json"

def clean(value):
    """Clean a cell value."""
    if value is None:
        return ""
    return re.sub(r'\s+', ' ', str(value)).strip()

def extract_table_captions(page_text):

    pattern = r'((?:Table|TABLE)\s+(\d+)\s*[:\-\.—]\s*[^\n]{3,120})'
    matches = re.findall(pattern, page_text)
    
    captions = []
    for full_caption, table_num in matches:
        captions.append((int(table_num), clean(full_caption)))
    
    return captions

def get_caption_positions(page_text, captions):
  
    positions = {}
    for table_num, caption in captions:
        pos = page_text.find(caption[:30])   # search by first 30 chars
        if pos != -1:
            positions[table_num] = pos
    return positions

def match_captions_to_tables(page_captions, num_tables_on_page):
    
    matched = {}
    for i in range(num_tables_on_page):
        if i < len(page_captions):
            table_num, caption = page_captions[i]
            matched[i] = (table_num, caption)
        else:
            matched[i] = (None, None)
    return matched

def serialize_table_to_text(table_num, caption, headers, rows):
    """Convert table to readable text summary for LLM context."""
    num_tag = f"[TABLE NUMBER {table_num}] " if table_num else ""
    name_line = f"{num_tag}{caption}" if caption else f"Table on page"
    
    lines = [f"Table name: {name_line}"]
    clean_headers = [clean(h) for h in headers if clean(h)]
    if clean_headers:
        lines.append(f"Headers: {' | '.join(clean_headers)}")
    
    for row in rows:
        cleaned_row = [clean(c) for c in row]
        if any(cleaned_row):
            lines.append("Row: " + " | ".join(cleaned_row))
    
    return " || ".join(lines)

def extract_keywords(table_num, caption, headers, rows):
    """Extract searchable keywords including table number variants."""
    text = (caption or "") + " " + " ".join([clean(h) for h in headers])
    for row in rows:
        text += " " + " ".join([clean(c) for c in row])
    
    # General keywords
    words = list(set(re.findall(r'[a-zA-Z]{3,}', text.lower())))
    
    # Add explicit table number keywords so "Table 11" queries work
    if table_num:
        words += [
            f"table{table_num}",
            f"table {table_num}",
        ]
    
    return words

tables_data = []
global_table_counter = 0

with pdfplumber.open(PDF_PATH) as pdf:
    for page_num, page in enumerate(pdf.pages, start=1):
        page_text = page.extract_text() or ""
        tables = page.extract_tables()
        
        if not tables:
            continue
        
        # Step 1: Find all captions on this page
        page_captions = extract_table_captions(page_text)
        
        # Step 2: Match captions to tables by order
        caption_map = match_captions_to_tables(page_captions, len(tables))
        
        # Step 3: Process each table
        for table_idx, table in enumerate(tables):
            if not table or len(table) < 1:
                continue
            
            global_table_counter += 1
            
            # Get matched caption for this table
            table_num, caption = caption_map.get(table_idx, (None, None))
            
            # Fallback name if no caption detected
            if not caption:
                caption = f"Table {global_table_counter} on page {page_num}"
                table_num = global_table_counter
            
            # Extract headers and rows
            headers = [clean(h) for h in table[0]]
            rows = [[clean(c) for c in row] for row in table[1:] 
                    if any(clean(c) for c in row)]
            
            # Build text summary
            text_summary = serialize_table_to_text(
                table_num, caption, headers, rows
            )
            
            # Build keywords
            keywords = extract_keywords(table_num, caption, headers, rows)
            
            table_entry = {
                "id": f"table_{global_table_counter}",
                "table_number": table_num,
                "name": caption,
                "page": page_num,
                "headers": headers,
                "rows": rows,
                "text_summary": text_summary,
                "keywords": keywords
            }
            
            tables_data.append(table_entry)
            print(f"✅ Page {page_num} | {caption[:60]}")

doc_name = os.path.basename(PDF_PATH)

knowledge_base = {
    "document": doc_name,
    "total_tables": len(tables_data),
    "tables": tables_data
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(knowledge_base, f, indent=2, ensure_ascii=False)

print(f"\nDone! {len(tables_data)} tables saved to {OUTPUT_PATH}")