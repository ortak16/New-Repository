import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- 1. TASARIM VE GİZLEME ---
st.set_page_config(page_title="BTÜ Asistanı", layout="centered")

st.markdown("""
    <style>
    /* Streamlit yazılarını ve butonlarını gizle */
    header, footer, .stDeployButton, [data-testid="stStatusWidget"], button[title="View fullscreen"] {
        display: none !important;
        visibility: hidden !important;
    }
    /* Modern Balonlar */
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

context = load_pdf()[:12000] # Kota dostu uzunluk
btu_logo = "https://depo.btu.edu.tr/img/sayfa//1691132554_284ffd9ee8d6a4286478.png"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesaj Geçmişini Göster
for message in st.session_state.messages:
    avatar = btu_logo if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# --- 3. SORGULAMA VE KISA HATA MESAJI ---
if prompt := st.chat_input("Sorunuzu buraya yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.spinner("Yanıtlanıyor..."):
        try:
            # Model ismine dokunulmadı
            model = genai.GenerativeModel('models/gemini-2.0-flash')
            
            sys_instr = f"Sen BTÜ asistanısın. Şu bilgilere göre cevap ver: {context}. Doğal ol."
            response = model.generate_content(f"{sys_instr}\n\nSoru: {prompt}")
            
            if response and response.text:
                with st.chat_message("assistant", avatar=btu_logo):
                    st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.warning("Şu an yanıt veremiyorum, lütfen biraz sonra tekrar deneyiniz.")

        except Exception as e:
            # BURASI ÖNEMLİ: Hata ne olursa olsun kullanıcıya sadece bunu gösteriyoruz
            st.error("⚠️ Sistem şu an çok yoğun. Lütfen kısa bir süre sonra tekrar deneyiniz.")
            # Teknik hatayı sadece loglarda görmek istersen: print(e)
