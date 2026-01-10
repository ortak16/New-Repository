import streamlit as st
from google import genai
from PyPDF2 import PdfReader

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API Anahtarı eksik! Lütfen Streamlit Secrets kısmını kontrol edin.")

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

st.set_page_config(page_title="Destek Asistanı", layout="centered")
st.title("Bilgi Asistanı")
st.warning("Lütfen kişisel verilerinizi paylaşmayın. Veriler işlenmektedir.")

context = ""
try:
    with open("bilgiler.pdf", "rb") as f:
        context = get_pdf_text(f)
except FileNotFoundError:
    st.error("Hata: 'bilgiler.pdf' dosyası bulunamadı!")


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


if prompt := st.chat_input("Sorunuzu buraya yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    denenecek_modeller = [
        'models/gemini-1.5-flash-latest',
        'models/gemini-1.5-flash',
        'models/gemini-pro',
        'gemini-1.5-flash'
    ]
    
    response_text = ""
    success = False


    for m_name in denenecek_modeller:
        try:
            model = genai.GenerativeModel(m_name)
            # Bağlamı çok uzun tutmamak için ilk 10.000 karakteri alalım (Hata riskini azaltır)
            full_prompt = f"Bağlam: {context[:10000]}\n\nSoru: {prompt}\n\nCevap:"
            res = model.generate_content(full_prompt)
            if res.text:
                response_text = res.text
                success = True
                break
        except Exception:
            continue

  
    if success:
        with st.chat_message("assistant"):
            st.write(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    else:
        st.error("Şu an modellerimiz cevap veremiyor. Lütfen Google AI Studio'dan yeni bir API KEY alıp denemeyi unutmayın.")

