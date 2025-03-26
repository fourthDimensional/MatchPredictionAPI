import csv
import logging
import os
import smtplib

from flask import Flask, jsonify, request, render_template, send_file, redirect
from flask_caching import Cache
from flask_cors import CORS
from redis import Redis

from helpers.logging_setup import setup_logging
from helpers.match_prediction import MatchPrediction
from helpers.statbotics_api import StatboticsAPI
from helpers.tba_api import BlueAllianceAPI
from email.mime.text import MIMEText

server = smtplib.SMTP_SSL('smtp.gmail.com', 465)

def send_email(subject, body):
    msg = MIMEText(body)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(os.getenv('EMAIL_ADDRESS'), os.getenv('EMAIL_PASSWORD'))
       smtp_server.sendmail(os.getenv('EMAIL_ADDRESS'), os.getenv('EMAIL_RECIPIENTS'), msg.as_string())

# Configuration for Redis connection
redis_host: str = 'localhost'
redis_port: int = 6379
redis_db: int = 0

offseason = False

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
model_rp_dir = os.path.join('static', 'rp_model', 'model.keras')
rf_rp_dir = os.path.join('static', 'rp_model', 'random_forest.pkl')
scaler_rp_dir = os.path.join('static', 'rp_model', 'scaler.pkl')

match_predictor = MatchPrediction(model_dir, rf_dir, scaler_dir, model_rp_dir, rf_rp_dir, scaler_rp_dir)
statbotics = StatboticsAPI(2025)
tba_api = BlueAllianceAPI(api_key='fWFSAeNa3VxZUdVJhaXgAXjnM9mfLBmbw1bbOrviglJBtJxmcUTANIMpECdWSSwU', year=2024)


def formatRpPrediction(value):
    return round(value*6, 0)


@app.route('/')
def index():
    return redirect('/dataset')


# Define a route to handle POST requests from TBA
@app.route('/tba', methods=['POST'])
def tba_webhook():
    # Match the message type from the request JSON
    match request.json['message_type']:
        case 'ping':
            # Log a message when a ping is received
            logging.info('Received ping from TBA')
        case 'match_score':
            # Handle new match score updates
            handle_new_match_score(request.json['message_data'])
        case 'upcoming_match':
            # Handle upcoming match notifications
            handle_upcoming_match(request.json['message_data'])

    # Return a success response
    return jsonify({'status': 'success'}), 200


@app.route('/<match_key>/prediction', methods=['GET'])
def get_match_prediction(match_key):
    # Check if the match metadata exists in Redis
    if redis_client.exists(f'completed_match:{match_key}:metadata'):
        # Retrieve the metadata from Redis
        metadata = redis_client.hgetall(f'completed_match:{match_key}:metadata')
        # Return the metadata as a JSON response with a 200 status code
        return jsonify(metadata), 200
    else:
        # Return an error message as a JSON response with a 404 status code
        team_data = tba_api.get_general_match_info(match_key)
        formatted_match = statbotics.format_match(team_data)
        prediction = match_predictor.predict(formatted_match)
        rp_prediction = match_predictor.predict_rp(formatted_match)

        return jsonify({'red_alliance_win_confidence': str(prediction[0]),
                        'blue_alliance_win_confidence': str(prediction[1]),
                        'draw_confidence': str(prediction[2]),
                        'red_rp_prediction': formatRpPrediction(rp_prediction[0]),
                        'blue_rp_prediction': formatRpPrediction(rp_prediction[1])}), 200


@app.route('/prediction', methods=['GET', 'POST'])
def get_upcoming_match_prediction():
    """
    Returns a match prediction from six teams.
    Uses Statbotics API system to get the needed input fields
    Uses Tensorflow Inference to load model file and make a prediction

    Args:
        teams (list): list of six teams in form data
    """
    # Grabs team keys from form data in puts them into lists.
    form_labels_red = {'team-red-1',
                       'team-red-2',
                       'team-red-3'}
    form_labels_blue = {'team-blue-1',
                        'team-blue-2',
                        'team-blue-3'}
    teams_red = []
    teams_blue = []
    for form_label in form_labels_red:
        teams_red.append(request.form.get(form_label))
    for form_label in form_labels_blue:
        teams_blue.append(request.form.get(form_label))

    formatted_match = statbotics.format_match(teams_blue + teams_red)

    prediction = match_predictor.predict(formatted_match)
    rp_prediction = match_predictor.predict_rp(formatted_match)

    return {'red_alliance_win_confidence': str(prediction[0]),
            'blue_alliance_win_confidence': str(prediction[1]),
            'draw_confidence': str(prediction[2]),
            'red_rp_prediction': str(formatRpPrediction(rp_prediction[0])),
            'blue_rp_prediction': str(formatRpPrediction(rp_prediction[1]))}


if __name__ == '__main__':
    app.run(port=5001)


