import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("Hata: API Anahtarı bulunamadı veya geçersiz!")


def get_pdf_text(pdf_file):
    try:
        text = ""
        pdf_reader = PdfReader(pdf_file)
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content:
                text += content
        return text
    except Exception as e:
        return f"PDF okuma hatası: {e}"

st.set_page_config(page_title="Destek Botu", layout="centered")

st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>""", unsafe_allow_html=True)

st.title("🤖 Bilgi Asistanı")
st.warning("⚠️ Kişisel veri paylaşmayın, veriler işlenmektedir.")

context = ""
try:
    with open("bilgiler.pdf", "rb") as f:
        context = get_pdf_text(f)
except FileNotFoundError:
    st.error("Hata: 'bilgiler.pdf' dosyası bulunamadı!")


with st.sidebar:
    st.info("💡 Örnek Sorular:\n1. Ders açmak istiyorum?\n2. Çalışma saatleriniz neler?\n3. İletişim bilgileriniz nedir?")


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt := st.chat_input("Sorunuzu buraya yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        
        full_query = f"Sana bir döküman metni vereceğim. Sadece bu metne dayanarak cevap ver. Metin: {context[:15000]}\n\nSoru: {prompt}"
        
        response = model.generate_content(full_query)
        
        if response.text:
            with st.chat_message("assistant"):
                st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        else:
            st.error("Bot cevap üretemedi, lütfen tekrar deneyin.")
            
    except Exception as e:
        
        st.error(f"Bir sorun oluştu: {str(e)}")
        st.info("Lütfen 30 saniye sonra tekrar deneyin (Kota dolmuş olabilir).")
