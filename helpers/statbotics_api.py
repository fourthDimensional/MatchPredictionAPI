import time
import random
import logging
from statbotics import Statbotics

# Define default metrics to use when API calls fail
DEFAULT_METRICS = {
    'team': 0,
    'epa_start': 0,
    'epa_pre_champs': 0,
    'epa_diff': 0,
    'auto_epa_end': 0,
    'teleop_epa_end': 0,
    'endgame_epa_end': 0,
    'rp_1_epa': 0,
    'rp_2_epa': 0,
    'unitless_epa_end': 0,
    'norm_epa_end': 0,
    'epa_conf_1': 0,
    'epa_conf_2': 0,
    'wins': 0,
    'losses': 0,
    'ties': 0,
    'count': 0,
    'winrate': 0.5,
    'total_epa_rank': 0,
    'total_epa_percentile': 0,
    'country_epa_rank': 0,
    'state_epa_rank': 0,
    'district_epa_rank': 0,
    'country_epa_percentile': 0,
    'state_epa_percentile': 0,
    'district_epa_percentile': 0
}

fields = [
    'team', 'epa_start', 'epa_pre_champs', 'epa_end', 'epa_diff',
    'auto_epa_end', 'teleop_epa_end', 'endgame_epa_end',
    'rp_1_epa_end', 'rp_2_epa_end', 'unitless_epa_end', 'norm_epa_end',
    'wins', 'losses', 'ties', 'count', 'winrate', 'full_wins', 'full_losses', 'full_ties', 'full_count', 'full_winrate',
    'total_epa_rank', 'total_epa_percentile', 'country_epa_rank', 'state_epa_rank', 'district_epa_rank',
    'country_epa_percentile', 'state_epa_percentile', 'district_epa_percentile'
]



class StatboticsAPI:
    def __init__(self, year):
        """
        Initialize the StatboticsAPI class.

        Args:
            year (int): The year for which to retrieve data.
        """
        self.sb = Statbotics()
        self.year = year
        self.context = 'seasonal'
        self.cached_teams = {}
        self.max_retries = 3
        self.retry_delay = 1  # Initial retry delay in seconds

    def get_team_metrics(self, team):
        """
        Retrieve team metrics from the Statbotics API or cache.

        Args:
            team (int): The team number.

        Returns:
            dict: A dictionary containing the team's metrics.
        """
        team_number = int(team)
        
        # Check if the team metrics are already cached
        if team_number in self.cached_teams:
            logging.info(f"Using cached data for team {team_number}")
            return self.cached_teams[team_number]

        print(f"Grabbing statistics from online, {team_number} was not cached")
        
        retries = 0
        delay = self.retry_delay
        
        while retries <= self.max_retries:
            try:
                metrics = self.sb.get_team_year(team_number, self.year)

                filtered_metrics = {}

                filtered_metrics['team'] = metrics['team']
                filtered_metrics['epa_start'] = metrics['epa']['stats']['start']
                filtered_metrics['epa_pre_champs'] = metrics['epa']['stats']['pre_champs']

        filtered_metrics['team'] = metrics['team']
        filtered_metrics['epa_start'] = metrics['epa']['stats']['start']
        filtered_metrics['epa_pre_champs'] = metrics['epa']['stats']['pre_champs']
        filtered_metrics['epa_diff'] = metrics['epa']['stats']['pre_champs'] - metrics['epa']['stats']['start']
        filtered_metrics['auto_epa_end'] = metrics['epa']['breakdown']['auto_points']
        filtered_metrics['teleop_epa_end'] = metrics['epa']['breakdown']['teleop_points']
        filtered_metrics['endgame_epa_end'] = metrics['epa']['breakdown']['endgame_points']
        filtered_metrics['rp_1_epa'] = metrics['epa']['breakdown']['rp_1']
        filtered_metrics['rp_2_epa'] = metrics['epa']['breakdown']['rp_2']
        filtered_metrics['unitless_epa_end'] = metrics['epa']['unitless']
        filtered_metrics['norm_epa_end'] = metrics['epa']['norm']
        filtered_metrics['epa_conf_1'] = metrics['epa']['conf'][0]
        filtered_metrics['epa_conf_2'] = metrics['epa']['conf'][1]
        filtered_metrics['wins'] = metrics['record']['wins']
        filtered_metrics['losses'] = metrics['record']['losses']
        filtered_metrics['ties'] = metrics['record']['ties']
        filtered_metrics['count'] = metrics['record']['count']
        filtered_metrics['winrate'] = metrics['record']['winrate']
        filtered_metrics['total_epa_rank'] = metrics['epa']['ranks']['total']['rank']
        filtered_metrics['total_epa_percentile'] = metrics['epa']['ranks']['total']['percentile']
        filtered_metrics['country_epa_rank'] = metrics['epa']['ranks']['country']['rank']
        filtered_metrics['state_epa_rank'] = metrics['epa']['ranks']['state']['rank']
        filtered_metrics['district_epa_rank'] = metrics['epa']['ranks']['district']['rank']
        filtered_metrics['country_epa_percentile'] = metrics['epa']['ranks']['country']['percentile']
        filtered_metrics['state_epa_percentile'] = metrics['epa']['ranks']['state']['percentile']
        filtered_metrics['district_epa_percentile'] = metrics['epa']['ranks']['district']['percentile']

        extracted_metric = filtered_metrics

        newly_formatted = {}
        extracted_team = extracted_metric['team']
        del extracted_metric['team']
        newly_formatted.update({extracted_team: extracted_metric})

        self.cached_teams[int(team)] = newly_formatted

        return newly_formatted

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

        team_metrics = {'red1': int(match[0][3:])} | {'red2': int(match[1][3:])} | {'red3': int(match[2][3:])} | {'blue1': int(match[3][3:])} | {'blue2': int(match[4][3:])} | {'blue3': int(match[5][3:])}
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