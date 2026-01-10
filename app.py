import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="ODB Asistanı", layout="centered")

# CSS: Gizlemeler ve Modern Balonlar
st.markdown("""
    <style>
    header, footer, .stDeployButton, [data-testid="stStatusWidget"], button[title="View fullscreen"] {
        display: none !important;
        visibility: hidden !important;
    }
    [data-testid="stChatMessage"] {
        border-radius: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #ffffff; border-left: 5px solid #d32f2f; }
    [data-testid="stChatMessage"]:nth-child(even) { background-color: #f0f7ff; border-right: 5px solid #007bff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API & PDF ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("API Hatası!")

@st.cache_data
def load_pdf():
    text = ""
    try:
        with open("bilgiler.pdf", "rb") as f:
            pdf_reader = PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except: return ""

context = load_pdf()

# BTÜ Logo Linki (Çalışan Şeffaf Logo)
btu_logo = "https://depo.btu.edu.tr/img/sayfa//1691132554_284ffd9ee8d6a4286478.png"

# --- 3. SOHBET GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesajları Ekrana Bas
for message in st.session_state.messages:
    avatar = btu_logo if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# --- 4. SORGULAMA (CEVAP VERMEYEN KISIM DÜZELTİLDİ) ---
prompt = st.chat_input("Sorunuzu buraya yazın...")

# Eğer öneri butonuna basıldıysa
if "pending_prompt" in st.session_state:
    prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.spinner("Cevaplanıyor..."):
        # Sistem talimatını çok uzun tutmadan modelin anlayacağı hale getirdik
        sys_instr = f"Sen BTÜ asistanısın. Sadece şu bilgilere odaklan: {context[:15000]}. Bilgi yoksa genel bilgini kullan ama doğal cevap ver."
        
        try:
            
            model = genai.GenerativeModel('models/gemini-2.0-flash')
            response = model.generate_content(f"{sys_instr}\n\nSoru: {prompt}")
            
            if response and response.text:
                answer = response.text
                with st.chat_message("assistant", avatar=btu_logo):
                    st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                # Not: st.rerun() burada bazen hataya sebep olur, streamlit zaten input gelince yeniler.
            else:
                st.error("Model cevap üretemedi.")
        except Exception as e:
            st.error(f"Hata oluştu: {str(e)}")

# Öneri butonları (Sadece boşken)
if not st.session_state.messages:
    st.info("Merhaba! Size nasıl yardımcı olabilirim?")
    if st.button("📑 Ders Açma İşlemleri Hakkında Bilgi"):
        st.session_state.pending_prompt = "Bölümümde ders açmak istiyorum, ne yapmalıyım?"
        st.rerun()
