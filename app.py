import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# Sayfa Ayarları
st.set_page_config(page_title="ODB Asistanı", layout="centered")

# CSS Düzenlemeleri
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

# API Anahtarı
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"API Hatası: {e}")
    st.stop()

# PDF Yükleme
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
    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"PDF okunamadı: {e}")
        return ""
    return text

context = load_pdf()

# Sistem Talimatı Hazırlama
system_instruction = "Sen BTÜ asistanısın. Yardımcı ve kibar ol."
if context:
    system_instruction += f"\n\nŞu bilgilere dayanarak cevap ver: {context[:30000]}."
else:
    system_instruction += "\n\nPDF verisi bulunamadı, genel akademik bilgini kullan."

# MODEL YÜKLEME (GÜNCELLENDİ - Listede var olan model seçildi)
@st.cache_resource
def load_model():
    # Model ismi listenizde olan 'gemini-2.0-flash' olarak ayarlandı
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash", 
        system_instruction=system_instruction
    )

try:
    model = load_model()
except Exception as e:
    st.error(f"Model yüklenirken hata oluştu: {e}")
    st.stop()

btu_logo = "https://depo.btu.edu.tr/img/sayfa//1691132554_284ffd9ee8d6a4286478.png"

# Mesaj Geçmişi
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesajları Göster
for message in st.session_state.messages:
    avatar = btu_logo if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Prompt Kontrolü
if "pending_prompt" in st.session_state:
    prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt
else:
    prompt = st.chat_input("Sorunuzu buraya yazın...")

# Sohbet İşlemi
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.spinner("Cevaplanıyor..."):
        try:
            response = model.generate_content(prompt)
            
            if response and hasattr(response, "text"):
                answer = response.text
                with st.chat_message("assistant", avatar=btu_logo):
                    st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error("Model boş cevap döndürdü.")
        except Exception as e:
            st.error(f"Hata oluştu: {e}")

# Açılış Ekranı
if not st.session_state.messages:
    st.info("Merhaba! Size nasıl yardımcı olabilirim?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📑 Ders Kaydı"):
            st.session_state.pending_prompt = "Ders kaydı nasıl yapılır?"
            st.rerun()
    
    with col2:
        if st.button("📅 Akademik Takvim"):
            st.session_state.pending_prompt = "Akademik takvim hakkında bilgi ver."
            st.rerun()
