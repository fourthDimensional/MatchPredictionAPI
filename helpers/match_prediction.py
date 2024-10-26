import os
import pickle

import pandas as pd
from keras.models import load_model

from helpers.ai_summaries import GroqSummaries

os.environ["KERAS_BACKEND"] = "tensorflow"

groq = GroqSummaries(os.environ.get("GROQ_API_KEY"))

class MatchPrediction:
    def __init__(self, model_dir, rf_dir, scaler_dir):
        self.model = load_model(model_dir, compile=False)

        with open(rf_dir, 'rb') as file:
            self.rf = pickle.load(file)

        with open(scaler_dir, 'rb') as file:
            self.sc = pickle.load(file)

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
        features_to_use = [feat[0] for feat in sorted_features[:-130]]

        X_reduced = X_normalized_df[features_to_use]

        print("AI Match Prediction: " + groq.predict_match(dataframe))

        return X_reduced

    def predict(self, preprocessed, focus=2):
        if focus == 2:
            preprocessed = self.preprocess_data(preprocessed)

        if focus == 2:
            return self.model.predict(preprocessed)[0]
        elif focus == 1:
            return self.model.predict(preprocessed)

