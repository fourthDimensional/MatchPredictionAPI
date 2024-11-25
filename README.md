# FRC Match Prediction Webserver

## Overview

This repository contains a Flask webserver that interacts with the First Robotics Competition (FRC) API called The Blue Alliance (TBA). The server retrieves relevant robot statistics about a match before it starts, makes a prediction on the match outcome, and then compares the prediction to the actual results once the match finishes. All data is stored in a Redis database.

## Features

- **Flask Webserver**: Serves as the main application framework.
- **TBA Integration**: Fetches match and team data from The Blue Alliance API using a webhook.
- **Match Prediction**: Uses machine learning models to predict match outcomes.
- **Redis Database**: Stores match data, predictions, and results.
- **Dockerized Deployment**: Easily deployable using Docker and Docker Compose.

## Requirements

- Redis
- Python 3.12

OR

- Docker
- Docker Compose

## Installation

1. **Clone the repository**:
    ```sh
    git clone https://github.com/yourusername/yourrepository.git
    cd yourrepository
    ```

2. **Build and run the Docker containers**:
    ```sh
    docker-compose up --build
    ```

## Usage

On The Blue Alliance's [website](https://www.thebluealliance.com/account), setup a webhook with your published API route with /tba appended to the base url.

It will automatically receive webhook data and process it. You may need to subscribe to specific events or teams on TBA's website.

### Endpoints

- **POST /tba**: Receives webhook data from TBA and processes match information.
- **GET /{match_key}/prediction**: Retrieves the prediction for a specific match.
- **GET /dataset**: Exports all completed match data to a CSV file.

### Example Webhook Payload From TBA

```json
{
    "message_data": {
        "event_name": "New England FRC Region Championship",
        "match": {
            "comp_level": "f",
            "match_number": 1,
            "videos": [],
            "time_string": "3:18 PM",
            "set_number": 1,
            "key": "2014necmp_f1m1",
            "time": 1397330280,
            "score_breakdown": null,
            "alliances": {
                "blue": {
                    "score": 154,
                    "teams": [
                        "frc177",
                        "frc230",
                        "frc4055"
                    ]
                },
                "red": {
                    "score": 78,
                    "teams": [
                        "frc195",
                        "frc558",
                        "frc5122"
                    ]
                }
            },
            "event_key": "2014necmp"
        }
    },
    "message_type": "match_score"
}
```

## Project Structure

- `app.py`: Main Flask application file.
- `helpers/`: Contains helper modules for logging setup, match prediction, and Statbotics API integration.
- `requirements.txt`: Python dependencies.
- `Dockerfile`: Docker configuration for building the application image.
- `compose.yaml`: Docker Compose configuration for setting up the application and Redis services.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Acknowledgements

- [The Blue Alliance](https://www.thebluealliance.com/) for providing the FRC API.
- [Redis](https://redis.io/) for the in-memory data structure store.
- [Flask](https://flask.palletsprojects.com/) for the web framework.
- [Docker](https://www.docker.com/) for containerization.
