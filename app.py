import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

st.set_page_config(page_title="Hızlı Asistan", layout="centered")
st.title("Ortak Dersler Bilgi Asistanı")

try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        st.error("API Anahtarı bulunamadı! Secrets kısmını kontrol edin.")
        st.stop()
except Exception as e:
    st.error(f"Bağlantı Hatası: {e}")
    st.stop()

def get_pdf_text(pdf_file):
    text = ""
    try:
        pdf_reader = PdfReader(pdf_file)
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content: text += content
        return text
    except Exception as e:
        return f"PDF hatası: {e}"

context = ""
try:
    with open("bilgiler.pdf", "rb") as f:
        context = get_pdf_text(f)
except FileNotFoundError:
    st.info("ℹ️ Bilgi: PDF dosyası bulunamadı, genel sohbet modu aktif.")


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


if prompt := st.chat_input("Sorunuzu buraya yazın..."):
       st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    response_text = ""
    
       selected_models = ['models/gemini-2.0-flash', 'models/gemini-flash-latest']

    with st.spinner("Yazıyor..."):
        limited_context = context[:30000] if context else ""
        
           system_instruction = """
        Sen yardımsever ve samimi bir asistansın.
        Verilen bilgilere dayanarak kullanıcının sorusunu cevapla.
        ÖNEMLİ KURAL: "Sağlanan bağlama göre", "Metne göre", "Dokümanda belirtildiği gibi" gibi giriş cümlelerini ASLA kullanma.
        Sanki bu bilgileri ezbere biliyormuşsun gibi doğrudan ve doğal bir şekilde cevap ver.
        """
        
        full_prompt = f"{system_instruction}\n\nBilgiler: {limited_context}\n\nSoru: {prompt}"

   
        for m_name in selected_models:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(full_prompt)
                
                if response and response.text:
                    response_text = response.text
                    break 
            except Exception:
                continue


    if response_text:
        with st.chat_message("assistant"):
            st.write(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    else:
        st.error("⚠️ Bağlantı hatası. Tekrar deneyin.")
