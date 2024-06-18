from flask import Flask, jsonify, abort, request, make_response
from flask_cors import CORS
from helpers.logging_setup import setup_logging

app = Flask(__name__)

CORS(app, resources={r'/*': {'origins': '*'}}, supports_credentials=True)

setup_logging()

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'
