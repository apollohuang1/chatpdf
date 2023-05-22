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
from urllib.parse import urlparse, unquote, parse_qs


from pypdf import PdfReader
from pypdf.errors import PdfReadError


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, '..', '..', 'data')
USER_DATA_DIR_PDF_DOWNLOADS = os.path.join(DATA_DIR, 'user_pdf_raw')


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PdfFetchError(Exception):
    """Exception raised when there is an error fetching the PDF."""

class PdfInvalidError(Exception):
    """Exception raised when the PDF is invalid."""
    
class NotAPdfError(Exception):
    pass

def is_valid_url(url):
    return validators.url(url)

from PyPDF2 import PdfFileReader
from io import BytesIO

def is_pdf(pdf_data):
    logging.info("Checking if the downloaded file is a valid PDF...")
    if pdf_data is None or len(pdf_data.getvalue()) == 0:
        raise PdfInvalidError("PDF data is empty or None.")

    # Check for PDF header
    if not pdf_data.getvalue().startswith(b"%PDF"):
        raise PdfInvalidError("PDF data does not start with '%PDF'.")

    # Try to read the PDF with PyPDF2
    try:
        pdf_file = PdfFileReader(pdf_data)
    except (PdfReadError, ValueError) as e:
        raise PdfInvalidError(f"Error while reading PDF: {str(e)}")
    except Exception as e:
        raise PdfInvalidError(f"Unexpected error while checking PDF: {str(e)}")

    # Check if the PDF has any pages
    num_pages = len(pdf_file.pages)
    if num_pages == 0:
        raise PdfInvalidError("PDF has no pages.")
    
    if num_pages > 250:
        logging.warning("PDF has more than 250 pages. Only the first page will be used.")

    logging.info("PDF is valid with %d pages.", num_pages)
    return True


def fetch_pdf(pdf_url):
    try:
        if 'drive.google.com' in pdf_url:
            # If the URL is a Google Drive URL, use gdown
            # generate a random temp id
            temp_id = str(uuid.uuid4())
            output_path = os.path.join(USER_DATA_DIR_PDF_DOWNLOADS, temp_id)
            logging.info(f"[fetch_pdf] Google Drive downloaded from {pdf_url} into {output_path}")

            try:
                gdown.download(pdf_url, output_path, quiet=False, fuzzy=True)
                with open(output_path, "rb") as f:
                    return io.BytesIO(f.read())
            except Exception as e:
                logging.error(f"[fetch_pdf] Failed to download from Google Drive: {pdf_url}. Error: {e}")
                raise Exception(f"Failed to download file from Google Drive. Error: <> Maybe check if the file is shared publicly?")

        else:
            # If not, use requests as before
            response = requests.get(pdf_url, stream=True, timeout=10)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'application/pdf' not in content_type and 'application/octet-stream' not in content_type:
                logging.error(f"URL does not point to a PDF. Content-Type was: {content_type}")
                raise NotAPdfError(f"URL does not point to a PDF. Content-Type was: {content_type}")
            
            logging.info(f"[fetch_pdf] PDF downloaded from {pdf_url}")

            # Hardcoded PDF name
            if 'openreview.net' in pdf_url:
                return io.BytesIO(response.content)

            return io.BytesIO(response.content)
        
    except RequestException as e:
        logging.error(f"An error occurred while downloading the PDF from {pdf_url}: {str(e)}")
        raise PdfFetchError(f"An error occurred while downloading the PDF from {pdf_url}: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error occurred while downloading the PDF from {pdf_url}: {str(e)}")
        raise PdfFetchError(f"Unexpected error occurred while downloading the PDF from {pdf_url}: {str(e)}")

def download_pdf(pdf_url):
    # Save PDF to output path
    os.makedirs(USER_DATA_DIR_PDF_DOWNLOADS, exist_ok=True)

    # Download PDF logic...
    try:
        pdf_data = fetch_pdf(pdf_url)
        is_pdf(pdf_data)
    except PdfFetchError as e:
        logging.error(f"[download_pdf] PdfFetchError occurred while downloading PDF: {e}")
        raise
    except PdfInvalidError as e:
        logging.error(f"[download_pdf] PdfInvalidError occurred while downloading PDF: {e}")
        raise
    except Exception as e:
        logging.error(f"[download_pdf] An unknown error occurred while downloading PDF: {e}")
        raise

    # Generate random PDF name
    pdf_name = str(uuid.uuid4()) + ".pdf"

    output_path = os.path.join(USER_DATA_DIR_PDF_DOWNLOADS, pdf_name)
    
    with open(output_path, "wb") as output_file:
        pdf_data.seek(0)
        output_file.write(pdf_data.getvalue())

    # Print success message
    logging.info(f"PDF downloaded from {pdf_url} and saved to {output_path} saved as {pdf_name}")

    # Return PDF name
    return pdf_name

