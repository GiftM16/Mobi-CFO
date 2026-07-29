import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image
import pdfplumber
import re
import io

# ===== DESIGN =====
st.set_page_config(page_title="MOBI CFO", page_icon="💼", layout="wide")

st.markdown("""
<style>
 .main {background-color: #0E1117;}
 .stApp {background: linear-gradient(135deg, #0E1117 0%, #1a1f2e 100%);}
  h1 {color: #00D4FF!important; font-weight: 800;}
  h3 {color: #FFFFFF!important;}
 .stDownloadButton>button {
    background: linear-gradient(90deg, #00FF88 0%, #00D4FF 100%);
    color: black; font-weight: 800; border-radius: 10px; border: none; font-size: 18px; padding: 15px 30px;
  }
  [data-testid="stFileUploader"] {background-color: #1a1f2e; border-radius: 10px; padding: 20px;}
 .contact-box {background-color: #1a1f2e; padding: 20px; border-radius: 10px; border-left: 4px solid #00D4FF;}
</style>
""", unsafe_allow_html=True)

# ===== HEADER WITH LOGO =====
col1, col2 = st.columns([1,4])
with col1:
    st.image("https://img.icons8.com/ios-filled/100/00D4FF/briefcase.png", width=80)
with col2:
    st.title("MOBI CFO")
    st.subheader("Turn Invoices into Excel in 5 Seconds")
    st.caption("Built for South African Small Businesses")

st.divider()

# ===== OCR FUNCTIONS =====
def perfect_clean(text):
    text = str(text).upper()
    text = text.replace('@', '0').replace('O', '0').replace('I', '1').replace('S', '5').replace('l', '1')
    text = re.sub(r'R[\s@O]*([0-9@O\.]+)', lambda m: 'R' + m.group(1).replace('@','0').replace('O','0'), text)
    text = re.sub(r'([0-9]+)[@O]+', lambda m: m.group(1) + '0', text)
    return text.strip()

def is_real_item(row):
    text = " ".join(row).lower()
    has_price = 'r' in text and any(c.isdigit() for c in text)
    has_product = any(word in text for word in ['bread','milk','coke','juice','water','kg','ml','l','x','each'])
    return has_price and has_product

def process_image(image):
    text = pytesseract.image_to_string(image)
    lines = [line.split() for line in text.split('\n') if line.strip()]
    return lines

def process_pdf(pdf_file):
    all_text = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = [line.split() for line in text.split('\n') if line.strip()]
                all_text.extend(lines)
    return all_text

# ===== MAIN APP =====
uploaded_file = st.file_uploader("📄 Upload Invoice PDF or Image", type=['pdf','png','jpg','jpeg'])

if uploaded_file:
    with st.spinner('⚡ Processing...'):
        if uploaded_file.type == "application/pdf":
            raw_data = process_pdf(uploaded_file)
        else:
            image = Image.open(uploaded_file)
            raw_data = process_image(image)
        
        cleaned_data = [[perfect_clean(cell) for cell in row] for row in raw_data]
        clean_table = [row for row in cleaned_data if is_real_item(row)]
    
    st.success("✅ Done!")
    
    if len(clean_table) > 0:
        df = pd.DataFrame(clean_table)
        if df.shape[1] > 3: df = df.iloc[:, :3]
        df.columns = ['Item', 'Qty', 'Price'][:df.shape[1]]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # ===== DOWNLOAD BUTTON =====
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Excel",
            data=csv,
            file_name='mobi_cfo_invoice.csv',
            mime='text/csv',
        )
    else:
        st.warning("⚠️ No items found. Try a clearer photo or PDF.")

st.divider()

# ===== CONTACT SECTION =====
st.markdown('<div class="contact-box">', unsafe_allow_html=True)
st.subheader("📞 Need Help?")
st.write("**Mpho Moloi**")
st.write("**Contact:** 060 269 5423")
st.write("**Email:** support@mobicfo.co.za")
st.markdown('</div>', unsafe_allow_html=True)

st.caption("© 2026 MOBI CFO | Made in South Africa 🇿🇦")
