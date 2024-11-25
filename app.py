import csv
import logging
import os

from flask import Flask, jsonify, request, render_template, send_file
from flask_caching import Cache
from flask_cors import CORS
from redis import Redis

from helpers.logging_setup import setup_logging
from helpers.match_prediction import MatchPrediction
from helpers.statbotics_api import StatboticsAPI

# Configuration for Redis connection
redis_host: str = 'localhost'
redis_port: int = 6379
redis_db: int = 0

offseason = True

# Create a Redis connection using environment variables
redis_client = Redis(
    host=os.getenv('REDIS_HOST', redis_host),
    port=int(os.getenv('REDIS_PORT', str(redis_port))),
    decode_responses=True
)

app = Flask(__name__, template_folder='static/templates')

CORS(app, resources={r'/*': {'origins': '*'}}, supports_credentials=True)

config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300
}

app.config.from_mapping(config)
cache = Cache(app)

setup_logging()

model_dir = os.path.join('static', 'model', 'model.keras')
rf_dir = os.path.join('static', 'model', 'random_forest.pkl')
scaler_dir = os.path.join('static', 'model', 'scaler.pkl')

match_predictor = MatchPrediction(model_dir, rf_dir, scaler_dir)
statbotics = StatboticsAPI(2024)


@app.route('/')
def index():
    return 'Hello, Docker!'


@app.route('/tba', methods=['POST'])
def tba_webhook():
    print(request.json)

    match request.json['message_type']:
        case 'ping':
            logging.info('Received ping from TBA')
        case 'match_score':
            handle_new_match_score(request.json['message_data'])
        case 'upcoming_match':
            handle_upcoming_match(request.json['message_data'])

    return jsonify({'status': 'success'}), 200


@app.route('/{match_key}/prediction', methods=['GET'])
def get_match_prediction(match_key):
    if redis_client.exists(f'completed_match:{match_key}:metadata'):
        metadata = redis_client.hgetall(f'completed_match:{match_key}:metadata')
        return jsonify(metadata), 200
    else:
        return jsonify({'error': 'Match not found'}), 404


def handle_new_match_score(message_json):
    match_key = message_json['match']['key']

    if redis_client.exists(f'upcoming_match:{match_key}:fields'):
        redis_client.hset(f'upcoming_match:{match_key}:metadata', 'actual_winner',
                          message_json['match']['winning_alliance'])

        logging.info(f'red total point keys {message_json["match"]["alliances"]["red"].keys()}')
        redis_client.hset(f'upcoming_match:{match_key}:metadata', mapping={
            'red_score': message_json['match']['alliances']['red']['score'],
            'blue_score': message_json['match']['alliances']['blue']['score'],
            'red_rp': message_json['match']['score_breakdown']['red']['rp'],
            'blue_rp': message_json['match']['score_breakdown']['blue']['rp']
        })

        redis_client.rename(f'upcoming_match:{match_key}:fields',
                            f'completed_match:{match_key}:fields')
        redis_client.rename(f'upcoming_match:{match_key}:metadata',
                            f'completed_match:{match_key}:metadata')

        if not redis_client.exists('local_prediction_accuracy'):
            redis_client.hset('local_prediction_accuracy', mapping={'correct': 0, 'total': 0, 'accuracy': 0.0})

        if not redis_client.exists('statbotics_prediction_accuracy'):
            redis_client.hset('statbotics_prediction_accuracy', mapping={'correct': 0, 'total': 0, 'accuracy': 0.0})

        if redis_client.hget(f'completed_match:{match_key}:metadata', 'actual_winner') == redis_client.hget(
                f'completed_match:{match_key}:metadata', 'local_predicted_winner'):
            redis_client.hincrby('local_prediction_accuracy', 'correct', 1)
        redis_client.hincrby('local_prediction_accuracy', 'total', 1)
        redis_client.hset('local_prediction_accuracy', 'accuracy',
                          int(redis_client.hget('local_prediction_accuracy', 'correct')) / int(
                              redis_client.hget('local_prediction_accuracy', 'total')))

        if redis_client.hget(f'completed_match:{match_key}:metadata', 'actual_winner') == redis_client.hget(
                f'completed_match:{match_key}:metadata', 'statbotics_prediction'):
            redis_client.hincrby('statbotics_prediction_accuracy', 'correct', 1)
        redis_client.hincrby('statbotics_prediction_accuracy', 'total', 1)
        redis_client.hset('statbotics_prediction_accuracy', 'accuracy',
                          int(redis_client.hget('statbotics_prediction_accuracy', 'correct')) / int(
                              redis_client.hget('statbotics_prediction_accuracy', 'total')))
    elif redis_client.exists(f'completed_match:{match_key}:fields'):
        logging.info(f'Match {match_key} has already been processed')
    else:
        if not redis_client.exists('failed_matches'):
            redis_client.set('failed_matches', 0)
        redis_client.incrby('failed_matches', 1)

    return jsonify({'status': 'success'}), 200


