import time
import random
import logging
from statbotics import Statbotics

class StatboticsAPI:
    CACHE_EXPIRATION = 300  # 5 minutes in seconds

    def __init__(self, year):
        self.sb = Statbotics()
        self.year = year
        self.cached_teams = {}  # Store data along with timestamps
        self.max_retries = 3
        self.retry_delay = 1  # Initial retry delay in seconds

    def _is_cache_valid(self, team_number):
        """Check if cached data is still valid."""
        return (
            team_number in self.cached_teams and
            (time.time() - self.cached_teams[team_number]['timestamp']) < self.CACHE_EXPIRATION
        )

    def get_team_metrics(self, team):
        team_number = int(team)

        # Remove expired cache
        self._expire_cache()

        if self._is_cache_valid(team_number):
            logging.info(f"Using cached data for team {team_number}")
            return self.cached_teams[team_number]['data']

        print(f"Grabbing statistics from online, {team_number} was not cached")

        retries = 0
        delay = self.retry_delay
        while retries <= self.max_retries:
            try:
                metrics = self.sb.get_team_year(team_number, self.year)
                filtered_metrics = {
                    'team': metrics['team'],
                    'epa_start': metrics['epa']['stats']['start'],
                    'epa_pre_champs': metrics['epa']['stats']['pre_champs'],
                    'epa_diff': metrics['epa']['stats']['pre_champs'] - metrics['epa']['stats']['start'],
                    'auto_epa_end': metrics['epa']['breakdown']['auto_points'],
                    'teleop_epa_end': metrics['epa']['breakdown']['teleop_points'],
                    'endgame_epa_end': metrics['epa']['breakdown']['endgame_points'],
                    'rp_1_epa': metrics['epa']['breakdown']['rp_1'],
                    'rp_2_epa': metrics['epa']['breakdown']['rp_2'],
                    'unitless_epa_end': metrics['epa']['unitless'],
                    'norm_epa_end': metrics['epa']['norm'],
                    'epa_conf_1': metrics['epa']['conf'][0],
                    'epa_conf_2': metrics['epa']['conf'][1],
                    'wins': metrics['record']['wins'],
                    'losses': metrics['record']['losses'],
                    'ties': metrics['record']['ties'],
                    'count': metrics['record']['count'],
                    'winrate': metrics['record']['winrate'],
                    'total_epa_rank': metrics['epa']['ranks']['total']['rank'],
                    'total_epa_percentile': metrics['epa']['ranks']['total']['percentile'],
                    'country_epa_rank': metrics['epa']['ranks']['country']['rank'],
                    'state_epa_rank': metrics['epa']['ranks']['state']['rank'],
                    'district_epa_rank': metrics['epa']['ranks']['district']['rank'],
                    'country_epa_percentile': metrics['epa']['ranks']['country']['percentile'],
                    'state_epa_percentile': metrics['epa']['ranks']['state']['percentile'],
                    'district_epa_percentile': metrics['epa']['ranks']['district']['percentile'],
                }

                self.cached_teams[team_number] = {
                    'timestamp': time.time(),
                    'data': {team_number: filtered_metrics}
                }
                return {team_number: filtered_metrics}

            except Exception as e:
                logging.warning(f"Failed to retrieve data for team {team_number}: {str(e)}")
                retries += 1
                time.sleep(delay)
                delay *= 2  # Exponential backoff

    def format_team(self, team_number, placement):
        """
        Format team metrics with a specific placement prefix.

        Args:
            team_number (int): The team number.
            placement (str): The placement prefix (e.g., 'red1', 'blue2').

        Returns:
            dict: A dictionary containing the formatted team metrics.
        """
        data = self.get_team_metrics(team_number)
        new_data = data[int(team_number)]
        return {f'{placement}_{key}': new_data[key] for key in new_data}

    def format_match(self, match):
        """
        Format match data with team metrics.

        Args:
            match (list): A list containing match information.

        Returns:
            dict: A dictionary containing the formatted match data.
        """
        red1 = self.format_team(match[3][3:], 'red1')
        red2 = self.format_team(match[4][3:], 'red2')
        red3 = self.format_team(match[5][3:], 'red3')
        blue1 = self.format_team(match[0][3:], 'blue1')
        blue2 = self.format_team(match[1][3:], 'blue2')
        blue3 = self.format_team(match[2][3:], 'blue3')

        team_metrics = {'red1': int(match[0][3:])} | {'red2': int(match[1][3:])} | {'red3': int(match[2][3:])} | {
            'blue1': int(match[3][3:])} | {'blue2': int(match[4][3:])} | {'blue3': int(match[5][3:])}
        team_metrics = team_metrics | red1 | red2 | red3 | blue1 | blue2 | blue3

        return team_metrics

    def get_statbotics_match_prediction(self, match_key):
        """
        Retrieve match prediction from the Statbotics API.

        Args:
            match_key (str): The match key.

        Returns:
            list: A list containing the predicted winner and win probability.
        """
        try:
            match_info = self.sb.get_match(match_key)
            return [match_info['pred']['winner'], match_info['pred'].get('prob', 1)]
        except Exception as e:
            logging.warning(f"Statbotics API request failed for match {match_key}: {str(e)}")
            return [None, 0]

        return {team_number: {}}  # Return empty dict if all attempts fail

    def _expire_cache(self):
        """Remove expired cache entries."""
        now = time.time()
        self.cached_teams = {
            team: data for team, data in self.cached_teams.items()
            if (now - data['timestamp']) < self.CACHE_EXPIRATION
        }
