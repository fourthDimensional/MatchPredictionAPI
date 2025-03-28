import unittest
from unittest.mock import patch, MagicMock
import json
from app import app, handle_new_match_score

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
    @patch('app.redis_client')
    def test_handle_new_match_score_with_none_score_breakdown(self, mock_redis):
        # Setup redis mock to indicate the match exists
        mock_redis.exists.return_value = True
        
        # Create test data with score_breakdown as None
        message_json = {
            'match': {
                'key': '2025mibig_qm45',
                'winning_alliance': 'red',
                'alliances': {
                    'red': {
                        'score': 115,
                        'keys': ['frc4327', 'frc6098', 'frc494']
                    },
                    'blue': {
                        'score': 50,
                        'keys': ['frc9225', 'frc10622', 'frc9742']
                    }
                },
                'score_breakdown': None
            }
        }
        
        # Call the function
        response = handle_new_match_score(message_json)
        
        # Verify the response
        self.assertEqual(response[1], 200)
        
        # Verify redis was called with correct parameters
        expected_mapping = {
            'red_score': message_json['match']['alliances']['red']['score'],
            'blue_score': message_json['match']['alliances']['blue']['score'],
            'red_rp': 0,
            'blue_rp': 0
        }
        mock_redis.hset.assert_any_call(
            f'upcoming_match:{message_json["match"]["key"]}:metadata', 
            mapping=expected_mapping
        )

if __name__ == '__main__':
    unittest.main()