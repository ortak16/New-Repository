import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="BTÜ Asistanı", layout="centered")

# --- BTÜ LOGOSU VE MODERN TASARIM CSS ---
st.markdown("""
    <style>
    /* Streamlit'in gereksiz parçalarını gizle */
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
    
    /* Asistan Balonu (BTÜ Kırmızısı Çizgi) */
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
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        st.error("⚠️ API Anahtarı Bulunamadı! Lütfen Secrets ayarlarını kontrol edin.")
        st.stop()
except Exception as e:
    st.error(f"API Hatası: {e}")

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
    except FileNotFoundError:
        return "" 

context = load_pdf()

# --- SOHBET GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Karşılama Ekranı (Sadece mesaj yoksa göster)
if not st.session_state.messages:
    st.markdown("### 🤖 BTÜ Öğrenci İşleri Asistanı")
    st.write("Merhaba! Ben Bursa Teknik Üniversitesi asistanıyım. Size nasıl yardımcı olabilirim?")
    
    c1, c2 = st.columns(2)
    if c1.button("📑 Ders Açma İşlemleri"):
        st.session_state.pending_prompt = "Bölümümde ders açmak istiyorum, ne yapmalıyım?"
    if c2.button("📅 Sınav Tarihleri"):
        st.session_state.pending_prompt = "Kısa sınav tarihimi nasıl öğrenebilirim?"

# Geçmiş Mesajları Ekrana Bas
btu_logo = "https://btu.edu.tr/dosyalar/btu/dosyalar/BTU_Logo_Yatay_TR_Siyah(1).png"

for message in st.session_state.messages:
    avatar_img = btu_logo if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar_img):
        st.markdown(message["content"])

# --- SORGULAMA MANTIĞI ---
prompt = st.chat_input("Sorunuzu buraya yazın...")

if "pending_prompt" in st.session_state:
    prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt

if prompt:
    # 1. Kullanıcı mesajını ekle ve göster
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 2. Cevap Üretimi
    with st.spinner("Cevaplanıyor..."):
        # Bağlamı kısalt (Hata riskini azaltır)
        limited_context = context[:30000] if context else ""
        
        sys_instr = f"""
        Sen BTÜ asistanısın. Aşağıdaki bilgilere göre cevap ver.
        Bilgiler: {limited_context}
        Eğer bilgide yoksa genel bilgini kullan ama bunu belirt.
        Asla 'metne göre' veya 'bağlama göre' deme. Doğal ve yardımsever konuş.
        """
        
        # SENİN İSTEDİĞİN GİBİ: 2.0 Flash İLK SIRADA
        selected_models = [
            'models/gemini-2.0-flash',       # En hızlı ve yeni
            'models/gemini-1.5-flash',       # Yedek (Çok kararlı)
            'models/gemini-pro'              # Son çare
        ]
        
        response_text = ""
        last_error = ""

        for m_name in selected_models:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(f"{sys_instr}\n\nSoru: {prompt}")
                
                if response and response.text:
                    response_text = response.text
                    break # Başarılı olduysa döngüden çık
            except Exception as e:
                last_error = str(e)
                continue # Hata alırsan sessizce diğer modele geç

    # 3. Sonucu Ekrana Bas
    if response_text:
        with st.chat_message("assistant", avatar=btu_logo):
            st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        # st.rerun() komutunu kaldırdım, artık cevap kaybolmayacak!
    else:
        st.error(f"Üzgünüm, şu an bağlantı kurulamadı. Hata detayı: {last_error}")