def handle_upcoming_match(message_json):
    formatted_match = statbotics.format_match(message_json['team_keys'])
    prediction = match_predictor.predict(formatted_match)

    local_prediction = {'red_alliance_win_confidence': str(prediction[0]),
                        'blue_alliance_win_confidence': str(prediction[1]),
                        'draw_confidence': str(prediction[2])}

    if float(local_prediction['draw_confidence']) > 1 / 3:
        local_predicted_winner = 'draw'
    else:
        local_predicted_winner = 'red' if float(local_prediction['red_alliance_win_confidence']) > float(
            local_prediction['blue_alliance_win_confidence']) else 'blue'

    redis_client.hset(f'upcoming_match:{message_json["match_key"]}:fields', mapping={**formatted_match})

    if offseason:
        metadata = {
            **local_prediction,
            'statbotics_prediction': 'red',
            'statbotics_win_confidence': '1.0',
            'local_predicted_winner': local_predicted_winner,
            'event_key': message_json['event_key'],
            'match_key': message_json['match_key'],
            'event_name': message_json['event_name'],
            'time': message_json['scheduled_time']
        }
    else:
        metadata = {
            **local_prediction,
            'statbotics_prediction': statbotics.get_statbotics_match_prediction(message_json['match_key'])[0],
            'statbotics_win_confidence': statbotics.get_statbotics_match_prediction(message_json['match_key'])[1],
            'local_predicted_winner': local_predicted_winner,
            'event_key': message_json['event_key'],
            'match_key': message_json['match_key'],
            'event_name': message_json['event_name'],
            'time': message_json['scheduled_time']
        }

    redis_client.hset(f'upcoming_match:{message_json["match_key"]}:metadata', mapping={**metadata})

    return jsonify({'status': 'success'}), 200


@app.route('/dataset', methods=['GET'])
def get_dataset():
    # Get all keys that match the pattern
    keys = redis_client.keys('completed_match:*:fields')

    # Initialize a list to hold the match data
    matches = []

    # Iterate over the keys
    for key in keys:
        # Get the hash data for the key
        data = redis_client.hgetall(key)

        # Get the associated metadata key
        metadata_key = key.replace(':fields', ':metadata')
        metadata = redis_client.hgetall(metadata_key)

        # Merge the data and metadata
        merged_data = {**data, **metadata}
        merged_data['match_key'] = key.split(':')[1]  # Extract match_key from the key

        # Append the merged data to the matches list
        matches.append(merged_data)

    return render_template('dataset.html', matches=matches)


@app.route('/dataset_csv', methods=['GET'])
def get_dataset_csv():
    # Get all keys that match the pattern
    keys = redis_client.keys('completed_match:*:fields')

    # Initialize a set to hold all possible fieldnames
    all_fieldnames = set()

    # Initialize a list to hold the match data
    matches = []

    # Iterate over the keys to collect all fieldnames
    for key in keys:
        # Get the hash data for the key
        data = redis_client.hgetall(key)

        # Get the associated metadata key
        metadata_key = key.replace(':fields', ':metadata')
        metadata = redis_client.hgetall(metadata_key)

        # Merge the data and metadata
        merged_data = {**data, **metadata}

        # Add the keys to the set of all fieldnames
        all_fieldnames.update(merged_data.keys())

        # Append the merged data to the matches list
        matches.append(merged_data)

    # Convert the set of fieldnames to a sorted list
    all_fieldnames = sorted(all_fieldnames)

    # Open a CSV file for writing
    csv_path = os.path.join('static', 'matches.csv')
    with open(csv_path, 'w', newline='') as csvfile:
        # Initialize the CSV writer
        writer = csv.DictWriter(csvfile, fieldnames=all_fieldnames)
        writer.writeheader()

        # Write each match's data to the CSV file
        for match in matches:
            writer.writerow(match)

    return send_file(csv_path, as_attachment=True)