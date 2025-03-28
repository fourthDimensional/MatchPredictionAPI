import os
import pickle

import pandas as pd
from keras.models import load_model

os.environ["KERAS_BACKEND"] = "TORCH"

new_column_order = [
    'blue1', 'blue1_auto_epa_end', 'blue1_count', 'blue1_country_epa_percentile', 'blue1_country_epa_rank',
    'blue1_district_epa_percentile', 'blue1_district_epa_rank', 'blue1_endgame_epa_end', 'blue1_epa_conf_1',
    'blue1_epa_conf_2', 'blue1_epa_diff', 'blue1_epa_pre_champs', 'blue1_epa_start', 'blue1_losses',
    'blue1_norm_epa_end', 'blue1_rp_1_epa', 'blue1_rp_2_epa', 'blue1_state_epa_percentile', 'blue1_state_epa_rank',
    'blue1_teleop_epa_end', 'blue1_ties', 'blue1_total_epa_percentile', 'blue1_total_epa_rank', 'blue1_unitless_epa_end',
    'blue1_winrate', 'blue1_wins', 'blue2', 'blue2_auto_epa_end', 'blue2_count', 'blue2_country_epa_percentile',
    'blue2_country_epa_rank', 'blue2_district_epa_percentile', 'blue2_district_epa_rank', 'blue2_endgame_epa_end',
    'blue2_epa_conf_1', 'blue2_epa_conf_2', 'blue2_epa_diff', 'blue2_epa_pre_champs', 'blue2_epa_start', 'blue2_losses',
    'blue2_norm_epa_end', 'blue2_rp_1_epa', 'blue2_rp_2_epa', 'blue2_state_epa_percentile', 'blue2_state_epa_rank',
    'blue2_teleop_epa_end', 'blue2_ties', 'blue2_total_epa_percentile', 'blue2_total_epa_rank', 'blue2_unitless_epa_end',
    'blue2_winrate', 'blue2_wins', 'blue3', 'blue3_auto_epa_end', 'blue3_count', 'blue3_country_epa_percentile',
    'blue3_country_epa_rank', 'blue3_district_epa_percentile', 'blue3_district_epa_rank', 'blue3_endgame_epa_end',
    'blue3_epa_conf_1', 'blue3_epa_conf_2', 'blue3_epa_diff', 'blue3_epa_pre_champs', 'blue3_epa_start', 'blue3_losses',
    'blue3_norm_epa_end', 'blue3_rp_1_epa', 'blue3_rp_2_epa', 'blue3_state_epa_percentile', 'blue3_state_epa_rank',
    'blue3_teleop_epa_end', 'blue3_ties', 'blue3_total_epa_percentile', 'blue3_total_epa_rank', 'blue3_unitless_epa_end',
    'blue3_winrate', 'blue3_wins', 'red1', 'red1_auto_epa_end', 'red1_count', 'red1_country_epa_percentile',
    'red1_country_epa_rank', 'red1_district_epa_percentile', 'red1_district_epa_rank', 'red1_endgame_epa_end',
    'red1_epa_conf_1', 'red1_epa_conf_2', 'red1_epa_diff', 'red1_epa_pre_champs', 'red1_epa_start', 'red1_losses',
    'red1_norm_epa_end', 'red1_rp_1_epa', 'red1_rp_2_epa', 'red1_state_epa_percentile', 'red1_state_epa_rank',
    'red1_teleop_epa_end', 'red1_ties', 'red1_total_epa_percentile', 'red1_total_epa_rank', 'red1_unitless_epa_end',
    'red1_winrate', 'red1_wins', 'red2', 'red2_auto_epa_end', 'red2_count', 'red2_country_epa_percentile',
    'red2_country_epa_rank', 'red2_district_epa_percentile', 'red2_district_epa_rank', 'red2_endgame_epa_end',
    'red2_epa_conf_1', 'red2_epa_conf_2', 'red2_epa_diff', 'red2_epa_pre_champs', 'red2_epa_start', 'red2_losses',
    'red2_norm_epa_end', 'red2_rp_1_epa', 'red2_rp_2_epa', 'red2_state_epa_percentile', 'red2_state_epa_rank',
    'red2_teleop_epa_end', 'red2_ties', 'red2_total_epa_percentile', 'red2_total_epa_rank', 'red2_unitless_epa_end',
    'red2_winrate', 'red2_wins', 'red3', 'red3_auto_epa_end', 'red3_count', 'red3_country_epa_percentile',
    'red3_country_epa_rank', 'red3_district_epa_percentile', 'red3_district_epa_rank', 'red3_endgame_epa_end',
    'red3_epa_conf_1', 'red3_epa_conf_2', 'red3_epa_diff', 'red3_epa_pre_champs', 'red3_epa_start', 'red3_losses',
    'red3_norm_epa_end', 'red3_rp_1_epa', 'red3_rp_2_epa', 'red3_state_epa_percentile', 'red3_state_epa_rank',
    'red3_teleop_epa_end', 'red3_ties', 'red3_total_epa_percentile', 'red3_total_epa_rank', 'red3_unitless_epa_end',
    'red3_winrate', 'red3_wins'
]

