import json
import logging
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import requests
import os
import numpy as np
import pandas as pd
from pprint import pprint
import time
from dotenv import load_dotenv
from .utils import USER_DATA_DIR_PDF_DOWNLOADS
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.document_loaders import TextLoader, PyPDFLoader
from utils.utils import is_valid_url

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Set up ChromaDB client
if os.getenv("CHROMA_DEV", "True"): 
    client = chromadb.Client(Settings(
    anonymized_telemetry=False,
    ))
else:
    client = chromadb.Client(Settings(
        anonymized_telemetry=False,
        chroma_api_impl="rest",
        chroma_server_host=os.getenv("CHROMA_SERVER_HOST", "localhost"),
        chroma_server_ssl_enabled=False,
        chroma_server_http_port=8000,
    ))

# Create or get the place collection
chatpdf_collection = client.get_or_create_collection(name="chatpdf_collection")


class InvalidUrlError(Exception):
    """Exception raised when an invalid URL is provided."""

class PdfNotFoundError(Exception):
    """Exception raised when the PDF is not found."""

class QueryNoResultsError(Exception):
    """Exception raised when a query returns no results."""


def check_pdf_exists(pdf_url):
    
    # Validate URL
    if not is_valid_url(pdf_url):
        logging.error(f"Invalid URL: {pdf_url}")
        raise InvalidUrlError(f"Invalid URL: {pdf_url}")
    
    logging.info(f"[check_pdf_exists] Checking if PDF {pdf_url} exists")

    pdf_name = os.path.basename(pdf_url)

    results = chatpdf_collection.get(where={"PDF_name":pdf_name})
    logging.info(f"[check_pdf_exists] Results: {results}")
    ids = results['ids']
    logging.info(f"[check_pdf_exists] IDs length: {len(ids)}") 
    if len(ids) > 0:
        logging.info(f"PDF {pdf_name} exists, skipping download and loading")
        return True
    else:
        logging.info(f"PDF {pdf_name} does not exist")
        return False
    
def load_file(pdf_url, temp_pdf_name):
    logging.info(f"Loading file {pdf_url} as {temp_pdf_name}")
    output_path = os.path.join(USER_DATA_DIR_PDF_DOWNLOADS, temp_pdf_name)

    if not os.path.exists(output_path):
        raise FileNotFoundError(f"The file {output_path} does not exist.")
    

    loader = PyPDFLoader(output_path)
    pages = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    chunks = text_splitter.split_documents(pages)

    texts = [doc.page_content for doc in chunks]
    metadatas = [doc.metadata for doc in chunks]

    # Generate an array of IDs with the same length as texts, including the PDF name
    ids = [f"{pdf_url}_{i}" for i in range(len(texts))]

    # Add the ID to each metadata object and PDF_name
    for i, metadata in enumerate(metadatas):
        metadata["PDF_url"] = pdf_url # not clean extension
        metadata["id"] = ids[i]

    logging.info(f"[load_file] texts: {texts}")
    logging.info(f"[load_file] metadatas: {metadatas}")
    logging.info(f"[load_file] ids: {ids}")

    chatpdf_collection.add(documents=texts, metadatas=metadatas, ids=ids)
    print(ids[0])

    logging.info(f"File {pdf_url} loaded successfully")

def query_file(pdf_name, query):
    logging.info(f"[query_file] Querying file with query: {query}")
    logging.info(f"[query_file] pdf_name: {pdf_name}")
    results = chatpdf_collection.query(query_texts=[query], where={"PDF_url":pdf_name}, n_results=5)
                
    logging.info(f"Query successful")
    return results

if __name__ == "__main__":
    # Run a test query against Note11B.pdf (already downloaded)  
    load_file("Note11B.pdf")
    query = "node voltage analysis"
    results = query_file(query)
    logging.info(f"Results: {results}")
