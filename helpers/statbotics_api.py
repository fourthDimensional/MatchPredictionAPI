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

        return {team_number: {}}  # Return empty dict if all attempts fail

    def _expire_cache(self):
        """Remove expired cache entries."""
        now = time.time()
        self.cached_teams = {
            team: data for team, data in self.cached_teams.items()
            if (now - data['timestamp']) < self.CACHE_EXPIRATION
        }
