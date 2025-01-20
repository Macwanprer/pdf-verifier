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
        for page_num, page in enumerate(reader.pages[:5]):  # Check first 5 pages
            text = page.extract_text().lower() if page.extract_text() else ""
            title_keywords = ["title", "contents", "abstract", "introduction"]
            if any(keyword in text for keyword in title_keywords):
                return f"Title page found on Page {page_num + 1}"
        return "No title page found"
    except Exception as e:
        return f"Error checking title page: {e}"

def check_pdf_readability(pdf_path, threshold=50):
    """Check the readability of the PDF using text extraction and OCR, return True/False and confidence."""
    try:
        # Extract text using PyPDF2
        reader = PdfReader(pdf_path)
        extracted_text = "".join(page.extract_text() or "" for page in reader.pages)
        if extracted_text.strip():
            return True, 100  # Considered readable with 100% confidence if there is any extracted text

        # Fallback to OCR for non-readable PDFs
        images = convert_from_path(pdf_path, dpi=300)
        ocr_confidences = []
        for image in images[:3]:  # Limit to first 3 pages for performance
            try:
                ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                for conf in ocr_data['conf']:
                    if conf.isdigit() and int(conf) > 0:  # Ignore invalid or zero-confidence values
                        ocr_confidences.append(int(conf))
            except Exception:
                pass

        if ocr_confidences:
            avg_confidence = sum(ocr_confidences) / len(ocr_confidences)
            return avg_confidence >= threshold, avg_confidence  # Return True if confidence is above threshold
        else:
            return False, 0  # If no OCR confidence, mark as non-readable
    except Exception as e:
        return False, 0  # In case of an error, mark as non-readable
    return False, 0

# --- Frontend (Streamlit) ---
st.set_page_config(page_title="PDF Verifier", layout="centered")

# Add a Sidebar for Instructions and Settings
with st.sidebar:
    st.header("PDF Verifier Settings")
    st.write("Upload your PDFs to check the title page and readability.")
    st.write("### OCR Settings")
    confidence_threshold = st.slider("Set OCR Confidence Threshold (%)", 0, 100, 50, 5)
    st.write(f"Current Threshold: {confidence_threshold}%")

# Main Content Area
st.title("PDF Verifier")
st.write(
    "Upload one or more PDF files to check the readability and title page status. "
    "The app will analyze the first few pages for text extraction and OCR analysis."
)

# File Upload Section
uploaded_files = st.file_uploader("Upload PDF file(s)", type="pdf", accept_multiple_files=True)

# Process uploaded files
if uploaded_files:
    results = []
    progress_bar = st.progress(0)

    for idx, uploaded_file in enumerate(uploaded_files):
        # Show Progress
        progress_bar.progress((idx + 1) / len(uploaded_files))

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(uploaded_file.read())
            temp_pdf_path = temp_pdf.name

        # Process the PDF
        title_page_status = check_title_page(temp_pdf_path)
        is_readable, confidence = check_pdf_readability(temp_pdf_path, threshold=confidence_threshold)

        # Append results
        results.append({
            "File Name": uploaded_file.name,
            "Title Page Status": title_page_status,
            "Is Readable (True/False)": "Yes" if is_readable else "No",
            "Confidence (%)": round(confidence, 2) if confidence > 0 else "N/A"
        })

        # Cleanup
        os.remove(temp_pdf_path)

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Styling the DataFrame
    def colorize_results(val):
        if val == "Yes":
            return "background-color: green; color: white;"
        elif val == "No":
            return "background-color: red; color: white;"
        return ""

    # Write results into the placeholder
    st.write("### Verification Results")
    st.dataframe(results_df.style.applymap(colorize_results, subset=["Is Readable (True/False)"]))

    # Provide a Downloadable Summary
    summary_csv = results_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Summary CSV",
        data=summary_csv,
        file_name="pdf_verification_summary.csv",
        mime="text/csv"
    )

# Footer Section
st.write("---")
st.write("This tool helps you analyze PDFs for title pages and readability. Adjust OCR settings using the sidebar.")
