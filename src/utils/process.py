import json
import logging
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import openai
import requests
import os
import numpy as np
import pandas as pd
from pprint import pprint
import time
from dotenv import load_dotenv
from .utils import USER_DATA_DIR_PDF_DOWNLOADS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.document_loaders import TextLoader, PyPDFLoader


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# API Keys
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

# Set up ChromaDB client
chroma_settings = Settings(
    chroma_api_impl="rest",
    chroma_server_host=os.getenv("CHROMA_SERVER_HOST", "localhost"),
    chroma_server_ssl_enabled=True,
    chroma_server_http_port=443,
    chroma_db_impl="duckdb+parquet",
)

# persist_directory = 'user_pdf_embeddings'

# db = Chroma(collection_name="chatpdf_collection", client_settings=chroma_settings, persist_directory=persist_directory)

# Set up ChromaDB client
# client = chromadb.Client(Settings(
#     anonymized_telemetry=False,
#     chroma_api_impl="rest",
#     chroma_server_host=os.getenv("CHROMA_SERVER_HOST", "localhost"),
#     chroma_server_ssl_enabled=True,
#     chroma_server_http_port=443,
#     chroma_db_impl="duckdb+parquet",
# ))
client = chromadb.Client(Settings(
    anonymized_telemetry=False,
))


# Set up embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-ada-002"
)

# Create or get the place collection
chatpdf_collection = client.get_or_create_collection(name="chatpdf_collection", embedding_function=openai_ef)

def load_file(pdf_path):
    logging.info(f"Loading file {pdf_path}")
    output_path = os.path.join(USER_DATA_DIR_PDF_DOWNLOADS, pdf_path)
    loader = PyPDFLoader(output_path)
    pages = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    chunks = text_splitter.split_documents(pages)

    texts = [doc.page_content for doc in chunks]
    metadatas = [doc.metadata for doc in chunks]

    # Extract the PDF name without the extension
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

    # Generate an array of IDs with the same length as texts, including the PDF name
    ids = [f"{pdf_name}_{i}" for i in range(len(texts))]

    # Add the ID to each metadata object and PDF_name
    for i, metadata in enumerate(metadatas):
        metadata["PDF_name"] = pdf_name
        metadata["id"] = ids[i]

    logging.info(f"[load_file] texts: {texts}")
    logging.info(f"[load_file] metadatas: {metadatas}")
    logging.info(f"[load_file] ids: {ids}")

    chatpdf_collection.add(documents=texts, metadatas=metadatas, ids=ids)

    logging.info(f"File {pdf_path} loaded successfully")

def query_file(pdf_name, query):
    # Strip .pdf extension from pdf_name
    pdf_name = os.path.splitext(pdf_name)[0]
    logging.info(f"[query_file] Querying file with query: {query}")
    logging.info(f"[query_file] pdf_name: {pdf_name}")
    results = chatpdf_collection.query(query_texts=[query], where={"PDF_name":pdf_name}, n_results=5)
    logging.info(f"Query successful")
    return results

if __name__ == "__main__":
    # Run a test query against Note11B.pdf (already downloaded)  
    load_file("Note11B.pdf")
    query = "node voltage analysis"
    results = query_file(query)
    logging.info(f"Results: {results}")