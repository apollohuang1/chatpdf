import argparse
import os
import requests
import validators
import io
import requests
from requests.exceptions import HTTPError
import logging
import urllib.parse
from requests.exceptions import RequestException
import gdown
import re
import uuid
from urllib.parse import urlparse, unquote

from pypdf import PdfReader
from pypdf.errors import PdfReadError


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, '..', '..', 'data')
USER_DATA_DIR_PDF_DOWNLOADS = os.path.join(DATA_DIR, 'user_pdf_raw')


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_valid_url(url):
    return validators.url(url)

from PyPDF2 import PdfFileReader
from io import BytesIO

def is_pdf(pdf_data):
    logging.info("Checking if the downloaded file is a valid PDF...")
    try:
        if pdf_data is None or len(pdf_data.getvalue()) == 0:
            logging.error("PDF data is empty or None.")
            return False

        # Check for PDF header
        if not pdf_data.getvalue().startswith(b"%PDF"):
            logging.error("PDF data does not start with '%PDF'.")
            return False

        # Try to read the PDF with PyPDF2
        pdf_file = PdfFileReader(pdf_data)

        # Check if the PDF has any pages
        num_pages = len(pdf_file.pages)
        if num_pages == 0:
            logging.error("PDF has no pages.")
            return False

        logging.info("PDF is valid with %d pages.", num_pages)
        return True
    except (PdfReadError, ValueError) as e:
        logging.error("Error while reading PDF: %s", str(e))
        return False
    except Exception as e:
        logging.error("Unexpected error while checking PDF: %s", str(e))
        return False


def fetch_pdf(pdf_url):
    try:
        if 'drive.google.com' in pdf_url:
            # If the URL is a Google Drive URL, use gdown
            # generate a random temp id
            temp_id = str(uuid.uuid4())
            output_path = os.path.join(USER_DATA_DIR_PDF_DOWNLOADS, temp_id)
            logging.info(f"[fetch_pdf] Google Drive downloaded from {pdf_url} into {output_path}")
            gdown.download(pdf_url, output_path, quiet=False, fuzzy=True)
            with open(output_path, "rb") as f:
                return io.BytesIO(f.read()), unquote(urlparse(pdf_url).path.split("/")[-2])
        else:
            # If not, use requests as before
            response = requests.get(pdf_url, stream=True, timeout=10)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'application/pdf' not in content_type and 'application/octet-stream' not in content_type:
                logging.error(f"URL does not point to a PDF. Content-Type was: {content_type}")
                return None

            logging.info(f"[fetch_pdf] PDF downloaded from {pdf_url}")

            return io.BytesIO(response.content), unquote(urlparse(pdf_url).path.split("/")[-1])
        
    except RequestException as e:
        logging.error(f"An error occurred while downloading the PDF from {pdf_url}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error occurred while downloading the PDF from {pdf_url}: {str(e)}")
        return None


def download_pdf(pdf_url):

    # Save PDF to output path
    os.makedirs(USER_DATA_DIR_PDF_DOWNLOADS, exist_ok=True)
    
    # Download PDF        
    pdf_data, pdf_name = fetch_pdf(pdf_url)
    if not is_pdf(pdf_data):
        logging.error("The downloaded file is not a valid PDF.")
        return
    if pdf_data is None:
        logging.error(f"The URL {pdf_url} does not point to a valid PDF file.")
        return

    output_path = os.path.join(USER_DATA_DIR_PDF_DOWNLOADS, pdf_name)
    
    with open(output_path, "wb") as output_file:
        pdf_data.seek(0)
        output_file.write(pdf_data.getvalue())

    # Print success message
    logging.info(f"PDF downloaded from {pdf_url} and saved to {output_path} saved as {pdf_name}")

    # Return PDF name
    return pdf_name
