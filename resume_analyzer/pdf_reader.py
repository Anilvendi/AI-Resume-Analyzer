import streamlit as st
from pypdf import PdfReader


@st.cache_data(show_spinner="📄 Reading your resume...")
def extract_text(uploaded_file):
    """
    Extract text from an uploaded PDF file.

    Parameters:
        uploaded_file : Streamlit uploaded PDF

    Returns:
        String containing the complete resume text.
    """

    try:

        reader = PdfReader(uploaded_file)

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:

                text += page_text + "\n"

        return text

    except Exception as e:

        return f"Error: {e}"