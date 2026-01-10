import streamlit as st
from google import genai
from PyPDF2 import PdfReader

# Sayfa ayarları en başta olmalı
st.set_page_config(page_title="Destek Asistanı", layout="centered")

# --- API ANAHTARI VE İSTEMCİ KURULUMU (YENİ SİSTEM) ---
client = None
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        # Yeni kütüphanede configure yerine Client oluşturulur
        client = genai.Client(api_key=api_key)
    else:
        st.error("API Anahtarı bulunamadı! Lütfen Streamlit Secrets kısmına 'GOOGLE_API_KEY' ekleyin.")
except Exception as e:
    st.error(f"Bağlantı Hatası: {str(e)}")

# --- FONKSİYONLAR ---
def get_pdf_text(pdf_file):
    text = ""
    try:
        pdf_reader = PdfReader(pdf_file)
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content: text += content
        return text
    except Exception as e:
        return f"PDF Okuma Hatası: {str(e)}"

# --- ARAYÜZ ---
st.title("Bilgi Asistanı")
st.warning("Lütfen kişisel verilerinizi paylaşmayın. Veriler işlenmektedir.")

# PDF Yükleme / Okuma
context = ""
try:
    # Eğer dosya yüklü değilse hata vermemesi için kontrol
    with open("bilgiler.pdf", "rb") as f:
        context = get_pdf_text(f)
except FileNotFoundError:
    st.error("Hata: 'bilgiler.pdf' dosyası ana dizinde bulunamadı! Dosyayı yüklediğinizden emin olun.")

# Mesaj Geçmişi
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- SOHBET MANTIĞI ---
if prompt := st.chat_input("Sorunuzu buraya yazın..."):
    if not client:
        st.error("API anahtarı olmadığı için işlem yapılamıyor.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Yeni kütüphane model isimleri (genelde 'models/' öneki olmadan çalışır ama ikisi de olur)
    denenecek_modeller = [
        'gemini-1.5-flash',
        'gemini-2.0-flash-exp', # Varsa yeni hızlı model
        'gemini-1.5-pro'
    ]
    
    response_text = ""
    success = False

    with st.spinner("Yanıt üretiliyor..."):
        for m_name in denenecek_modeller:
            try:
                # Bağlamı kısaltıyoruz (Token limitini aşmamak için)
                limited_context = context[:20000] if context else "Bağlam yok."
                
                # Yeni SDK Kullanımı: client.models.generate_content
                response = client.models.generate_content(
                    model=m_name,
                    contents=f"Aşağıdaki metne göre cevapla.\n\nBağlam: {limited_context}\n\nSoru: {prompt}"
                )
                
                if response.text:
                    response_text = response.text
                    success = True
                    break # Başarılı olursa döngüden çık
            except Exception as e:
                # Hata alırsak diğer modele geç, loglara yaz
                print(f"Model {m_name} hata verdi: {e}")
                continue

    if success:
        with st.chat_message("assistant"):
            st.write(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    else:
        st.error("Üzgünüm, şu an modeller yanıt veremiyor veya kota dolmuş olabilir. API Key'inizi ve kotanızı kontrol edin.")
