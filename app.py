import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Model Dedektifi")
st.title("🕵️ Model Bulucu")

try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        st.info(f"Anahtar ile bağlantı kuruldu. Kullanılabilir modeller aranıyor...")
        
        # Google'dan modelleri iste
        available_models = []
        for m in genai.list_models():
            # Sadece içerik üretebilen (chat) modelleri al
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if available_models:
            st.success(f"✅ Bulunan Modeller ({len(available_models)} adet):")
            # Listeyi ekrana bas
            st.json(available_models)
            
            st.write("---")
            st.write("👇 **Çözüm:** Aşağıdaki test kutusuna listedeki isimlerden birini (örn: `models/gemini-pro`) yazıp deneyin.")
            
            selected_model = st.selectbox("Bir model seçip test et:", available_models)
            
            if st.button("Seçili Modeli Test Et"):
                try:
                    model = genai.GenerativeModel(selected_model)
                    res = model.generate_content("Merhaba, çalışıyor musun?")
                    st.success(f"Cevap: {res.text}")
                except Exception as e:
                    st.error(f"Hata: {e}")

        else:
            st.warning("⚠️ Bağlantı başarılı ama 'generateContent' destekleyen model bulunamadı.")
            
    else:
        st.error("API Key bulunamadı.")
        
except Exception as e:
    st.error(f"Listeleme Hatası: {str(e)}")
