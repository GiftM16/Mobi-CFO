import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image, ImageEnhance
import pdfplumber
import re

st.set_page_config(page_title="Invoice Reader", page_icon="📄", layout="wide")
st.title("📄 AI INVOICE READER")
st.caption("Extracts Company Details + Items. All in R.")

def to_rand(val): 
    return 'R' + re.sub(r'[^0-9.]','', str(val))

@st.cache_data
def full_invoice_parser(file):
    text = ""
    if file.type == "application/pdf":
        with pdfplumber.open(file) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    else:
        image = Image.open(file)
        # Simple enhancement, no opencv
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        text = pytesseract.image_to_string(image, lang='eng')
    
    raw_lines = text.split('\n')
    text_up = text.upper()
    
    # 1. COMPANY DISTRIBUTION
    company = {
        "Company Name": "",
        "Address": "",
        "Phone": "",
        "Email": ""
    }
    
    for line in raw_lines[:5]:
        if len(line.strip()) > 3:
            company["Company Name"] = line.strip().title()
            break
    
    for line in raw_lines[:15]:
        if any(x in line.upper() for x in ['ROAD','STREET','AVE','RD','DRIVE','PO BOX','GAUTENG','LIMPOPO']):
            company["Address"] += line.strip() + ", "
    company["Address"] = company["Address"].rstrip(", ")
    
    phone_match = re.search(r'(TEL|TEL:|PHONE|CELL)\s*:?\s*([0-9\s\-\(\)]{9,})', text_up)
    if phone_match: company["Phone"] = phone_match.group(2).strip()
    
    email_match = re.search(r'([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})', text_up)
    if email_match: company["Email"] = email_match.group(1).lower()
    
    # 2. INVOICE INFO
    invoice = {
        "Invoice No": "",
        "Date": "",
        "Total": "",
        "Notes": ""
    }
    
    inv_match = re.search(r'INVOICE\s*(NO|#)?\s*:?\s*([A-Z0-9-]+)', text_up)
    if inv_match: invoice["Invoice No"] = inv_match.group(2)
    
    date_match = re.search(r'DATE\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})', text_up)
    if date_match: invoice["Date"] = date_match.group(1)
    
    total_match = re.search(r'TOTAL\s*:?\s*R?\s?([0-9]{1,5}[.,]?[0-9]{0,2})', text_up)
    if total_match: invoice["Total"] = to_rand(total_match.group(1))
    
    # 3. LINE ITEMS
    items = []
    for line in raw_lines:
        prices = re.findall(r'[0-9]{2,4}[.,]?[0-9]{0,2}', line)
        if prices and len(line) > 5:
            price = to_rand(prices[-1])
            item = re.sub(r'[0-9]{2,4}[.,]?[0-9]{0,2}', '', line).strip()
            qty_match = re.search(r'([0-9]{1,3})', item)
            qty = 'x' + qty_match.group(1) if qty_match else "x1"
            item = re.sub(r'[0-9]{1,3}', '', item).strip()
            if len(item) > 3 and 'TOTAL' not in item.upper():
                items.append([item, qty, price])
    
    df_items = pd.DataFrame(items, columns=['Item','Qty','Price']).drop_duplicates()
    return company, invoice, df_items

uploaded_file = st.file_uploader("Upload Invoice PDF or Image", type=['pdf','png','jpg','jpeg'])

if uploaded_file:
    if st.button("🔍 READ INVOICE"):
        with st.spinner('Reading...'):
            company, invoice, df = full_invoice_parser(uploaded_file)
        
        if len(df) > 0:
            st.success("✅ Invoice Captured")
            
            st.subheader("🏢 COMPANY DISTRIBUTION")
            c1, c2 = st.columns(2)
            c1.write(f"**Name:** {company['Company Name']}")
            c1.write(f"**Address:** {company['Address']}")
            c2.write(f"**Phone:** {company['Phone']}")
            c2.write(f"**Email:** {company['Email']}")
            
            st.divider()
            st.subheader("📋 INVOICE DETAILS")
            col1, col2, col3 = st.columns(3)
            col1.metric("Invoice #", invoice["Invoice No"] or "N/A")
            col2.metric("Date", invoice["Date"] or "N/A")
            col3.metric("Total", invoice["Total"] or "R0")
            
            st.divider()
            st.subheader("🛒 LINE ITEMS")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            export = pd.DataFrame([{**company, **invoice}])
            csv = pd.concat([export, df], axis=1).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Full Excel", csv, 'invoice_full.csv', 'text/csv')
        else:
            st.error("No items found. Try clearer image or PDF.")
