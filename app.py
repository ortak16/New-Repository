import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Hata Ayıklama", layout="centered")
st.title("🔍 Hata Tespit Ekranı")

# 1. ADIM: API Anahtarı Kontrolü
st.subheader("1. API Anahtarı Kontrolü")
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        # Güvenlik için sadece ilk 4 ve son 4 karakteri gösterelim
        visible_key = f"{api_key[:4]}...{api_key[-4:]}"
        st.success(f"✅ API Anahtarı Algılandı: {visible_key}")
        
        # Yapılandırma
        genai.configure(api_key=api_key)
    else:
        st.error("❌ HATA: Streamlit Secrets içinde 'GOOGLE_API_KEY' bulunamadı!")
        st.stop()
except Exception as e:
    st.error(f"❌ Anahtar okunurken hata: {e}")
    st.stop()

# 2. ADIM: Bağlantı Testi
st.subheader("2. Google Sunucusuna Bağlantı Testi")
try:
    # En temel modeli deneyelim
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    with st.spinner("Google'a 'Merhaba' deniliyor..."):
        response = model.generate_content("Merhaba, bağlantı testi yapıyorum.")
        
    if response and response.text:
        st.success("✅ BAŞARILI! Model Cevap Verdi:")
        st.info(response.text)
    else:
        st.warning("⚠️ Model boş cevap döndü.")

except Exception as e:
    st.error("❌ KRİTİK HATA OLUŞTU:")
    st.code(str(e), language="python")
    
    st.markdown("""
    **Olası Sebepler:**
    1. **403 Permission Denied:** API Anahtarı hatalı kopyalanmış (boşluk olabilir).
    2. **404 Not Found:** Model ismi yanlış veya hesabınızda aktif değil.
    3. **400 Invalid Argument:** API anahtarı yetkisi yok.
    """)
