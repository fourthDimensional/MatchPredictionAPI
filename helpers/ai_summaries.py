import groq


class GroqSummaries:
    def __init__(self, api_key):
        self.api_key = api_key

        self.client = groq.Groq(api_key=api_key)

    def chat_completion(self, messages, model="llama3-70b-8192"):
        return self.client.chat.completions.create(
            messages=messages,
            model=model,
        ).choices[0].message.content

    def predict_match(self, match):
        print(match)
        role = ("You are a data expert on the First Robotics Competiton. You are predicting the outcome of a match. "
                "You will get a CSV file with statistics of each of the six teams participating in the match. The "
                "statistics include the team's EPA at the start of the season, before the championship, and at the "
                "end of the season. The statistics also include the team's win rate, total EPA rank, and percentile "
                "rank in the country, state, and district. EPA means Expected Points Added. You will use this data to "
                "predict the outcome of the"
                "match. Each field is prefaced with the team number and the placement on the alliance (red1, red2, "
                "red3, blue1, blue2, blue3). The prediction will be a string of either 'red', 'blue', or 'draw'."
                "In your prediction, explain your reasoning and the importance of the features you used."
                f"Secondly, refer to red1 as {match['red1'][0]}, red2 as {match['red2'][0]}, red3 as {match['red3'][0]}, "
                f"blue1 as {match['blue1'][0]}, blue2 as {match['blue2'][0]}, and blue3 as {match['blue3'][0]}. ")

        # return self.chat_completion([{"role": "user", "content": role + str(match)}])
        return ''
