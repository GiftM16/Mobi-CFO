import streamlit as st
import pdfplumber
import pytesseract
import pandas as pd
from PIL import Image, ImageEnhance
import io
import datetime
import re

st.set_page_config(page_title="MOBI CFO", page_icon="📄")
st.title("📄 MOBI CFO - Invoice Scanner")
st.write("Upload PDF or Photo. Get Excel in 5 seconds. R100 per file")

uploaded_file = st.file_uploader("Upload Invoice", type=['pdf', 'png', 'jpg', 'jpeg'])

def process_file(file_bytes, filename):
    text = ""
    if filename.endswith('.pdf'):
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                if page.extract_text(): 
                    text += page.extract_text() + "\n"
    else:
        image = Image.open(io.BytesIO(file_bytes)).convert('L')
        image = ImageEnhance.Contrast(image).enhance(2.5)
        text = pytesseract.image_to_string(image)
    
    data = []
    for line in text.split('\n'):
        if re.search(r'\d', line) and len(line.split()) > 1:
            parts = line.split()
            item = " ".join(parts[:-2])
            qty = parts[-2]
            price = parts[-1].replace("R","").replace(",","")
            data.append([item, qty, f"R{price}"])
    if data:
        return pd.DataFrame(data, columns=["Item","Qty","Price"])
    else:
        return None

if uploaded_file:
    with st.spinner("Reading invoice..."):
        df = process_file(uploaded_file.read(), uploaded_file.name)
    if df is not None and len(df) > 0:
        st.success("✅ Done!")
        st.dataframe(df, use_container_width=True)
        filename = f"MOBI_CFO_{datetime.date.today()}.xlsx"
        df.to_excel(filename, index=False)
        with open(filename, "rb") as f:
            st.download_button("📥 Download Excel", f, file_name=filename, type="primary")
    else:
        st.error("❌ Couldn't read. Try clearer photo in daylight.")
