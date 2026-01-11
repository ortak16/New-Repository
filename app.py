import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# ---------------------------------------------------------
# 1. AYARLAR VE TASARIM
# ---------------------------------------------------------
st.set_page_config(page_title="BTÜ Asistanı", layout="centered")

st.markdown("""
<style>
/* Gereksiz başlık ve footer'ı gizle */
header, footer, .stDeployButton, [data-testid="stStatusWidget"], button[title="View fullscreen"] {
    display: none !important;
}

/* Mesaj kutularının tasarımı */
[data-testid="stChatMessage"] {
    border-radius: 12px;
    margin-bottom: 10px;
    padding: 10px;
}

/* Asistan Mesajı Rengi */
[data-testid="stChatMessage"]:nth-child(odd) {
    background-color: #f9f9f9;
    border-left: 3px solid #d32f2f;
}

/* Kullanıcı Mesajı Rengi */
[data-testid="stChatMessage"]:nth-child(even) {
    background-color: #eef6fc;
    border-right: 3px solid #007bff;
    flex-direction: row-reverse;
    text-align: right;
}

/* --- LOGO KÜÇÜLTME AYARI --- */
/* Avatar boyutunu 32px'e sabitliyoruz */
[data-testid="stChatMessageAvatar"] {
    width: 32px !important;
    height: 32px !important;
}
[data-testid="stChatMessageAvatar"] img {
    width: 32px !important;
    height: 32px !important;
    object-fit: contain;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. API VE PDF İŞLEMLERİ
# ---------------------------------------------------------

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı.")
    st.stop()

@st.cache_data
def load_pdf_context():
    text = ""
    try:
        with open("bilgiler.pdf", "rb") as f:
            pdf_reader = PdfReader(f)
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except FileNotFoundError:
        return None
    except Exception:
        return ""
    return text

pdf_context = load_pdf_context()

# ---------------------------------------------------------
# 3. YAPAY ZEKA KİŞİLİĞİ (PROMPT)
# ---------------------------------------------------------

base_instruction = """
Sen Bursa Teknik Üniversitesi (BTÜ) Öğrenci İşleri asistanısın.

KONUŞMA KURALLARIN:
1. **Giriş:** Asla "Merhaba ben ODB asistanı" gibi uzun girişler yapma. Doğrudan konuya gir.
2. **Ton:** Resmiyet kasma. Bir öğrenciye yardım eden bir arkadaş gibi samimi, net ve kısa cevaplar ver.
3. **Bilgi:** - Önceliğin PDF verisi.
   - PDF'de yoksa ve soru genel kültürse (Nasılsın, Python nedir vb.) cevapla.
   - Okul prosedürüyle ilgili PDF'de bilgi yoksa uydurma, "Bu konuda net bilgi yok, duyurulara bakmalısın" de.

Aşağıdaki PDF bilgisini kullan:
"""

final_instruction = base_instruction
if pdf_context:
    final_instruction += f"\n--- PDF BAŞLA ---\n{pdf_context[:30000]}\n--- PDF BİTİR ---\n"
else:
    final_instruction += "\n(PDF yok, genel bilgini kullan.)\n"

@st.cache_resource
def get_model():
    # BURASI ÇOK ÖNEMLİ:
    # 'gemini-flash-latest' yerine 'gemini-1.5-flash' kullanıyoruz.
    # 1.5 sürümünün günlük kotası 1500 mesajdır (2.5 sürümü sadece 20 mesaj).
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash", 
        system_instruction=final_instruction
    )

model = get_model()

# ---------------------------------------------------------
# 4. SOHBET GEÇMİŞİ
# ---------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# Logolar
bot_avatar = "https://depo.btu.edu.tr/img/sayfa//1691132554_284ffd9ee8d6a4286478.png"
user_avatar = "👤"

# Ekrana Yazdırma
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar=user_avatar):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar=bot_avatar):
            st.markdown(msg["content"])

# ---------------------------------------------------------
# 5. İLETİŞİM DÖNGÜSÜ
# ---------------------------------------------------------

prompt = st.chat_input("Sorunuzu buraya yazın...")

# Buton tıklanmışsa onu prompt olarak al
if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt

if prompt:
    # 1. Kullanıcı mesajını göster
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=user_avatar):
        st.markdown(prompt)

    # 2. Asistan cevap versin
    with st.chat_message("assistant", avatar=bot_avatar):
        with st.spinner("Yazıyor..."):
            try:
                # Geçmiş konuşmaları hafıza olarak veriyoruz
                history_for_model = [
                    {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
                    for m in st.session_state.messages[:-1]
                ]
                
                chat = model.start_chat(history=history_for_model)
                response = chat.send_message(prompt)
                
                if response and response.text:
                    bot_reply = response.text
                    st.markdown(bot_reply)
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                else:
                    st.warning("Cevap alınamadı.")
            
            except Exception as e:
                # Kota hatası olursa kullanıcıya anlaşılır mesaj göster
                if "429" in str(e):
                    st.error("⚠️ Çok hızlı işlem yaptınız, lütfen 30 saniye bekleyip tekrar deneyin.")
                else:
                    st.error(f"Hata: {e}")

# ---------------------------------------------------------
# 6. BAŞLANGIÇ EKRANI
# ---------------------------------------------------------
if len(st.session_state.messages) == 0:
    st.info("👋 Selam! BTÜ hakkında merak ettiklerini sorabilirsin.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📝 Ders Kaydı"):
            st.session_state.pending_prompt = "Ders kaydı nasıl yapılır?"
            st.rerun()
    with col2:
        if st.button("📅 Sınavlar"):
            st.session_state.pending_prompt = "Sınav takvimi ne zaman?"
            st.rerun()
    with col3:
        if st.button("🎓 Staj"):
            st.session_state.pending_prompt = "Staj başvurusu nasıl olur?"
            st.rerun()