class MatchPrediction:
    def __init__(self, model_dir, rf_dir, scaler_dir, model_rp_dir, rf_rp_dir, scaler_rp_dir):
        self.model = load_model(model_dir, compile=False)

        with open(rf_dir, 'rb') as file:
            self.rf = pickle.load(file)

        with open(scaler_dir, 'rb') as file:
            self.sc = pickle.load(file)

        self.model_rp = load_model(model_rp_dir, compile=False)

        with open(rf_rp_dir, 'rb') as file:
            self.rf_rp = pickle.load(file)

        with open(scaler_rp_dir, 'rb') as file:
            self.sc_rp = pickle.load(file)

    def preprocess_data(self, raw, convert=True):
        if convert:
            dataframe = pd.DataFrame(raw, index=[0])
        else:
            dataframe = raw

        # Normalize the data
        X = dataframe.fillna(0)

        X = X.reindex(columns=new_column_order)

        X_normalized = self.sc.transform(X)
        X_normalized_df = pd.DataFrame(X_normalized, columns=X.columns)

        # Select features based on feature importance
        feature_importance_dict = dict(zip(X.columns, self.rf.feature_importances_))
        sorted_features = sorted(feature_importance_dict.items(), key=lambda item: item[1], reverse=True)
        features_to_use = [feat[0] for feat in sorted_features[:-130]]

        X_reduced = X_normalized_df[features_to_use]

        print(X_reduced.columns.to_list())

        X_reduced.to_csv('X_reduced.csv')

        return X_reduced

    def preprocess_data_rp(self, raw, convert=True):
        if convert:
            dataframe = pd.DataFrame(raw, index=[0])
        else:
            dataframe = raw

        # Normalize the data
        X = dataframe.fillna(0)
        X_normalized = self.sc_rp.transform(X)
        X_normalized_df = pd.DataFrame(X_normalized, columns=X.columns)

        # Select features based on feature importance
        feature_importance_dict = dict(zip(X.columns, self.rf_rp.feature_importances_))
        sorted_features = sorted(feature_importance_dict.items(), key=lambda item: item[1], reverse=True)
        features_to_use = [feat[0] for feat in sorted_features[:-89]]

        X_reduced = X_normalized_df[features_to_use]

        X_reduced.to_csv('X_reduced_rp.csv')

        return X_reduced

    def predict(self, preprocessed, focus=2):
        if focus == 2:
            preprocessed = self.preprocess_data(preprocessed)

        if focus == 2:
            return self.model.predict(preprocessed)[0]
        elif focus == 1:
            return self.model.predict(preprocessed)

    def predict_rp(self, preprocessed, focus=2):
        if focus == 2:
            preprocessed = self.preprocess_data_rp(preprocessed)

        if focus == 2:
            return self.model_rp.predict(preprocessed)[0]
        elif focus == 1:
            return self.model_rp.predict(preprocessed)
