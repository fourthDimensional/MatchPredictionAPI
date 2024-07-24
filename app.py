import logging

from flask import Flask, jsonify, request
from flask_caching import Cache
from flask_cors import CORS

from helpers.logging_setup import setup_logging
from helpers.match_prediction import MatchPrediction
from helpers.statbotics_api import StatboticsAPI

app = Flask(__name__)

CORS(app, resources={r'/*': {'origins': '*'}}, supports_credentials=True)

config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300
}

app.config.from_mapping(config)
cache = Cache(app)

setup_logging()

match_predictor = MatchPrediction('static/model/model.keras', 'static/model/random_forest.pkl',
                                  'static/model/scaler.pkl')
statbotics = StatboticsAPI(2024)


@app.route('/tba/ping', methods=['POST'])
def test_connection():  # Uses TBA ping webhook to test the connection

    logging.info('Received ping from TBA')

    return jsonify({'status': 'success'}), 200


# learned there is only one route for a single webhook and I have to handle it based off of the message typex
@app.route('/tba', methods=['POST'])
@cache.cached(timeout=20)
def tba_webhook():
    logging.info(request.json)
    logging.info('Received new information from TBA')

    match request.json['message_type']:
        case 'ping':
            logging.info('Received ping from TBA')
        case 'match_score':
            handle_new_match_score(request.json['message_data'])
        case 'upcoming_match':
            handle_upcoming_match(request.json['message_data'])

    return jsonify({'status': 'success'}), 200


def handle_new_match_score(message_json):
    logging.info('Received new match score from TBA')
    logging.info(message_json)

    return jsonify({'status': 'success'}), 200


def handle_upcoming_match(message_json):
    logging.info('Received upcoming match from TBA')
    logging.info(message_json)

    formatted_match = statbotics.format_match(message_json['team_keys'])
    prediction = match_predictor.predict(formatted_match)

    local_prediction = {'red_alliance_win_confidence': str(prediction[0]),
                        'blue_alliance_win_confidence': str(prediction[1]),
                        'draw_confidence': str(prediction[2])}

    if local_prediction['draw_confidence'] > (
            local_prediction['blue_alliance_win_confidence'] + local_prediction['red_alliance_win_confidence']):
        local_predicted_winner = 'draw'
    else:
        local_predicted_winner = 'red' if local_prediction['red_alliance_win_confidence'] > local_prediction[
            'blue_alliance_win_confidence'] else 'blue'

    logging.info(
        f'Statbotics predicted winner: {statbotics.get_statbotics_match_prediction(message_json["match_key"])[0]}')

    logging.info(f'Locally predicted winner: {local_predicted_winner}')

    return jsonify({'status': 'success'}), 200
