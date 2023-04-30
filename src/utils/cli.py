import argparse
import requests
import io
import re
import logging
from utils import download_pdf, is_pdf, is_valid_url, USER_DATA_DIR_PDF_DOWNLOADS
import os
import PyPDF2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_from_pdf(file_path):
    logging.info(f"Extracting text from {file_path}")
    return "text"

def search_pdf(file_path, query):
    logging.info(f"Searching {file_path} for {query}")
    text = extract_text_from_pdf(file_path)
    matches = re.findall(query, text, flags=re.IGNORECASE)
    return matches

def main():
    parser = argparse.ArgumentParser(description="Search or ask questions against a PDF and insert a PDF via a link.")
    subparsers = parser.add_subparsers(dest="command")

    # Download PDF command
    download_parser = subparsers.add_parser("download", help="Download a PDF from a given URL")
    download_parser.add_argument("url", type=str, help="URL of the PDF file")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search a PDF for a given query")
    search_parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
    search_parser.add_argument("query", type=str, help="Search query")

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

    elif args.command == "search":
        matches = search_pdf(args.pdf_path, args.query)
        logging.info(f"Found {len(matches)} matches for the query '{args.query}':")
        for idx, match in enumerate(matches, 1):
            logging.info(f"{idx}. {match}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()


