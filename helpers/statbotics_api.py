from statbotics import Statbotics

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
        self.sb = Statbotics()
        self.year = year
        self.context = 'seasonal'

        self.cached_teams = {}

    def get_team_metrics(self, team):
        if int(team) in self.cached_teams:
            return self.cached_teams[int(team)]
        else:
            print(f"Grabbing statistics from online, {team} was not cached")
            metrics = self.sb.get_team_year(int(team), self.year)
            extracted_metric = {key: metrics[key] for key in fields}

            newly_formatted = {}

            extracted_team = extracted_metric['team']
            del extracted_metric['team']
            newly_formatted.update({extracted_team: extracted_metric})

            self.cached_teams[int(team)] = newly_formatted

            return newly_formatted

    def format_team(self, team_number, placement):
        data = self.get_team_metrics(team_number)

        new_data = data[int(team_number)]

        return {f'{placement}_{key}': new_data[key] for key in new_data}

    def format_match(self, match):
        red1 = self.format_team(match[3][3:], 'red1')
        red2 = self.format_team(match[4][3:], 'red2')
        red3 = self.format_team(match[5][3:], 'red3')
        blue1 = self.format_team(match[0][3:], 'blue1')
        blue2 = self.format_team(match[1][3:], 'blue2')
        blue3 = self.format_team(match[2][3:], 'blue3')

        team_metrics = {'red1': int(match[0][3:])} | red1 | {'red2': int(match[1][3:])} | red2 | {
            'red3': int(match[2][3:])} | red3 | {'blue1': int(match[3][3:])} | blue1 | {
                           'blue2': int(match[4][3:])} | blue2 | {'blue3': int(match[5][3:])} | blue3

        return team_metrics

    def get_statbotics_match_prediction(self, match_key):
        match_info = self.sb.get_match(match_key)
        return [match_info['epa_winner'], match_info['epa_win_prob']]

