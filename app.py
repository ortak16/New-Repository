import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="BTÜ Öğrenci İşleri Asistanı", layout="centered")

# Manage App ve diğer Streamlit öğelerini gizle (CSS ile)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 BTÜ Öğrenci İşleri Asistanı")

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

# --- 3. PDF OKUMA VE BAĞLAM ---
@st.cache_data # PDF'i her seferinde okuyup yavaşlatmaması için önbelleğe alıyoruz
def get_pdf_text(pdf_file_path):
    text = ""
    try:
        with open(pdf_file_path, "rb") as f:
            pdf_reader = PdfReader(f)
            for page in pdf_reader.pages:
                content = page.extract_text()
                if content: text += content
        return text
    except:
        return ""

context = get_pdf_text("bilgiler.pdf")

# --- 4. SOHBET GEÇMİŞİ VE ÖNERİLER ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Karşılama mesajı ve öneri butonları
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.write("Merhaba! Ben BTÜ Öğrenci İşleri Asistanıyım. Size nasıl yardımcı olabilirim?")
        st.write("Sıkça sorulan bazı sorular:")
        
        # Öneri Butonları
        c1, c2 = st.columns(2)
        if c1.button("📑 Bölümümde ders açmak istiyorum?"):
            st.session_state.pending_prompt = "Bölümümde ders açmak istiyorum, ne yapmalıyım?"
        if c2.button("📅 Kısa sınav tarihlerini öğrenme?"):
            st.session_state.pending_prompt = "Kısa sınav tarihimi nasıl öğrenebilirim?"
        
        c3, c4 = st.columns(2)
        if c3.button("🎓 Mezuniyet şartları neler?"):
            st.session_state.pending_prompt = "Mezuniyet şartları nelerdir?"
        if c4.button("🌍 Genel bir soru sor"):
            st.session_state.pending_prompt = "Merhaba, genel bir sorum var."

# Eski mesajları ekrana bas
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. SOHBET MANTIĞI ---
# Eğer butonla bir soru geldiyse veya kullanıcı yazdıysa
prompt = st.chat_input("Sorunuzu buraya yazın...")
if hasattr(st.session_state, 'pending_prompt'):
    prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Düşünüyorum..."):
        # Sistem Talimatı: Hem PDF'i hem genel bilgiyi kullanacak şekilde revize edildi
        system_instruction = f"""
        Sen Bursa Teknik Üniversitesi (BTÜ) Öğrenci İşleri Daire Başkanlığı için özelleşmiş bir asistansın.
        
        KURALLAR:
        1. Eğer soru kurumun iç işleyişi (ders açma, sınavlar, yönetmelik vb.) ile ilgiliyse önce şu bilgilere bak: {context[:25000]}
        2. Eğer soru genel kültür, tarih, teknoloji veya BTÜ dışı bir konuysa kendi genel bilgilerini kullanarak cevap ver.
        3. Cevapların doğal olsun. ASLA "belgelere göre", "bağlamda yazdığı gibi" deme. 
        4. Samimi ama resmi bir dil kullan (BTÜ personeli gibi).
        5. Eğer PDF'te bilgi yoksa ve konu BTÜ ile ilgiliyse 'Bu konuda detaylı bilgi için odb.btu.edu.tr adresini ziyaret edebilir veya ilgili birimle iletişime geçebilirsiniz' de.
        """

        selected_models = ['models/gemini-2.0-flash', 'models/gemini-1.5-flash-latest']
        response_text = ""

        for m_name in selected_models:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(f"{system_instruction}\n\nKullanıcı Sorusu: {prompt}")
                if response and response.text:
                    response_text = response.text
                    break
            except:
                continue

    if response_text:
        with st.chat_message("assistant"):
            st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        # Sayfayı butonların gitmesi için yenile
        st.rerun()
