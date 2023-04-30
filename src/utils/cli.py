import argparse
import requests
import io
import re
import logging
from utils import download_pdf, is_pdf, is_valid_url, USER_DATA_DIR_PDF_DOWNLOADS
import os
from langchain.document_loaders import PyPDFLoader


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_from_pdf(file_path):
    logging.info(f"Extracting text from {file_path}")
    return "text"

def dump_text_from_pdf(pdf_path):
    logging.info(f"Dumping text from {pdf_path}")
    output_path = os.path.join(USER_DATA_DIR_PDF_DOWNLOADS, pdf_path)
    loader = PyPDFLoader(output_path)
    pages = loader.load_and_split()
    # loop over all pages and print the text
    for page in pages:
        logging.info(page.page_content)
    # number of pages
    logging.info(f"Number of pages: {len(pages)}")
    return pages

def main():
    parser = argparse.ArgumentParser(description="Search or ask questions against a PDF and insert a PDF via a link.")
    subparsers = parser.add_subparsers(dest="command")

    # Download PDF command
    download_parser = subparsers.add_parser("download", help="Download a PDF from a given URL")
    download_parser.add_argument("url", type=str, help="URL of the PDF file")

    # Dump command
    dump_parser = subparsers.add_parser("dump", help="Dump a PDF to text")
    dump_parser.add_argument("pdf_path", type=str, help="Path to the PDF file")

    args = parser.parse_args()

    if args.command == "download":
        # Validate URL
        if not is_valid_url(args.url):
            logging.error(f"Invalid URL: {args.url}")
            return
        
        # Download PDF        
        pdf_data = download_pdf(args.url)
        if not is_pdf(pdf_data):
            logging.error("The downloaded file is not a valid PDF.")
            return
        if pdf_data is None:
            logging.error(f"The URL {args.url} does not point to a valid PDF file.")
            return
        
        # Save PDF to output path
        os.makedirs(USER_DATA_DIR_PDF_DOWNLOADS, exist_ok=True)
        pdf_name = os.path.basename(args.url)
        output_path = os.path.join(USER_DATA_DIR_PDF_DOWNLOADS, pdf_name)
        
        with open(output_path, "wb") as output_file:
            pdf_data.seek(0)
            output_file.write(pdf_data.getvalue())

        # Print success message
        logging.info(f"PDF downloaded from {args.url} and saved to {output_path}")

    elif args.command == "dump":
        dump_text_from_pdf(args.pdf_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()