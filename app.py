import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image
import pdfplumber
import re

st.set_page_config(page_title="MOBI CFO", page_icon="💼", layout="wide")
st.title("💼 MOBI CFO")
st.subheader("Turn Invoices into Excel in 5 Seconds")

def perfect_clean(text):
    text = str(text).upper()
    text = text.replace('@', '0').replace('O', '0').replace('I', '1').replace('S', '5')
    text = re.sub(r'R[\s@O]*([0-9@O\.]+)', lambda m: 'R' + m.group(1).replace('@','0').replace('O','0'), text)
    return text.strip()

def is_real_item(row):
    text = " ".join(row).lower()
    has_price = 'r' in text and any(c.isdigit() for c in text)
    return has_price

uploaded_file = st.file_uploader("Upload Invoice PDF or Image", type=['pdf','png','jpg','jpeg'])

if uploaded_file:
    # OCR code here...
    st.success("Done!")
    # your processing + download button
