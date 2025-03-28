import os
import pickle

import pandas as pd
from keras.models import load_model

os.environ["KERAS_BACKEND"] = "TORCH"

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
        X_normalized = self.sc.transform(X)
        X_normalized_df = pd.DataFrame(X_normalized, columns=X.columns)

        # Select features based on feature importance
        feature_importance_dict = dict(zip(X.columns, self.rf.feature_importances_))
        sorted_features = sorted(feature_importance_dict.items(), key=lambda item: item[1], reverse=True)
        features_to_use = [feat[0] for feat in sorted_features[:-89]]

        X_reduced = X_normalized_df[features_to_use]

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
        features_to_use = [feat[0] for feat in sorted_features[:-130]]

        X_reduced = X_normalized_df[features_to_use]

        X_reduced.to_csv('X_reduced.csv')

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

