import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image
import pdfplumber
import re

st.set_page_config(page_title="MOBI CFO", page_icon="💼")
st.title("💼 MOBI CFO - SA INVOICE READER")
st.caption("Always outputs in R - for South African businesses")

uploaded_file = st.file_uploader("📄 Upload Invoice PDF or Image", type=['pdf','png','jpg','jpeg'])

def to_rand(val):
    """Convert any currency to R"""
    val = str(val).replace('$','').replace('€','').replace('₺','').replace(',','.')
    val = re.sub(r'[^0-9.]','', val)
    return 'R' + val if val else 'R0'

@st.cache_data
def sa_parser(file):
    rows = []
    text = ""
    
    if file.type == "application/pdf":
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            if not row: continue
                            row = [str(cell).strip() if cell else "" for cell in row]
                            
                            # FORMAT: ITEM | QTY |... | AMOUNT
                            if len(row) >= 4:
                                item, qty, amount = row[0], row[1], row[-1]
                                amount = to_rand(amount)
                                qty = 'x' + re.sub(r'[^0-9.]','', qty) if re.sub(r'[^0-9.]','', qty) else "x1"
                                
                                if 'DESCRIPTION' not in item.upper() and 'TOTAL' not in item.upper() and len(item) > 2:
                                    rows.append([item][qty][amount])
    
    else: # IMAGE
        image = Image.open(file)
        text = pytesseract.image_to_string(image, lang='eng+tur')
        
        for line in text.split('\n'):
            # Find any number as price and convert to R
            prices = re.findall(r'[0-9]{2,4}[.,]?[0-9]{0,2}', line)
            if prices:
                price = to_rand(prices[-1]) # last number is usually price
                item = re.sub(r'[0-9]{2,4}[.,]?[0-9]{0,2}', '', line).strip()
                item = re.sub(r'X|QTY','', item).strip()
                qty_match = re.search(r'([0-9]{1,3})', item)
                qty = 'x' + qty_match.group(1) if qty_match else "x1"
                item = re.sub(r'[0-9]{1,3}', '', item).strip()
                
                if len(item) > 2 and float(price.replace('R','')) > 0:
                    rows.append([item][qty][price])
    
    df = pd.DataFrame(rows, columns=['Item','Qty','Price'])
    return df.drop_duplicates()

if uploaded_file:
    with st.spinner('🧠 Converting to R...'):
        df = sa_parser(uploaded_file)
    
    if len(df) > 0:
        st.success(f"✅ Found {len(df)} items - All in ZAR")
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Excel", csv, 'mobi_cfo_invoice.csv', 'text/csv')

st.divider()
st.write("**Mpho Moloi | 060 269 5423 | mphomolotmr16@gmail.com**")
