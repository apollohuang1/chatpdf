import json
import os
import logging
from dotenv import load_dotenv
from quart import Quart, request, Response, send_file, render_template, render_template_string
import quart_cors
from utils.utils import download_pdf
from utils.process import load_file, query_file, check_pdf_exists

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = quart_cors.cors(Quart(__name__))

@app.post("/pdf/load")
async def load_pdf():
    try:
        data = await request.get_json(force=True)
        logging.info(f"[load_pdf] Data: {data}")
        pdf_url = data["pdf_url"]

        if check_pdf_exists(pdf_url):
            logging.info(f"[load_pdf] PDF {pdf_url} already exists, skipping download and loading")
            return Response(response=json.dumps({"status": "success"}), status=200)

        logging.info(f"[load_pdf] Loading PDF from URL: {pdf_url}")
        pdf_name = download_pdf(pdf_url)
        load_file(pdf_name)
        logging.info(f"[load_pdf] PDF loaded from URL: {pdf_url}")

        return Response(response=json.dumps({"status": "success"}), status=200)
    except Exception as e:
        logging.error(f"[load_pdf] Error occurred: {e}")
        return Response(response=json.dumps({"error": "An error occurred."}), status=500)


@app.post("/pdf/<pdf_name>/query")
async def query_pdf(pdf_name):
    try:
        data = await request.get_json(force=True)
        query = data["query"]
        logging.info(f"[query_pdf] Querying PDF {pdf_name} with query: {query}")
        results = query_file(pdf_name, query)
        logging.info(f"[query_pdf] Query results for PDF {pdf_name}: {results}")
        logging.info(f"[query_pdf] Document results for PDF {pdf_name}: {results['documents'][0]}")
        return Response(response=json.dumps({"results": results['documents'][0]}), status=200)

    except Exception as e:
        logging.error(f"[query_pdf] Error occurred: {e}")
        return Response(response=json.dumps({"error": "An error occurred."}), status=500)

@app.get("/logo.png")
async def plugin_logo():
    filename = os.path.join(current_dir, '..', 'assets', 'logo.png')
    return await send_file(filename, mimetype='image/png')

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open(os.path.join(current_dir, '..', 'config', 'ai-plugin.json')) as f:
        text = f.read()
        text = text.replace("PLUGIN_HOSTNAME", f"http://{host}")
        return Response(text, mimetype="text/json")

@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open(os.path.join(current_dir, '..', 'config', 'openapi.yaml')) as f:
        text = f.read()
        text = text.replace("PLUGIN_HOSTNAME", f"http://{host}")
        return Response(text, mimetype="text/yaml")
    

@app.get("/legal")
async def legal():
    with open(os.path.join(current_dir, '..', 'legal.txt')) as f:
        return Response(f.read(), mimetype="text/plain")

@app.get("/health")
async def health_check():
    logging.info("Health check endpoint accessed")
    return Response(response="🫡", status=200, mimetype="text/plain")

@app.get("/")
async def homepage():
    with open(os.path.join(current_dir, '..', 'index.html'), 'r') as f:
        content = f.read()
    return await render_template_string(content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

