import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

st.set_page_config(page_title="ODB Asistanı", layout="centered")

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

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"API Hatası: {e}")
    st.stop()

@st.cache_data
def load_pdf():
    text = ""
    try:
        with open("bilgiler.pdf", "rb") as f:
            pdf_reader = PdfReader(f)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
    except Exception as e:
        st.error(f"PDF okunamadı: {e}")
    return text

context = load_pdf()

if not context:
    st.warning("PDF içeriği boş veya okunamadı.")

@st.cache_resource
def load_model():
    return genai.GenerativeModel("models/gemini-2.0-flash")

model = load_model()

btu_logo = "https://depo.btu.edu.tr/img/sayfa//1691132554_284ffd9ee8d6a4286478.png"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    avatar = btu_logo if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

prompt = st.chat_input("Sorunuzu buraya yazın...")

if "pending_prompt" in st.session_state:
    prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.spinner("Cevaplanıyor..."):
        sys_instr = f"Sen BTÜ asistanısın. Öncelikle şu bilgilere dayan: {context[:8000]}. Bilgi yoksa genel bilgini kullan ve doğal cevap ver."
        try:
            response = model.generate_content([
                {"role": "system", "parts": sys_instr},
                {"role": "user", "parts": prompt}
            ])
            if response and hasattr(response, "text"):
                answer = response.text
                with st.chat_message("assistant", avatar=btu_logo):
                    st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error("Model cevap üretemedi.")
        except Exception:
            st.error("⚠️ Sistem şu anda yoğun. Lütfen daha sonra tekrar deneyin.")


if not st.session_state.messages:
    st.info("Merhaba! Size nasıl yardımcı olabilirim?")
    if st.button("📑 Ders Açma İşlemleri Hakkında Bilgi"):
        st.session_state.pending_prompt = "Bölümümde ders açmak istiyorum, ne yapmalıyım?"




