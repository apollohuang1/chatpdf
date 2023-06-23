import json
import logging
import requests
import os
import numpy as np
import pandas as pd
from pprint import pprint
import time
from dotenv import load_dotenv
from .utils import USER_DATA_DIR_PDF_DOWNLOADS, USER_DATA_DIR_PDF_EMBEDDING
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader, PyPDFLoader
from utils.utils import is_valid_url
import pickle
import modal
import tiktoken

stub = modal.Stub("sheets")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

token_count = 0

class InvalidUrlError(Exception):
    """Exception raised when an invalid URL is provided."""

class PdfNotFoundError(Exception):
    """Exception raised when the PDF is not found."""

class QueryNoResultsError(Exception):
    """Exception raised when a query returns no results."""

class PdfFormatError(Exception):
    """Exception raised when we cannot parse the PDF. Maybe the text is in an image? Currently not supported."""


def num_tokens_from_texts(texts) -> int:
    # texts is an array of strings
    pdfblob = "".join(texts)
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(pdfblob))
    return num_tokens


def check_pdf_exists(pdf_url):
    
    # Validate URL
    if not is_valid_url(pdf_url):
        logging.error(f"Invalid URL: {pdf_url}")
        raise InvalidUrlError(f"Invalid URL: {pdf_url}")
    
    logging.info(f"[check_pdf_exists] Checking if PDF {pdf_url} exists")

    # Check if PDF exists as a file
    if os.path.exists(os.path.join(USER_DATA_DIR_PDF_DOWNLOADS, pdf_url)):
        logging.info(f"[check_pdf_exists] PDF {pdf_url} exists as a file")
        return True
    else:
        logging.info(f"[check_pdf_exists] PDF {pdf_url} does not exist as a file")
        return False
    
def load_file(pdf_url, temp_pdf_name):
    global token_count  # Declare the variable as global
    logging.info(f"Loading file {pdf_url} as {temp_pdf_name}")
    output_path = os.path.join(USER_DATA_DIR_PDF_DOWNLOADS, temp_pdf_name)

    if not os.path.exists(output_path):
        raise FileNotFoundError(f"The file {output_path} does not exist.")
    

    loader = PyPDFLoader(output_path)
    pages = loader.load()
    logging.info(f"[load_file] pages: {pages}")
    if pages[0].page_content == "":
        logging.info(f"[load_file] pages[0].page_content: {pages[0].page_content}")
        raise PdfFormatError("PDF has no text content that can be parsed. Maybe the text is in an image? Currently not supported.")
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=512, chunk_overlap=0
    )

    chunks = text_splitter.split_documents(pages)
    
    logging.info(f"[load_file] chunks: {chunks[0]}")

    texts = [doc.page_content for doc in chunks]
    metadatas = [doc.metadata for doc in chunks]

    # Generate an array of IDs with the same length as texts, including the PDF name
    ids = [f"{pdf_url}_{i}" for i in range(len(texts))]

    # Add the ID to each metadata object and PDF_name
    for i, metadata in enumerate(metadatas):
        metadata["PDF_url"] = pdf_url # not clean extension
        metadata["id"] = ids[i]

    
    token_count+=num_tokens_from_texts(texts)
    logging.info(f"[load_file] token_count: {token_count}")

    logging.info(f"[load_file] texts: {texts}")
    logging.info(f"[load_file] metadatas: {metadatas}")
    logging.info(f"[load_file] ids: {ids}")

    # Ensure the directory exists
    directory = os.path.dirname(os.path.join(USER_DATA_DIR_PDF_EMBEDDING, f"{pdf_url}.pkl"))
    os.makedirs(directory, exist_ok=True)

    # Picke just the texts
    with open(os.path.join(USER_DATA_DIR_PDF_EMBEDDING, f"{pdf_url}.pkl"), "wb") as f:
        pickle.dump(texts, f)

    print(ids[0])

    logging.info(f"File {pdf_url} loaded successfully")

def query_file(pdf_url, query):
    logging.info(f"[query_file] Querying file with query: {query}")
    logging.info(f"[query_file] pdf_url: {pdf_url}")

    # Load the texts
    with open(os.path.join(USER_DATA_DIR_PDF_EMBEDDING, f"{pdf_url}.pkl"), "rb") as f:
        texts = pickle.load(f)

    logging.info(f"[query_file] texts: {texts}")
    
    rembedSimilarity = modal.Function.lookup("sheets", "SentenceEmbeddings.similarity")
    results = rembedSimilarity.call(query,texts)

    logging.info(f"[query_file] results: {results}")
                
    logging.info(f"Query successful")
    return results

if __name__ == "__main__":
    # Run a test query against Note11B.pdf (already downloaded)  
    load_file("Note11B.pdf")
    query = "node voltage analysis"
    results = query_file(query)
    logging.info(f"Results: {results}")
