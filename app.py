import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image
import pdfplumber
import re

st.set_page_config(page_title="MOBI CFO", page_icon="💼")
st.title("💼 MOBI CFO - AI INVOICE READER")
st.caption("The smartest invoice reader for SA businesses")

uploaded_file = st.file_uploader("📄 Upload Invoice PDF or Image", type=['pdf','png','jpg','jpeg'])

def clean_text(t):
    t = t.upper()
    t = t.replace('@','0').replace('O','0').replace('I','1').replace('S','5').replace('l','1')
    t = re.sub(r'\s+', ' ', t).strip()
    return t

@st.cache_data
def smart_process(file):
    if file.type == "application/pdf":
        with pdfplumber.open(file) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    else:
        image = Image.open(file)
        text = pytesseract.image_to_string(image)
    
    text = clean_text(text)
    rows = []
    
    for line in text.split('\n'):
        if 'TOTAL' in line or 'VAT' in line or 'SUBTOTAL' in line: continue
        if len(line) < 4: continue
        
        price_match = re.search(r'R?\s?([0-9]{1,4}[.,]?[0-9]{0,2})', line)
        if not price_match: continue
        price = 'R' + price_match.group(1).replace(',','.')
        
        qty_match = re.search(r'(?:X|QTY)?\s?([0-9]{1,3})', line)
        qty = 'x' + qty_match.group(1) if qty_match else 'x1'
        
        item = line
        item = item.replace(price_match.group(0), '')
        if qty_match: item = item.replace(qty_match.group(0), '')
        item = re.sub(r'X|QTY|EACH|EA', '', item).strip()
        
        item = item.replace('CO0L','COOL').replace('DR1NK','DRINK').replace('M1LK','MILK')
        
        if len(item) > 2:
            rows.append([item, qty, price])
    
    df = pd.DataFrame(rows, columns=['Item','Qty','Price'])
    df = df.drop_duplicates()
    return df

if uploaded_file:
    with st.spinner('🧠 AI is reading...'):
        df = smart_process(uploaded_file)
    
    st.success(f"✅ Found {len(df)} items!")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Excel", csv, 'mobi_cfo_invoice.csv', 'text/csv')

st.divider()
st.markdown("### 📞 Need Help?")
st.write("**Mpho Moloi**")
st.write("**WhatsApp:** 060 269 5423")
st.write("**Email:** mphomolotmr16@gmail.com")  # YOUR EMAIL
