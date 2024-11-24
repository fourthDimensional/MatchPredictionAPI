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

    def get_general_match_info(self, event=None, red=None, blue=None, offset=1):
        if event is not None:
            data = self.tba.event_matches(event=event, simple=True)

            match_index = next((i for i, match in enumerate(data) if match['actual_time'] is None), None)

            if match_index is not None:
                match_index += offset

                if 0 <= match_index < len(data):
                    data = data[match_index]
                else:
                    print("Offset leads to an invalid match index.")
                    return None
            else:
                print("No match without actual time found.")
                return None

            red = data['alliances']['red']['team_keys']
            blue = data['alliances']['blue']['team_keys']
        else:
            # Ensures machine learning model input shape is correct if function was given lists of teams instead of
            # an event. Might change this later or split into two functions.
            data = {'key': 0, 'event_key': 0, 'comp_level': 0, 'set_number': 0, 'match_number': 0}

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
        }

        result = {**teams_sides_dict, **pre_match_fields}

        return result, red, blue

    def get_event_rankings(self, event='2024ksla'):
        rankings = self.tba.event_rankings(event)
        actual = {}
        for ranking in rankings['rankings']:
            actual[int(ranking['team_key'][3:])] = ranking['rank']
        return actual
