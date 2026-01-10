import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# Sayfa ayarları
st.set_page_config(page_title="Destek Asistanı", layout="centered")
st.title("Bilgi Asistanı")

# --- 1. API ANAHTARI AYARLAMA (KLASİK YÖNTEM) ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        st.error("API Anahtarı bulunamadı! Lütfen Streamlit Secrets kısmına ekleyin.")
        st.stop()
except Exception as e:
    st.error(f"Bağlantı Hatası: {str(e)}")

# --- 2. FONKSİYONLAR ---
def get_pdf_text(pdf_file):
    text = ""
    try:
        pdf_reader = PdfReader(pdf_file)
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content: text += content
        return text
    except Exception as e:
        return f"PDF Okuma Hatası: {str(e)}"

# --- 3. PDF YÜKLEME ---
context = ""
try:
    with open("bilgiler.pdf", "rb") as f:
        context = get_pdf_text(f)
except FileNotFoundError:
    st.warning("⚠️ 'bilgiler.pdf' dosyası bulunamadı! Bot sadece genel bilgiyle cevap verecek.")

# --- 4. SOHBET GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- 5. SOHBET MANTIĞI ---
if prompt := st.chat_input("Sorunuzu buraya yazın..."):
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Yanıt üret
    response_text = ""
    success = False
    
    # Kararlı modeller listesi
    denenecek_modeller = [
        'gemini-1.5-flash',
        'gemini-pro'
    ]

    with st.spinner("Düşünüyor..."):
        # PDF içeriğini kısalt (Hata riskini azaltır)
        limited_context = context[:15000] if context else ""
        
        full_prompt = f"Aşağıdaki bilgilere göre cevapla.\n\nBağlam: {limited_context}\n\nSoru: {prompt}"

        for m_name in denenecek_modeller:
            try:
                # Klasik Kütüphane Çağrısı
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(full_prompt)
                
                if response and response.text:
                    response_text = response.text
                    success = True
                    break
            except Exception as e:
                print(f"Model {m_name} hatası: {e}")
                continue

    if success:
        with st.chat_message("assistant"):
            st.write(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    else:
        st.error("Üzgünüm, şu an bağlantı kurulamadı. Lütfen API anahtarınızın kotasını kontrol edin.")
