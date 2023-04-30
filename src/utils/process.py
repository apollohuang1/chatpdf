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
from utils import download_pdf, is_pdf, is_valid_url, USER_DATA_DIR_PDF_DOWNLOADS
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

persist_directory = 'user_pdf_embeddings'

embedding = OpenAIEmbeddings()

db = Chroma(collection_name="chatpdf_collection", client_settings=chroma_settings, persist_directory=persist_directory)

# docsearch = vectorstore.from_documents(webpage, embeddings, collection_name="webpage")

def load_file(pdf_path):
    output_path = os.path.join(USER_DATA_DIR_PDF_DOWNLOADS, pdf_path)
    loader = PyPDFLoader(output_path)
    pages = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    chunks = text_splitter.split_documents(pages)
    vectordb = db.from_documents(documents=chunks, embedding=embedding)
    vectordb.persist()

def query_file(query):
    return db.similarity_search_with_score(query)

