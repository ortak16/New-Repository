import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Model Kontrolü")

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    st.write("### 📋 Kullanılabilir Modeller Listesi:")
    st.write("Eğer listede 'gemini-1.5-flash' yoksa kütüphane hala eskidir.")
    
    # Mevcut kütüphanenin gördüğü tüm modelleri listele
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
            st.code(m.name) # Örn: models/gemini-pro
            
except Exception as e:
    st.error(f"Hata: {e}")
