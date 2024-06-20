import logging

from flask import Flask, jsonify, request
from flask_cors import CORS

from helpers.logging_setup import setup_logging

app = Flask(__name__)

CORS(app, resources={r'/*': {'origins': '*'}}, supports_credentials=True)

setup_logging()


@app.route('/tba/ping', methods=['POST'])
def test_connection():  # Uses TBA ping webhook to test the connection

    logging.info('Received ping from TBA')

    return jsonify({'status': 'success'}), 200


# learned there is only one route for a single webhook and I have to handle it based off of the message type
@app.route('/tba', methods=['POST'])
def tba_webhook():
    logging.info(request.json)
    logging.info('Received new information from TBA')

    match request.json['message_type']:
        case 'ping':
            logging.info('Received ping from TBA')
        case 'match_score':
            handle_new_match_score(request['message_data'])

    return jsonify({'status': 'success'}), 200


def handle_new_match_score(message_json):
    logging.info('Received new match score from TBA')
    logging.info(message_json)

    return jsonify({'status': 'success'}), 200
