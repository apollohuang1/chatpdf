import argparse
import os
import requests
import validators
import io
import requests
from requests.exceptions import HTTPError
import logging


from pypdf import PdfReader
from pypdf.errors import PdfReadError


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, '..', '..', 'data')
USER_DATA_DIR_PDF_DOWNLOADS = os.path.join(DATA_DIR, 'user_pdf_raw')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_valid_url(url):
    return validators.url(url)

def is_pdf(pdf_data):
    logging.info("Checking if the downloaded file is a valid PDF...")
    try:
        if pdf_data is None:
            return False
        pdf_reader = PdfReader(pdf_data)
        logging.info("num_pages: %d", len(pdf_reader.pages))
        return True
    except (PdfReadError, ValueError):
        return False
    
def fetch_pdf(pdf_url):
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('application/pdf'):
            return None

        return io.BytesIO(response.content)
    except HTTPError:
        logging.error(f"An error occurred while downloading the PDF from {pdf_url}")
        return None

def download_pdf(pdf_url):
     # Validate URL
    if not is_valid_url(pdf_url):
        logging.error(f"Invalid URL: {pdf_url}")
        return
    
    # Download PDF        
    pdf_data = fetch_pdf(pdf_url)
    if not is_pdf(pdf_data):
        logging.error("The downloaded file is not a valid PDF.")
        return
    if pdf_data is None:
        logging.error(f"The URL {pdf_url} does not point to a valid PDF file.")
        return
    
    # Save PDF to output path
    os.makedirs(USER_DATA_DIR_PDF_DOWNLOADS, exist_ok=True)
    pdf_name = os.path.basename(pdf_url)
    output_path = os.path.join(USER_DATA_DIR_PDF_DOWNLOADS, pdf_name)
    
    with open(output_path, "wb") as output_file:
        pdf_data.seek(0)
        output_file.write(pdf_data.getvalue())

    # Print success message
    logging.info(f"PDF downloaded from {pdf_url} and saved to {output_path}")

    # Return PDF name
    return pdf_name