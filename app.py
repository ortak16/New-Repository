import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. GÜVENLİK: API anahtarını Streamlit Secrets'tan alıyoruz
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("Hata: API Anahtarı bulunamadı!")

# 2. PDF OKUMA FONKSİYONU
def get_pdf_text(pdf_file):
    text = ""
    pdf_reader = PdfReader(pdf_file)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# 3. SAYFA AYARLARI (Gömme moduna uygun)
st.set_page_config(page_title="Destek Botu", layout="centered")

# Görseli sadeleştiren CSS (Menüleri gizler)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 Bilgi Asistanı")
st.warning("⚠️ Kişisel veri paylaşmayın, veriler işlenmektedir.")

# 4. PDF'İ OTOMATİK YÜKLE
# Klasördeki 'bilgiler.pdf' dosyasını okur
context = ""
try:
    with open("bilgiler.pdf", "rb") as f:
        context = get_pdf_text(f)
except FileNotFoundError:
    st.error("Hata: 'bilgiler.pdf' dosyası bulunamadı!")

# 5. SOHBET GEÇMİŞİ VE CEVAPLAMA
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Sorunuzu buraya yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gemini'ye PDF içeriğiyle birlikte soruyu gönder
    model = genai.GenerativeModel('gemini-pro')
    full_query = f"Bağlam: {context}\n\nSoru: {prompt}\n\nLütfen sadece yukarıdaki bağlama göre cevap ver."
    
    response = model.generate_content(full_query)
    
    with st.chat_message("assistant"):
        st.markdown(response.text)

    st.session_state.messages.append({"role": "assistant", "content": response.text})

