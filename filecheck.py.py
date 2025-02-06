import os
import pytesseract
from PyPDF2 import PdfReader
from pdf2image import convert_from_path

# Path to Poppler's bin folder (update this to the correct path)
poppler_path = r'C:\Users\USER\Documents\prerna\poppler-24.08.0\Library\bin'

# Folder containing PDFs
folder_path = r'C:\Users\USER\Documents\prerna\pdf_noise_detection.py\data'

# Configure Tesseract-OCR path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Function to check for a title page
def check_title_page(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        for page_num, page in enumerate(reader.pages[:5]):  # Check first 5 pages
            text = page.extract_text().lower() if page.extract_text() else ""
            title_keywords = ["title", "contents", "abstract", "introduction"]
            if any(keyword in text for keyword in title_keywords):
                return f"Title page found on Page {page_num + 1}"
        return "No title page found"
    except Exception as e:
        print(f"Error checking title page for {pdf_path}: {e}")
        return "Error detecting title page"

# Function to check readability confidence
def check_pdf_readability(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        extracted_text = "".join(page.extract_text() or "" for page in reader.pages)
        if extracted_text.strip():
            return 100  # High confidence if text is found

        # Fallback to OCR
        images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
        ocr_text = ""
        ocr_confidences = []

        for image in images:
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            for conf, text in zip(ocr_data['conf'], ocr_data['text']):
                if int(conf) > 0:  # Only consider valid words with confidence > 0
                    ocr_confidences.append(int(conf))
                    ocr_text += text + " "

        if ocr_confidences:
            avg_confidence = sum(ocr_confidences) / len(ocr_confidences)
            return avg_confidence

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
    return 0

# Get list of PDF files
pdf_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]

# Analyze each PDF
results = []
readable_pdfs = []
unreadable_pdfs = []

for pdf_file in pdf_files:
    title_page_status = check_title_page(pdf_file)
    readability_confidence = check_pdf_readability(pdf_file)
    results.append((os.path.basename(pdf_file), title_page_status, readability_confidence))

    # Categorize PDFs based on readability confidence
    if readability_confidence >= 30:
        readable_pdfs.append(os.path.basename(pdf_file))
    else:
        unreadable_pdfs.append(os.path.basename(pdf_file))

# Sort results by readability confidence
results.sort(key=lambda x: x[2], reverse=True)

# Display results
print(f"{'File Name':<40} {'Title Page':<30} {'Readability Confidence'}")
print("=" * 80)
for file_name, title_page_status, confidence in results:
    print(f"{file_name:<40} {title_page_status:<30} {confidence:.2f}")

# Summary
print("\nSummary:")
print(f"Total PDFs: {len(results)}")
print(f"Readable PDFs: {len(readable_pdfs)}")
print(f"Non-Readable PDFs: {len(unreadable_pdfs)}\n")

# List readable and unreadable PDFs
print("Readable PDFs:")
for pdf in readable_pdfs:
    print(f"  - {pdf}")

print("\nNon-Readable PDFs:")
for pdf in unreadable_pdfs:
    print(f"  - {pdf}")
