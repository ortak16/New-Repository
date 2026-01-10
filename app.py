import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Hızlı Asistan", layout="centered")
st.title("⚡ Hızlı Bilgi Asistanı")

# --- 1. API KURULUMU ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        st.error("⚠️ API Anahtarı bulunamadı! Lütfen 'Manage App' -> 'Secrets' kısmını kontrol edin.")
        st.stop()
except Exception as e:
    st.error(f"Bağlantı Hatası: {e}")
    st.stop()

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
        return f"PDF hatası: {e}"

# --- 3. PDF YÜKLEME ---
context = ""
try:
    # Dosya adının tam olarak 'bilgiler.pdf' olduğundan emin olun
    with open("bilgiler.pdf", "rb") as f:
        context = get_pdf_text(f)
except FileNotFoundError:
    st.info("ℹ️ Not: 'bilgiler.pdf' dosyası yüklenmediği için bot genel bilgiyle cevap verecek.")

# --- 4. SOHBET GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- 5. SOHBET MANTIĞI (GÜNCELLENMİŞ MODEL) ---
if prompt := st.chat_input("Sorunuzu buraya yazın..."):
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    response_text = ""
    
    # Senin listendeki EN İYİ ve EN HIZLI modeller
    # 1. Tercih: 2.0 Flash (Çok hızlı ve yüksek kotalı)
    # 2. Tercih: Flash Latest (Yedek)
    selected_models = [
        'models/gemini-2.0-flash', 
        'models/gemini-flash-latest'
    ]

    with st.spinner("Yanıtlanıyor..."):
        # PDF içeriğini çok uzunsa kırpalım (Hata riskini düşürür)
        # Flash modelleri büyük veri sever ama biz yine de garantici olalım.
        limited_context = context[:30000] if context else ""
        
        full_prompt = f"Sen yardımsever bir asistansın. Aşağıdaki bağlama göre cevap ver.\n\nBağlam: {limited_context}\n\nSoru: {prompt}"

        # Modelleri sırayla dene
        for m_name in selected_models:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(full_prompt)
                
                if response and response.text:
                    response_text = response.text
                    break # Başarılı olduysa döngüden çık
            except Exception as e:
                print(f"{m_name} hata verdi: {e}")
                continue

    # Sonuç Yazdırma
    if response_text:
        with st.chat_message("assistant"):
            st.write(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    else:
        st.error("⚠️ Bağlantı kurulamadı. Lütfen sayfayı yenileyip tekrar deneyin.")
