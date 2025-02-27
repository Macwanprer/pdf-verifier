import os
import pytesseract
import streamlit as st
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pandas as pd
import tempfile

# --- Configure Tesseract-OCR Path Dynamically ---
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:
    pytesseract.pytesseract_cmd = 'tesseract'

# --- Backend Functions ---
def check_title_page(pdf_path):
    """Check if the PDF contains a title page based on keywords."""
    try:
        reader = PdfReader(pdf_path)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text().lower() if page.extract_text() else ""
            title_keywords = ["title", "contents", "abstract", "introduction"]
            if any(keyword in text for keyword in title_keywords):
                return f"Title page found on Page {page_num + 1}"
        return "No title page found"
    except Exception as e:
        return f"Error checking title page: {e}"

def check_pdf_readability(pdf_path, threshold=50, handwriting=False, language='eng'):
    """Check the readability of the PDF using text extraction and OCR, with optional handwriting detection."""
    try:
        reader = PdfReader(pdf_path)
        extracted_text = "".join(page.extract_text() or "" for page in reader.pages)
        if extracted_text.strip():
            return True, 100

        images = convert_from_path(pdf_path, dpi=300)
        ocr_confidences = []

        for image in images:
            try:
                if handwriting:
                    ocr_text = pytesseract.image_to_string(image, lang=language)
                else:
                    ocr_data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
                    for conf in ocr_data['conf']:
                        if isinstance(conf, int) and conf > 0:
                            ocr_confidences.append(conf)
            except Exception:
                pass

        if ocr_confidences:
            avg_confidence = sum(ocr_confidences) / len(ocr_confidences)
            return avg_confidence >= threshold, round(avg_confidence, 2)
        else:
            return False, 0
    except Exception:
        return False, 0

def check_duplicate_files(uploaded_files):
    """Check if files are uploaded more than once."""
    file_names = [file.name for file in uploaded_files]
    duplicates = {name for name in file_names if file_names.count(name) > 1}
    return duplicates

def check_file_format(uploaded_file):
    """Ensure the uploaded file is a valid PDF."""
    return uploaded_file.name.lower().endswith('.pdf')

def save_temp_pdf(uploaded_file):
    """Save uploaded file temporarily."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(uploaded_file.read())
        return temp_pdf.name

# --- Frontend (Streamlit) ---
st.set_page_config(page_title="PDF Verifier", layout="centered")

with st.sidebar:
    st.header("PDF Verifier Settings")
    st.write("Upload your PDFs to check the title page and readability.")
    confidence_threshold = st.slider("Set OCR Confidence Threshold (%)", 0, 100, 50, 5)
    st.write(f"Current Threshold: {confidence_threshold}%")
    handwriting_option = st.checkbox("Enable Handwritten Text Recognition")
    language_option = st.selectbox("Select OCR Language", ["eng", "spa", "fra", "deu", "ita", "jpn", "chi_sim", "chi_tra"])

st.title("PDF Verifier")
st.write("Upload PDF files to check readability, duplicate uploads, and title page status.")

st.markdown("""
    <style>
        .stFileUploader { border: 2px dashed #ccc; padding: 20px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader("Upload PDF file(s)", type="pdf", accept_multiple_files=True)

if uploaded_files:
    duplicate_files = check_duplicate_files(uploaded_files)
    results = []
    progress_bar = st.progress(0)

    for idx, uploaded_file in enumerate(uploaded_files):
        progress_bar.progress((idx + 1) / len(uploaded_files))
        
        if not check_file_format(uploaded_file):
            results.append({"File Name": uploaded_file.name, "Error": "Invalid file format"})
            continue
        
        temp_pdf_path = save_temp_pdf(uploaded_file)
        title_page_status = check_title_page(temp_pdf_path)
        is_readable, confidence = check_pdf_readability(temp_pdf_path, threshold=confidence_threshold, handwriting=handwriting_option, language=language_option)

        results.append({
            "File Name": uploaded_file.name,
            "Duplicate File": "Yes" if uploaded_file.name in duplicate_files else "No",
            "Title Page Status": title_page_status,
            "Is Readable (True/False)": "Yes" if is_readable else "No",
            "Confidence (%)": f"{round(confidence, 2)}%"
        })

        os.remove(temp_pdf_path)

    results_df = pd.DataFrame(results)

    def colorize_results(val):
        if val == "Yes":
            return "background-color: green; color: white;"
        elif val == "No":
            return "background-color: red; color: white;"
        return ""

    st.write("### Verification Results")
    st.dataframe(results_df.style.applymap(colorize_results, subset=["Is Readable (True/False)"]))

    summary_csv = results_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Summary CSV",
        data=summary_csv,
        file_name="pdf_verification_summary.csv",
        mime="text/csv"
    )

st.write("---")
st.write("PDF Verifier Tool")
