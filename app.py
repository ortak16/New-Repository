import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Hata Ayıklama Modu")

st.title("🛠️ Sistem Kontrolü")

# 1. API Anahtarı Kontrolü
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ API Anahtarı (GOOGLE_API_KEY) secrets içinde bulunamadı!")
    st.stop()
else:
    st.success(f"✅ API Anahtarı bulundu (Son 4 hane: ...{api_key[-4:]})")

# 2. Bağlantı Kurma
try:
    genai.configure(api_key=api_key)
    st.write("✅ Konfigürasyon yapıldı.")
except Exception as e:
    st.error(f"❌ Konfigürasyon Hatası: {e}")
    st.stop()

# 3. Model Testi
if st.button("Test Mesajı Gönder"):
    try:
        # Daha güvenli olan 1.5-flash modelini deniyoruz
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        with st.spinner("Google'a bağlanılıyor..."):
            response = model.generate_content("Merhaba, test yapıyorum.")
            
        if response and response.text:
            st.success("🎉 BAŞARILI! Cevap geldi:")
            st.info(response.text)
        else:
            st.warning("Cevap boş döndü.")
            
    except Exception as e:
        st.error("💥 KRİTİK HATA OLUŞTU:")
        st.code(str(e)) # Hatayı tam olarak ekrana yazar
