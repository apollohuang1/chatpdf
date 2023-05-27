from flask import Flask, request, Response, send_file, render_template, render_template_string, session
from flask_cors import CORS
from utils.utils import download_pdf
from utils.process import load_file, query_file, check_pdf_exists
from werkzeug.exceptions import BadRequest
import os
import logging
from dotenv import load_dotenv
import json
import uuid
from threading import Thread


load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")
CORS(app)

class InvalidUrlError(Exception):
    """Exception raised when an invalid URL is provided."""

class PdfNotFoundError(Exception):
    """Exception raised when the PDF is not found."""

class QueryNoResultsError(Exception):
    """Exception raised when a query returns no results."""

class PdfFetchError(Exception):
    """Exception raised when there is an error fetching the PDF."""

class PdfInvalidError(Exception):
    """Exception raised when the PDF is invalid."""

class PdfFormatError(Exception):
    """Exception raised when we cannot parse the PDF. Maybe the text is in an image? Currently not supported."""


@app.route("/pdf/load", methods=['POST'])
def load_pdf():
    try:
        data = request.get_json(force=True)
        logging.info(f"[load_pdf] Data: {data}")
        pdf_url = data["pdf_url"]

        if check_pdf_exists(pdf_url):
            logging.info(f"[load_pdf] PDF {pdf_url} already exists, skipping download and loading")
            return Response(response=json.dumps({"status": "success"}), status=200)
        else :
            logging.info(f"[load_pdf] PDF {pdf_url} does not exist, downloading and loading")
            
            logging.info(f"[load_pdf] Downloading PDF from URL: {pdf_url}")
            pdf_name, time_to_load = download_pdf(pdf_url)

            logging.info(f"[load_pdf] Downloaded PDF {pdf_url} as {pdf_name} in {time_to_load} seconds")

            # if less than 20 seconds, load the file
            if time_to_load < 20:
                logging.info(f"[load_pdf] Loading PDF {pdf_url} as {pdf_name}")
                load_file(pdf_url, pdf_name)
                return Response(response=json.dumps({"status": "success"}), status=200)
            
            # otherwise, load the file in a separate thread
            # thread load_file so that we can return a response immediately
            logging.info(f"[load_pdf] Loading PDF {pdf_url} as {pdf_name}")

            Thread(target=load_file, args=(pdf_url, pdf_name)).start()

            # resopnse with the number of seconds it will take to load the file and the name of the file and saying "The PDF is being loaded in the background and will be available in {time_to_load} seconds."
            return Response(response=json.dumps({"status": "success", "message": f"PDF has been successfully loaded and will be available in {time_to_load} seconds to process.", "time_to_load": time_to_load, "filename": pdf_name}), status=200)
            

    except (InvalidUrlError, PdfNotFoundError, PdfFormatError) as e:
        logging.error(f"[load_pdf] Error occurred: {e}")
        return Response(response=json.dumps({"error": str(e)}), status=400)
    except (PdfFetchError, PdfInvalidError) as e:
        logging.error(f"[load_pdf] PdfFetchError occurred: {e}")
        return Response(response=json.dumps({"error": "An error occurred. {e}"}), status=500)
    except Exception as e:
        logging.error(f"[load_pdf] Error occurred: {e}")
        return Response(response=json.dumps({"error": f"An unexpected error occurred. Error: {e}"}), status=500)

@app.route("/pdf/query", methods=['POST'])
def query_pdf():
    try:
        data = request.get_json(force=True)
        query = data["query"]
        pdf_url = data["pdf_url"]

        logging.info(f"[query_pdf] Querying PDF {pdf_url} with query: {query}")
        results = query_file(pdf_url, query)

        logging.info(f"[query_pdf] Query results for PDF {pdf_url}: {results}")
        logging.info(f"[query_pdf] Document results for PDF {pdf_url}: {results['documents'][0]}")

        return Response(response=json.dumps({"results": results['documents'][0]}), status=200)
    
    except QueryNoResultsError as e:
        logging.error(f"[query_pdf] Error occurred: {e}")

        return Response(response=json.dumps({"error": str(e)}), status=404)
    
    except Exception as e:
        logging.error(f"[query_pdf] Error occurred: {e}")

        return Response(response=json.dumps({"error": f"An unexpected error occurred. Error: {e}"}), status=500)
    
@app.route("/logo.png", methods=['GET'])
def plugin_logo():
    filename = os.path.join(current_dir, '..', 'assets', 'logo.png')
    return send_file(filename, mimetype='image/png')

@app.route("/.well-known/ai-plugin.json", methods=['GET'])
def plugin_manifest():
    host = request.headers['Host']
    with open(os.path.join(current_dir, '..', 'config', 'ai-plugin.json')) as f:
        text = f.read()
        text = text.replace("PLUGIN_HOSTNAME", f"http://{host}")
        return Response(text, mimetype="text/json")

@app.route("/openapi.yaml", methods=['GET'])
def openapi_spec():
    host = request.headers['Host']
    with open(os.path.join(current_dir, '..', 'config', 'openapi.yaml')) as f:
        text = f.read()
        text = text.replace("PLUGIN_HOSTNAME", f"http://{host}")
        return Response(text, mimetype="text/yaml")

@app.route("/legal", methods=['GET'])
def legal():
    with open(os.path.join(current_dir, '..', 'legal.txt')) as f:
        return Response(f.read(), mimetype="text/plain")

@app.route("/health", methods=['GET'])
def health_check():
    logging.info("Health check endpoint accessed")
    return Response(response="🫡", status=200, mimetype="text/plain")

@app.route("/", methods=['GET'])
def homepage():
    with open(os.path.join(current_dir, '..', 'index.html'), 'r') as f:
        content = f.read()
    return render_template_string(content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
