import argparse
import requests
import io
import re
import logging
from utils import fetch_pdf, is_pdf, is_valid_url, USER_DATA_DIR_PDF_DOWNLOADS, download_pdf
import os
from langchain.document_loaders import PyPDFLoader


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        download_pdf(args.url)

    elif args.command == "dump":
        dump_text_from_pdf(args.pdf_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()