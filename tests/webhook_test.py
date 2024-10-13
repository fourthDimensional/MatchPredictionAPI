import requests


def test_post_new_match():
    url = "http://localhost:5000/tba"
    headers = {'Content-Type': 'application/json'}
    data = {
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
                "score_breakdown": None,
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

    response = requests.post(url, headers=headers, json=data)

    assert response.status_code == 200
