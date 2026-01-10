import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader


try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API Anahtarı eksik!")


def get_pdf_text(pdf_file):
    text = ""
    try:
        pdf_reader = PdfReader(pdf_file)
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content: text += content
        return text
    except:
        return ""


st.set_page_config(page_title="Destek Botu")
st.title("Bilgi Asistanı")
st.warning(" Kişisel veri paylaşmayın.")

context = ""
try:
    with open("bilgiler.pdf", "rb") as f:
        context = get_pdf_text(f)
except:
    st.error("bilgiler.pdf bulunamadı!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


if prompt := st.chat_input("Sorunuzu yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

   
    modeller = ['gemini-2.0-flash', 'gemini-1.5-flash-latest', 'gemini-pro']
    
    response = None
    success = False

    for model_adi in modeller:
        try:
            model = genai.GenerativeModel(model_adi)
            full_query = f"Bağlam: {context[:15000]}\n\nSoru: {prompt}"
            response = model.generate_content(full_query)
            success = True
            break # Çalışan modeli bulduğunda döngüden çık
        except Exception:
            continue # Hata verirse bir sonrakini dene

    if success and response:
        with st.chat_message("assistant"):
            st.write(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    else:
        st.error("Üzgünüm, şu an tüm modeller yoğun veya bölgenizde desteklenmiyor. Lütfen biraz sonra tekrar deneyin.")
