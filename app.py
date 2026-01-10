import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="BTÜ Asistanı", layout="centered")

# --- BTÜ LOGOSU VE MODERN TASARIM CSS ---
st.markdown("""
    <style>
    /* Streamlit öğelerini içeriden gizle */
    header, footer, .stDeployButton, [data-testid="stStatusWidget"], button[title="View fullscreen"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* Modern Balonlar */
    [data-testid="stChatMessage"] {
        border-radius: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    /* Asistan Balonu (BTÜ Kırmızısı Detay) */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #ffffff;
        border-left: 5px solid #d32f2f;
    }

    /* Kullanıcı Balonu */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #f0f7ff;
        border-right: 5px solid #007bff;
    }
    </style>
    """, unsafe_allow_html=True)
# --- API KURULUMU ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API Anahtarı eksik!")

# --- PDF OKUMA ---
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

# --- SOHBET GEÇMİŞİ VE ÖNERİLER ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Karşılama Ekranı
if not st.session_state.messages:
    st.markdown("### 🤖 BTÜ Öğrenci İşleri Asistanı")
    st.write("Merhaba! Ben Bursa Teknik Üniversitesi asistanıyım. Size nasıl yardımcı olabilirim?")
    
    c1, c2 = st.columns(2)
    if c1.button("📑 Ders Açma İşlemleri"):
        st.session_state.pending_prompt = "Bölümümde ders açmak istiyorum, ne yapmalıyım?"
    if c2.button("📅 Sınav Tarihleri"):
        st.session_state.pending_prompt = "Kısa sınav tarihimi nasıl öğrenebilirim?"

# Mesajları Ekrana Bas (BTÜ LOGOSU BURADA)
for message in st.session_state.messages:
    avatar_img = "https://btu.edu.tr/dosyalar/btu/dosyalar/BTU_Logo_Yatay_TR_Siyah(1).png" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar_img):
        st.markdown(message["content"])

# --- SORGULAMA ---
prompt = st.chat_input("Sorunuzu buraya yazın...")
if "pending_prompt" in st.session_state:
    prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.spinner("Cevaplanıyor..."):
        sys_instr = f"Sen BTÜ asistanısın. Şu bilgilere bak: {context[:25000]}. Bilgi yoksa genel dünya bilgini kullan. Doğal ol, 'metne göre' deme."
        
        # Senin çalışan model listen
        selected_models = ['models/gemini-2.0-flash', 'models/gemini-flash-latest']
        for m_name in selected_models:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(f"{sys_instr}\n\nSoru: {prompt}")
                if response.text:
                    with st.chat_message("assistant", avatar="https://btu.edu.tr/dosyalar/btu/dosyalar/BTU_Logo_Yatay_TR_Siyah(1).png"):
                        st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    st.rerun()
                    break
            except: continue

