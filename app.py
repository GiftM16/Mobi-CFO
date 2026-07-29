import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image
import pdfplumber
import re

st.set_page_config(page_title="MOBI CFO", page_icon="💼")
st.title("💼 MOBI CFO - AI INVOICE READER")
st.caption("Reads COLD DRINK x6 R70 perfectly")

uploaded_file = st.file_uploader("📄 Upload Invoice PDF or Image", type=['pdf','png','jpg','jpeg'])

@st.cache_data
def ultimate_parser(file):
    # 1. GET TEXT
    if file.type == "application/pdf":
        with pdfplumber.open(file) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    else:
        image = Image.open(file)
        text = pytesseract.image_to_string(image, config='--psm 6') # better for blocks
    
    text = text.upper()
    rows = []
    
    # 2. ULTIMATE PATTERN: ITEM NAME QTY PRICE
    # Matches: COLD DRINK x6 R70  |  BREAD 2 30.00  |  MILK 25
    pattern = r'([A-Z][A-Z\s]{3,}?)\s*(?:X\s*|QTY\s*)?([0-9]{1,3})?\s*R?\s?([0-9]{1,4}[.,]?[0-9]{0,2})'
    
    for line in text.split('\n'):
        if any(word in line for word in ['TOTAL','VAT','SUBTOTAL','CHANGE']): continue
        
        for match in re.finditer(pattern, line):
            item, qty, price = match.groups()
            
            # CLEAN ITEM
            item = item.strip()
            item = re.sub(r'\s+', ' ', item) # COLD   DRINK -> COLD DRINK
            item = item.replace('CO0L','COLD').replace('DR1NK','DRINK').replace('M1LK','MILK')
            
            # CLEAN QTY
            qty = f"x{qty}" if qty else "x1"
            
            # CLEAN PRICE
            price = 'R' + price.replace(',','.')
            
            if len(item) > 2 and float(price.replace('R','')) > 0:
                rows.append([item, qty, price])
    
    df = pd.DataFrame(rows, columns=['Item','Qty','Price'])
    return df.drop_duplicates()

if uploaded_file:
    with st.spinner('🧠 Reading like a human...'):
        df = ultimate_parser(uploaded_file)
    
    if len(df) > 0:
        st.success(f"✅ Found {len(df)} items!")
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Excel", csv, 'mobi_cfo_invoice.csv', 'text/csv')
    else:
        st.warning("No items found. Use PDF or clearer photo.")

st.divider()
st.write("**Mpho Moloi | 060 269 5423 | mphomolotmr16@gmail.com**")
