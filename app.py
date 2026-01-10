import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- 1. SAYFA AYARLARI VE CSS (Built with Streamlit ve Fullscreen Gizleme) ---
st.set_page_config(page_title="BTÜ Asistanı", layout="centered")

st.markdown("""
    <style>
    /* Streamlit yazılarını ve butonlarını tamamen gizle */
    header, footer, .stDeployButton, [data-testid="stStatusWidget"], button[title="View fullscreen"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Modern Balon Tasarımı */
    [data-testid="stChatMessage"] {
        border-radius: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    /* Asistan Balonu (Sol) */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #ffffff;
        border-left: 5px solid #d32f2f;
    }
    
    /* Kullanıcı Balonu (Sağ) */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #f0f7ff;
        border-right: 5px solid #007bff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API VE PDF KURULUMU ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("API Anahtarı bulunamadı!")
except Exception as e:
    st.error(f"Bağlantı Hatası: {e}")

@st.cache_data
def get_pdf_text():
    text = ""
    try:
        with open("bilgiler.pdf", "rb") as f:
            pdf_reader = PdfReader(f)
            for page in pdf_reader.pages:
                content = page.extract_text()
                if content: text += content
        return text
    except:
        return ""

context = get_pdf_text()

# --- 3. SOHBET GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- 4. SORGULAMA MANTIĞI ---
if prompt := st.chat_input("Sorunuzu buraya yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    response_text = ""
    
    # SENİN İSTEDİĞİN MODEL LİSTESİ
    selected_models = ['models/gemini-2.0-flash', 'models/gemini-flash-latest']

    with st.spinner("Yazıyor..."):
        # Robotik ifadeleri engelleyen talimat
        system_instruction = f"""
        Sen yardımsever bir BTÜ asistansın.
        Şu bilgilere dayanarak cevap ver: {context[:25000]}
        ÖNEMLİ: "Sağlanan bağlama göre" gibi ifadeler kullanma. 
        Doğrudan ve samimi cevap ver. Bilgi yoksa genel bilgini kullan.
        """
        
        # Modelleri sırayla dene
        for m_name in selected_models:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(f"{system_instruction}\n\nSoru: {prompt}")
                
                if response and response.text:
                    response_text = response.text
                    break 
            except Exception:
                continue

    # Sonuç Yazdırma ve Hata Maskeleme
    if response_text:
        with st.chat_message("assistant"):
            st.write(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    else:
        # Uzun hata mesajı yerine kısa uyarı
        st.error("⚠️ Sistem şu an çok yoğun. Lütfen kısa bir süre sonra tekrar deneyiniz.")
