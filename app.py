import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- 1. SAYFA AYARLARI VE GİZLEME ---
st.set_page_config(page_title="ODB Asistanı", layout="centered")

# --- MODERN TASARIM CSS ---
st.markdown("""
    <style>
    /* Ana Arkaplan */
    .stApp { background-color: #f8f9fa; }
    
    /* Mesaj Balonlarını Modernleştir */
    [data-testid="stChatMessage"] {
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* Kullanıcı Mesajı (Sağ tarafa yakın ve farklı renk) */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #e3f2fd;
        border-left: 5px solid #1976d2;
    }

    /* Asistan Mesajı (Sol tarafta ve BTÜ renklerine yakın) */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #ffffff;
        border-left: 5px solid #d32f2f;
    }

    /* Avatar Simgelerini Yuvarla */
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        border-radius: 50%;
    }

    /* Gizlemeler */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

# Manage App ve Streamlit öğelerini gizle
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stStatusWidget"] {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. API KURULUMU ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        st.error("⚠️ API Anahtarı bulunamadı!")
        st.stop()
except Exception as e:
    st.error(f"Bağlantı Hatası: {e}")
    st.stop()

# --- 3. PDF OKUMA ---
@st.cache_data
def load_context():
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

context = load_context()

# --- 4. SOHBET GEÇMİŞİ VE ÖNERİLER ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Başlangıç ekranı (Sadece mesaj yoksa görünür)
if not st.session_state.messages:
    st.markdown("### 🤖 BTÜ Öğrenci İşleri Asistanı")
    st.write("Merhaba! Ben Bursa Teknik Üniversitesi Öğrenci İşleri asistanıyım. Size nasıl yardımcı olabilirim?")
    
    st.write("👇 **Hızlı Erişim için Tıklayabilirsiniz:**")
    c1, c2 = st.columns(2)
    if c1.button("📑 Bölümümde ders açmak istiyorum?"):
        st.session_state.pending_prompt = "Bölümümde ders açmak istiyorum, ne yapmalıyım?"
    if c2.button("📅 Kısa sınav tarihlerini öğrenme?"):
        st.session_state.pending_prompt = "Kısa sınav tarihimi nasıl öğrenebilirim?"

# Mesajları ekrana bas
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. SOHBET MANTIĞI ---
# Butonla veya klavyeyle gelen soruyu al
prompt = st.chat_input("Sorunuzu buraya yazın...")
if "pending_prompt" in st.session_state:
    prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt

if prompt:
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Cevap üret
    with st.spinner("Cevaplanıyor..."):
        # Kesin kural: "Metne göre" gibi laflar yok, genel bilgi de verebilir
        system_instruction = f"""
        Sen Bursa Teknik Üniversitesi (BTÜ) Öğrenci İşleri asistanısın. 
        Sana verilen şu bilgilere göre cevap ver: {context[:25000]}
        ÖNEMLİ KURALLAR:
        1. "Belgeye göre", "Sağlanan bağlama göre" gibi ifadeleri ASLA kullanma. 
        2. Bilgileri kendin biliyormuşsun gibi doğal bir dille anlat.
        3. Eğer soru yukarıdaki bilgilerde yoksa, genel dünya bilgilerini kullanarak cevap ver (Çünkü sen her konuda bilgili bir asistansın).
        4. BTÜ ile ilgili ulaşılamayan detaylar için odb.btu.edu.tr adresine yönlendir.
        """
        
        # Senin belirttiğin model listesi (Dokunulmadı)
        selected_models = ['models/gemini-2.0-flash', 'models/gemini-flash-latest']
        response_text = ""

        for m_name in selected_models:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(f"{system_instruction}\n\nSoru: {prompt}")
                if response and response.text:
                    response_text = response.text
                    break
            except Exception:
                continue

    # Cevabı ekle ve ekrana yaz
    if response_text:
        with st.chat_message("assistant"):
            st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        # Sayfanın butonları temizlemesi için sadece bu kısımda küçük bir yenileme gerekebilir
        # ancak st.chat_input kullanıldığında streamlit bunu genelde otomatik yapar.

