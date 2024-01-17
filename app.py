import sys
from flask import Flask, request, jsonify, Response
from flask_cors import CORS  # Importieren von flask_cors

# Pfad zum Verzeichnis des Skripts hinzufügen
sys.path.append(r'C:\Users\janni\Desktop\DT-Projekt\backend_prompt_chatgpt_aufruf.py')

from backend_prompt_chatgpt_aufruf import generate_response

app = Flask(__name__)
CORS(app)  # Aktivieren von CORS für die gesamte Flask-Anwendung

NGROK_URL = 'https://finaigpt-public.eu.ngrok.io'

@app.route("/")
def index():
    return Response("Flask-Server läuft!", mimetype='text/plain')

@app.route("/generate_response", methods=["POST"])
def handle_generate_response():
    data = request.json
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    commodity = data.get('commodity')
    prompt_type = data.get('prompt_type')

    # Aufrufen der Funktion aus dem importierten Skript
    your_generated_text = generate_response(start_date, end_date,commodity, prompt_type)

    return jsonify({'generatedText': your_generated_text})

if __name__ == '__main__':
    app.run(debug=True)