def handle_new_match_score(message_json):
    # Extract the match key from the message
    match_key = message_json['match']['key']

    # Check if the match data exists in Redis for upcoming matches
    if redis_client.exists(f'upcoming_match:{match_key}:fields'):
        # Store the actual winner in Redis
        redis_client.hset(f'upcoming_match:{match_key}:metadata', 'actual_winner',
                          message_json['match']['winning_alliance'])

        # Log the red alliance total point keys
        logging.info(f'red total point keys {message_json["match"]["alliances"]["red"].keys()}')

        # Store the match scores and ranking points in Redis
        redis_client.hset(f'upcoming_match:{match_key}:metadata', mapping={
            'red_score': message_json['match']['alliances']['red']['score'],
            'blue_score': message_json['match']['alliances']['blue']['score'],
            'red_rp': message_json['match']['score_breakdown']['red']['rp'],
            'blue_rp': message_json['match']['score_breakdown']['blue']['rp']
        })

        # Rename the keys to mark the match as completed
        redis_client.rename(f'upcoming_match:{match_key}:fields',
                            f'completed_match:{match_key}:fields')
        redis_client.rename(f'upcoming_match:{match_key}:metadata',
                            f'completed_match:{match_key}:metadata')

        # Initialize prediction accuracy tracking if not already present
        if not redis_client.exists('local_prediction_accuracy'):
            redis_client.hset('local_prediction_accuracy', mapping={'correct': 0, 'total': 0, 'accuracy': 0.0})

        if not redis_client.exists('statbotics_prediction_accuracy'):
            redis_client.hset('statbotics_prediction_accuracy', mapping={'correct': 0, 'total': 0, 'accuracy': 0.0})

        # Update local prediction accuracy
        if redis_client.hget(f'completed_match:{match_key}:metadata', 'actual_winner') == redis_client.hget(
                f'completed_match:{match_key}:metadata', 'local_predicted_winner'):
            redis_client.hincrby('local_prediction_accuracy', 'correct', 1)
        redis_client.hincrby('local_prediction_accuracy', 'total', 1)
        redis_client.hset('local_prediction_accuracy', 'accuracy',
                          int(redis_client.hget('local_prediction_accuracy', 'correct')) / int(
                              redis_client.hget('local_prediction_accuracy', 'total')))

        # Update Statbotics prediction accuracy
        if redis_client.hget(f'completed_match:{match_key}:metadata', 'actual_winner') == redis_client.hget(
                f'completed_match:{match_key}:metadata', 'statbotics_prediction'):
            redis_client.hincrby('statbotics_prediction_accuracy', 'correct', 1)
        redis_client.hincrby('statbotics_prediction_accuracy', 'total', 1)
        redis_client.hset('statbotics_prediction_accuracy', 'accuracy',
                          int(redis_client.hget('statbotics_prediction_accuracy', 'correct')) / int(
                              redis_client.hget('statbotics_prediction_accuracy', 'total')))
    # Check if the match has already been processed
    elif redis_client.exists(f'completed_match:{match_key}:fields'):
        logging.info(f'Match {match_key} has already been processed')
    # Handle failed matches
    else:
        if not redis_client.exists('failed_matches'):
            redis_client.set('failed_matches', 0)
        redis_client.incrby('failed_matches', 1)

        # SHUT UP
        # send_email('Failed Match', f'Match {match_key} has failed to process')

    # Return a success response
    return jsonify({'status': 'success'}), 200


def handle_upcoming_match(message_json):
    # Format the match data using Statbotics API
    formatted_match = statbotics.format_match(message_json['team_keys'])

    # Predict the match outcome using the match predictor
    prediction = match_predictor.predict(formatted_match)
    rp_prediction = match_predictor.predict_rp(formatted_match)

    # Create a dictionary for local prediction results
    local_prediction = {
        'red_alliance_win_confidence': str(prediction[0]),
        'blue_alliance_win_confidence': str(prediction[1]),
        'draw_confidence': str(prediction[2]),
        'red_rp_prediction': str(formatRpPrediction(rp_prediction[0])),
        'blue_rp_prediction': str(formatRpPrediction(rp_prediction[1]))
    }

    # Determine the predicted winner based on confidence values
    if float(local_prediction['draw_confidence']) > 1 / 3:
        local_predicted_winner = 'draw'
    else:
        local_predicted_winner = 'red' if float(local_prediction['red_alliance_win_confidence']) > float(
            local_prediction['blue_alliance_win_confidence']) else 'blue'

    # Store the formatted match data in Redis
    redis_client.hset(f'upcoming_match:{message_json["match_key"]}:fields', mapping={**formatted_match})

    # Create metadata for the match based on whether it is offseason or not
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

    # Store the metadata in Redis
    redis_client.hset(f'upcoming_match:{message_json["match_key"]}:metadata', mapping={**metadata})

    # Return a success response
    return jsonify({'status': 'success'}), 200


@app.route('/dataset', methods=['GET'])
def get_dataset():
    # Get all keys for completed and upcoming matches
    completed_keys = redis_client.keys('completed_match:*:fields')
    upcoming_keys = redis_client.keys('upcoming_match:*:fields')

    # Initialize a list to hold the match data
    matches = []

    # Function to process match keys
    def process_keys(keys, status):
        for key in keys:
            # Get the hash data for the key
            data = redis_client.hgetall(key)

            # Get the associated metadata key
            metadata_key = key.replace(':fields', ':metadata')
            metadata = redis_client.hgetall(metadata_key)

            # Merge the data and metadata
            merged_data = {**data, **metadata}
            merged_data['match_key'] = key.split(':')[1]  # Extract match_key from the key
            merged_data['status'] = status  # Add status to differentiate between completed and upcoming

            # Append the merged data to the matches list
            matches.append(merged_data)

    # Process completed and upcoming matches
    process_keys(completed_keys, 'completed')
    process_keys(upcoming_keys, 'upcoming')

    # Sort matches: upcoming matches first, then by match_key
    matches.sort(key=lambda x: (x['status'] == 'completed', x['match_key']))

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