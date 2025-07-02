import streamlit as st
from PyPDF2 import PdfReader
import openai
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import numpy as np
from gtts import gTTS
import os
import spacy
from langchain.chains import RetrievalQA
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter

# Initialisierung
nlp = spacy.load("en_core_web_sm")
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Pfad anpassen

# Streamlit UI
st.title("🔮 Intelligenter PDF Reader")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")
pdf_file = st.file_uploader("PDF hochladen", type="pdf")

if pdf_file and api_key:
    openai.api_key = api_key
    pdf_bytes = pdf_file.read()
    
    # PDF-Verarbeitung
    def extract_text(pdf_bytes):
        try:
            # Versuch Textextraktion
            with pdfplumber.open(pdf_file) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages])
            if len(text) < 100:  # OCR falls Text fehlt
                images = convert_from_bytes(pdf_bytes)
                text = "\n".join([pytesseract.image_to_string(img) for img in images])
            return text
        except:
            return "Fehler bei der Textextraktion"
    
    full_text = extract_text(pdf_bytes)
    
    # Funktionen
    def summarize_text(text):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Fasse diesen Text zusammen:\n\n{text}"}]
        )
        return response.choices[0].message['content']
    
    def answer_question(question, text):
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_text(text)
        embeddings = OpenAIEmbeddings()
        docsearch = FAISS.from_texts(texts, embeddings)
        qa = RetrievalQA.from_chain_type(
            llm=openai.ChatCompletion,
            chain_type="stuff",
            retriever=docsearch.as_retriever()
        )
        return qa.run(question)
    
    def translate_text(text, target_lang="DE"):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Übersetze ins {target_lang}:\n{text}"}]
        )
        return response.choices[0].message['content']
    
    def text_to_speech(text, lang='de'):
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save("audio.mp3")
        return "audio.mp3"
    
    def extract_key_phrases(text):
        doc = nlp(text)
        key_phrases = [chunk.text for chunk in doc.noun_chunks]
        return list(set(key_phrases))[:10]
    
    # Feature-UI
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "📝 Zusammenfassung", "❓ Frage&A", "🌐 Übersetzung", "🔊 Vorlesen",
        "🔑 Schlüsselbegriffe", "📊 Inhaltsanalyse", "💡 Konzeptextraktion",
        "📑 Autom. Glossar", "🤖 KI-Bearbeitung", "📈 Datenextraktion"
    ])
    
    with tab1:
        if st.button("Zusammenfassung erstellen"):
            summary = summarize_text(full_text[:15000])  # Kürzen für Tokenlimit
            st.write(summary)
    
    with tab2:
        question = st.text_input("Stelle eine Frage zum Dokument")
        if question:
            answer = answer_question(question, full_text)
            st.write(answer)
    
    with tab3:
        target_lang = st.selectbox("Zielsprache", ["DE", "EN", "FR", "ES"])
        if st.button("Übersetzen"):
            translation = translate_text(full_text[:5000], target_lang)
            st.write(translation)
    
    with tab4:
        if st.button("Vorlesen (erste 500 Zeichen)"):
            audio_file = text_to_speech(full_text[:500])
            st.audio(audio_file)
    
    with tab5:
        key_phrases = extract_key_phrases(full_text)
        st.write(key_phrases)
    
    with tab6:
        doc = nlp(full_text[:10000])
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        st.write(entities)
    
    with tab7:
        if st.button("Konzepte extrahieren"):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"Extrahiere Hauptkonzepte:\n{full_text[:10000]}"}]
            )
            st.write(response.choices[0].message['content'])
    
    with tab8:
        if st.button("Glossar generieren"):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"Erstelle Fachbegriff-Glossar:\n{full_text[:10000]}"}]
            )
            st.write(response.choices[0].message['content'])
    
    with tab9:
        edit_instruction = st.text_area("Bearbeitungsanweisung")
        if st.button("Dokument bearbeiten"):
            edited = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"Bearbeite nach Anweisung:\nAnweisung:{edit_instruction}\nText:{full_text[:5000]}"}]
            )
            st.write(edited.choices[0].message['content'])
    
    with tab10:
        if st.button("Tabellen extrahieren"):
            with pdfplumber.open(pdf_file) as pdf:
                for i, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for table in tables:
                        st.write(f"Tabelle auf Seite {i+1}:")
                        st.table(table)
else:
    st.warning("Bitte laden Sie eine PDF-Datei hoch und geben Sie einen OpenAI API Key ein")