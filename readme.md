# chatwithpdf
ChatWithPDF is a ChatGPT plugin that allows users to do Q/A with any PDF online.

## Usage
Interact with ChatPDF by installing this URL into the ChatGPT plugin interface: **chatwithpdf.sdan.io**

First load up the PDF (either enter "load <publically_accessible_pdf_url>" or you can load it when asking the question)

- "Search for the definition of machine learning in the PDF"
- "Find the section about data preprocessing in the document"
- "List the advantages of deep learning from the PDF"
- "What are the main points in the executive summary?"
- "Locate the results of the experiment in the paper"

## Overview
We store your PDFs temporarily, embed them on runtime, and do cosine similary to find relevant chunks within the parsed PDF document and feed that back into ChatGPT to spin up a relevant answer just from the PDF

## Features
- Load and process PDF documents from a temporary URL
- Semantic search within PDF documents
- Extracts relevant information from the document based on user queries
- No installation required. Just add **chatwithpdf.sdan.io** as an unverified plugin on ChatGPT's UI

## How it works
- Users provide a temporary PDF URL to be loaded and processed
- The plugin downloads and processes the PDF document, extracting relevant information
- User queries are matched with the processed information from the PDF
- The most relevant matches are returned to ChatGPT to spin up a relevant answer

Enjoy efficient PDF document processing and searching with the ChatWithPDF plugin!