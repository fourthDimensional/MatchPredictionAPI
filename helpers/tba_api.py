import datetime
import pandas
import tbapy


class BlueAllianceAPI:
    def __init__(self, api_key, year):
        self.tba = tbapy.TBA(api_key)
        self.year = year

    def count_played(self, team_number, event):
        team_key = 'frc' + str(team_number)
        team_matches = self.tba.team_matches(team_key, year=self.year) if event == 'all' \
            else self.tba.team_matches(team_key, event, year=self.year)
        played_matches = []

        for match in team_matches:
            if match['actual_time'] is not None:
                played_matches.append(match['key'])

        return len(played_matches)

    def get_all_matches_event(self, event):
        mass_data = self.tba.event_matches(event, simple=True)

        results = pandas.DataFrame()
        for data in mass_data:
            red = data['alliances']['red']['team_keys']
            blue = data['alliances']['blue']['team_keys']

            teams_sides_dict = {
                f'red{index + 1}': team for index, team in enumerate(red)
            }
            teams_sides_dict.update({
                f'blue{index + 1}': team for index, team in enumerate(blue)
            })

            pre_match_fields = {
                'match_key': data['key'],
                'event_key': data['event_key'],
                'match_type': data['comp_level'],
                'set_number': data['set_number'],
                'match_number': data['match_number'],
                'winning_alliance': data['winning_alliance'],
            }
            try:
                winning_side = data['winning_alliance']
            except KeyError:
                continue

            result = {**teams_sides_dict, 'winning_alliance': winning_side, **pre_match_fields}
            results = pandas.concat([results, pandas.DataFrame(result, index=[0])], axis=0)

        return results

    def get_general_match_info(self, match_key=None):
        data = self.tba.match(match_key)

        red = data['alliances']['red']['team_keys']
        blue = data['alliances']['blue']['team_keys']

        return blue + red

    def get_event_rankings(self, event='2024ksla'):
        rankings = self.tba.event_rankings(event)
        actual = {}
        for ranking in rankings['rankings']:
            actual[int(ranking['team_key'][3:])] = ranking['rank']
        return actual
