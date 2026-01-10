import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# ---------------------------------------------------------
# 1. AYARLAR VE TASARIM
# ---------------------------------------------------------
st.set_page_config(page_title="BTÜ Asistanı", layout="centered")

st.markdown("""
<style>
/* Gereksiz öğeleri gizle */
header, footer, .stDeployButton, [data-testid="stStatusWidget"], button[title="View fullscreen"] {
    display: none !important;
}
/* Sohbet balonları tasarımı */
[data-testid="stChatMessage"] {
    border-radius: 15px;
    margin-bottom: 10px;
    padding: 10px;
}
/* Asistan mesajı */
[data-testid="stChatMessage"]:nth-child(odd) {
    background-color: #f8f9fa;
    border-left: 4px solid #d32f2f;
}
/* Kullanıcı mesajı */
[data-testid="stChatMessage"]:nth-child(even) {
    background-color: #e3f2fd;
    border-right: 4px solid #007bff;
    flex-direction: row-reverse;
    text-align: right;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. API VE PDF YÜKLEME
# ---------------------------------------------------------

# API Anahtarı Kontrolü
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı. Lütfen secrets.toml dosyasını kontrol edin.")
    st.stop()

@st.cache_data
def load_pdf_context():
    """PDF içeriğini yükler ve metne çevirir."""
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
    except Exception as e:
        st.error(f"PDF okuma hatası: {e}")
        return ""
    return text

# PDF verisini hafızaya al
pdf_context = load_pdf_context()

# ---------------------------------------------------------
# 3. MODEL VE ZEKA AYARLARI (SİSTEM TALİMATI)
# ---------------------------------------------------------

# Modelin kişiliği ve kuralları burada belirleniyor
base_instruction = """
Sen Bursa Teknik Üniversitesi (BTÜ) Öğrenci İşleri Daire Başkanlığı'nın yapay zeka asistanısın.
Adın 'ODB Asistanı'.

GÖREVLERİN VE KURALLARIN:
1. **İnsan Gibi Konuş:** Resmiyetten uzak durma ama samimi, anlaşılır ve yardımsever bir dil kullan. Robotik cevaplar verme. "Merhaba, size nasıl yardımcı olabilirim?" gibi doğal girişler yap.
2. **Bilgi Kaynağı:**
   - Öncelikli olarak sana verilen "PDF BİLGİSİ"ni kullan.
   - Eğer kullanıcı "Nasılsın?", "Merhaba", "Python nedir?", "Hava durumu" gibi okul dışı veya genel kültür sorusu sorarsa: Kendi genel yapay zeka bilgini kullan ve güzelce cevapla. "PDF'te yok" deme.
   - Eğer kullanıcı okul prosedürleri (ders kaydı, staj vb.) hakkında "PDF BİLGİSİ" içinde OLMAYAN çok spesifik bir şey sorarsa: ASLA uydurma cevap verme. "Bu konuda şu an sistemimde güncel bilgi bulunmuyor. Yanlış yönlendirmemek adına üniversitemizin web sayfasındaki duyuruları takip etmenizi veya ilgili birimle görüşmenizi öneririm" de.
3. **Format:** Cevapları madde madde veya kısa paragraflar halinde ver ki okuması kolay olsun.

Aşağıdaki veriyi (PDF BİLGİSİ) referans al:
"""

# PDF varsa talimata ekle, yoksa boş geç
final_instruction = base_instruction
if pdf_context:
    # Modelin kafası karışmasın diye çok uzun PDF'leri kısaltıyoruz (30k karakter)
    final_instruction += f"\n--- PDF BİLGİSİ BAŞLANGICI ---\n{pdf_context[:30000]}\n--- PDF BİLGİSİ BİTİŞİ ---\n"
else:
    final_instruction += "\n(Şu an sistemde yüklü PDF verisi yok, sadece genel bilgini kullan.)\n"

@st.cache_resource
def get_model():
    # 'gemini-flash-latest' en güncel ve ücretsiz çalışan versiyondur.
    return genai.GenerativeModel(
        model_name="gemini-flash-latest",
        system_instruction=final_instruction
    )

model = get_model()

# ---------------------------------------------------------
# 4. SOHBET GEÇMİŞİ VE ARAYÜZ
# ---------------------------------------------------------

# Mesaj geçmişini başlat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Logolar
bot_avatar = "https://depo.btu.edu.tr/img/sayfa//1691132554_284ffd9ee8d6a4286478.png"
user_avatar = "👤"

# Geçmiş mesajları ekrana yazdır
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar=user_avatar):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar=bot_avatar):
            st.markdown(msg["content"])

# ---------------------------------------------------------
# 5. GİRDİ İŞLEME (Prompt Handling)
# ---------------------------------------------------------

# Kullanıcıdan girdi al (Hem input kutusu hem butonlar için mantık)
prompt = st.chat_input("Sorunuzu buraya yazın...")

# Eğer input boşsa ama butonla tetiklenmiş bir soru varsa onu al
if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt # Kullandıktan sonra sil

# Eğer bir soru varsa (Prompt doluysa)
if prompt:
    # 1. Kullanıcı mesajını ekrana ve geçmişe ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=user_avatar):
        st.markdown(prompt)

    # 2. Cevap üret
    with st.chat_message("assistant", avatar=bot_avatar):
        with st.spinner("Düşünüyorum..."):
            try:
                # Chat oturumu yerine tekli istek gönderiyoruz (hafızayı manuel yönetiyoruz)
                # Geçmiş konuşmaları da bağlam olarak ekleyebiliriz ama basitlik için şimdilik prompt'u atıyoruz.
                response = model.generate_content(prompt)
                
                if response and response.text:
                    response_text = response.text
                    st.markdown(response_text)
                    # 3. Asistan mesajını geçmişe ekle
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    st.warning("Boş cevap döndü, lütfen tekrar deneyin.")
            
            except Exception as e:
                st.error(f"Bir bağlantı hatası oluştu: {e}")

# ---------------------------------------------------------
# 6. HOŞGELDİN EKRANI VE ÖNERİ BUTONLARI
# ---------------------------------------------------------

# Sadece hiç mesaj yoksa göster
if len(st.session_state.messages) == 0:
    st.info("👋 Merhaba! Ben BTÜ Asistanıyım. Dersler, yönetmelikler veya genel konularda bana soru sorabilirsin.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Ders Kaydı"):
            st.session_state.pending_prompt = "Ders kaydı nasıl yapılır, kurallar nedir?"
            st.rerun()
            
    with col2:
        if st.button("📅 Akademik Takvim"):
            st.session_state.pending_prompt = "Akademik takvimde sınav tarihleri ne zaman?"
            st.rerun()

    with col3:
        if st.button("🤖 Yapay Zeka Nedir?"):
            st.session_state.pending_prompt = "Yapay zeka nedir, kısaca anlatır mısın?"
            st.rerun()
