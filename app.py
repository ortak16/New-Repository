import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- 1. TASARIM VE GİZLEME (Dokunulmadı) ---
st.set_page_config(page_title="BTÜ Asistanı", layout="centered")

st.markdown("""
    <style>
    header, footer, .stDeployButton, [data-testid="stStatusWidget"], button[title="View fullscreen"] {
        display: none !important;
        visibility: hidden !important;
    }
    [data-testid="stChatMessage"] { border-radius: 20px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #ffffff; border-left: 5px solid #d32f2f; }
    [data-testid="stChatMessage"]:nth-child(even) { background-color: #f0f7ff; border-right: 5px solid #007bff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API VE PDF ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Sistem yapılandırılamadı.")

@st.cache_data
def load_pdf():
    try:
        text = ""
        with open("bilgiler.pdf", "rb") as f:
            pdf_reader = PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except: return ""

context = load_pdf()[:8000]

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 3. SORGULAMA (İstediğin Model Listesi Eklendi) ---
if prompt := st.chat_input("Sorunuzu buraya yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Yanıtlanıyor..."):
        # İSTEDİĞİN MODEL LİSTESİ
        selected_models = ['models/gemini-2.0-flash', 'models/gemini-flash-latest']
        
        response_text = ""
        success = False

        # Modelleri sırayla dene
        for m_name in selected_models:
            try:
                model = genai.GenerativeModel(m_name)
                sys_instr = f"Sen BTÜ asistanısın. Bilgi: {context}. Doğal ol."
                response = model.generate_content(f"{sys_instr}\n\nSoru: {prompt}")
                
                if response and response.text:
                    response_text = response.text
                    success = True
                    break # Başarılı olursa döngüden çık
            except Exception:
                continue # Hata alırsan listedeki bir sonraki modele geç

        if success:
            with st.chat_message("assistant"):
                st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        else:
            # Tüm modeller kota/hata verirse gösterilecek kısa mesaj
            st.error("⚠️ Sistem şu an çok yoğun. Lütfen 1-2 dakika sonra tekrar deneyiniz.")
