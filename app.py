import logging

from flask import Flask, jsonify
from flask_cors import CORS

from helpers.logging_setup import setup_logging

app = Flask(__name__)

CORS(app, resources={r'/*': {'origins': '*'}}, supports_credentials=True)

setup_logging()


@app.route('/tba/ping', methods=['POST'])
def test_connection():  # Uses TBA ping webhook to test the connection
    logging.info('Received ping from TBA')

    return jsonify({'status': 'success'}), 200

@app.route('/tba/new_match', methods=['POST'])
def log_new_match():
    logging.info('Received new match from TBA')

    return jsonify({'status': 'success'}), 200
