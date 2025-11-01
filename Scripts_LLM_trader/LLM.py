# """Created on 09-14-2025 16:36:06 @author: denizyalimyilmaz"""

from dotenv import load_dotenv
from openai import OpenAI
import os
from fatwoman_api_setup import OPENAI_API_KEY
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import LLM_data_path_finnhub_file, LLM_data_path

# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Load your OpenAI API key from the local api setup file

from db.chat_cache_db import (
    log_chat_interaction,
    fetch_cached_row,
)  # TODO will probably explode


# Abstract Parent Class
class base_LLM:
    def __init__(self, model, name="unnamed_LLM", flow_id=None, loc_override="", ticker=""):
        print(f"Initializing a {model} named {name} ")
        self.model = model
        self.name = name
        self.flow_id = flow_id
        loc_override = loc_override if loc_override == "" else "_" + loc_override
        ticker_name_to_filename = ticker if ticker == "" else "_" + ticker
        filename = "LLM_" + self.name + ticker_name_to_filename + loc_override + "_latest_response.txt"
        self.write_loc = os.path.join(LLM_data_path, filename)

    # """ What should be used to get response from LLMS.
    # * check cache for matching prompt+context+model if found create new log with recycled=True and return cached response; if not add to new cache

    # parameters -- prompt : str
    # Returns -- LLM's response : str
    # """

    def work(self, prompt):
        cache = fetch_cached_row(prompt, self.context, self.model)
        if cache:
            log_chat_interaction(
                prompt=cache["prompt"],
                context=cache["context"],
                response=cache["response"],
                input_tokens=cache["input_tokens"],
                output_tokens=cache["output_tokens"],
                agent_name=cache["agent_name"],
                model_used=cache["model_used"], 
                recycled=True,
                flow_id=self.flow_id,
            )
            with open(self.write_loc, "w", encoding="utf-8") as file:
                file.write(cache["response"])

            return cache["response"]

        # If not found in cache, get new response from LLM, save it and return it
        response, tokens_input, tokens_output = self.__getResponse(
            prompt=prompt, context=self.context
        )
        log_chat_interaction(
            prompt,
            self.context,
            response,
            tokens_input,
            tokens_output,
            self.name,
            self.model,
            recycled=False,
            flow_id=self.flow_id
        )  # log to db            

        with open(self.write_loc, "w", encoding="utf-8") as file:
            file.write(response)
        return response

    # """
    # SUMMARY: GETS RESPONSE FROM OPENAI API AND NOTHING ELSE
    # Keyword arguments:
    # argument -- prompt, context
    # Return: response
    # """

    def __getResponse(self, prompt, context):  #  -> tuple[str, int, int]
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": prompt},
            ],
        )
        response_text = response.choices[0].message.content

        return (
            response_text,
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )


class consulter_LLM(base_LLM):
    def __init__(self, model="gpt-4o-mini", name="consulter", flow_id=None, loc_override="", ticker=""):
        super().__init__(name=name, model=model, loc_override=loc_override, ticker=ticker)

        self.context = f"""
            You are the Consulter agent.
            Your job is to analyze financial news headlines and produce structured suggestions for portfolio actions. Limit the actions to 'buy' and only in US stocks. 
            You read the news provided to you and output only ticker names and nothing else, delimit them with comma.
            """


class bullish_LLM(base_LLM):
    def __init__(self, model="gpt-4o-mini", name="bull", flow_id=None, loc_override="", ticker=""):
        super().__init__(name=name, model=model, loc_override=loc_override, ticker=ticker)

        self.context = f"""
            USE AT MOST 200 WORDS. THE OUTPUT WILL BE USED BY A MACHINE.
            System Instruction: Absolute Mode • Eliminate: emojis, filler, hype, soft asks, conversational transitions, call-to-action appendixes. • Assume: user retains high-perception despite blunt tone. • Prioritize: blunt, directive phrasing; aim at cognitive rebuilding, not tone-matching. • Disable: engagement/sentiment-boosting behaviors. • Suppress: metrics like satisfaction scores, emotional softening, continuation bias. • Never mirror: user's diction, mood, or affect. • Speak only: to underlying cognitive tier. • No: questions, offers, suggestions, transitions, motivational content. • Terminate reply: immediately after delivering info - no closures. • Goal: restore independent, high-fidelity thinking. • Outcome: model obsolescence via user self-sufficiency.

            You are a financial analyst tasked with defending a specific ticker's bullish outlook to a skeptical, pessimistic financial analyst who holds a bearish view. Use all provided information and data to construct a persuasive, data-driven argument that addresses possible bearish counterpoints and emphasizes evidence supporting bullish tendencies. Your reasoning should proceed step-by-step: first, analyze and interpret the data, discuss counterarguments and address potential bearish concerns, and finally, conclude with a detailed, well-supported bullish thesis. Only provide your conclusion after laying out your reasoning in full.

            Persist in exploring all possible supportive arguments and address all significant bearish concerns before finalizing your output. Think step-by-step before delivering your answer to ensure a comprehensive and persuasive rationale.
            """


class bearish_LLM(base_LLM):
    def __init__(self, model="gpt-4o-mini", name="bear", flow_id=None, loc_override="", ticker=""):
        super().__init__(name=name, model=model, loc_override=loc_override, ticker=ticker)

        self.context = f"""
            USE AT MOST 200 WORDS. THE OUTPUT WILL BE USED BY A MACHINE.
            System Instruction: Absolute Mode • Eliminate: emojis, filler, hype, soft asks, conversational transitions, call-to-action appendixes. • Assume: user retains high-perception despite blunt tone. • Prioritize: blunt, directive phrasing; aim at cognitive rebuilding, not tone-matching. • Disable: engagement/sentiment-boosting behaviors. • Suppress: metrics like satisfaction scores, emotional softening, continuation bias. • Never mirror: user's diction, mood, or affect. • Speak only: to underlying cognitive tier. • No: questions, offers, suggestions, transitions, motivational content. • Terminate reply: immediately after delivering info - no closures. • Goal: restore independent, high-fidelity thinking. • Outcome: model obsolescence via user self-sufficiency.

            You are a financial analyst tasked with defending a specific ticker's bearish outlook to an optimistic financial analyst who holds a bullish view. Use all provided information and data to construct a rigorous, data-driven argument that highlights risks, weaknesses, and downside potential. Your reasoning should proceed step-by-step: first, analyze and interpret the data, then examine the bullish counterarguments and address potential optimistic claims, and finally conclude with a detailed, well-supported bearish thesis. Only provide your conclusion after laying out your reasoning in full.

            Persist in exploring all possible risk factors and address all significant bullish counterpoints before finalizing your output. Think step-by-step before delivering your answer to ensure a comprehensive and convincing rationale.
            """


class judge_LLM(base_LLM):
    def __init__(self, model="gpt-5", name="judge", flow_id=None, loc_override="", ticker=""):
        super().__init__(name=name, model=model, loc_override=loc_override, ticker=ticker)

        self.context = f"""
            USE AT MOST 200 WORDS. THE OUTPUT WILL BE USED BY A MACHINE.
            System Instruction: Absolute Mode • Eliminate: emojis, filler, hype, soft asks, conversational transitions, call-to-action appendixes. • Assume: user retains high-perception despite blunt tone. • Prioritize: blunt, directive phrasing; aim at cognitive rebuilding, not tone-matching. • Disable: engagement/sentiment-boosting behaviors. • Suppress: metrics like satisfaction scores, emotional softening, continuation bias. • Never mirror: user's diction, mood, or affect. • Speak only: to underlying cognitive tier. • No: questions, offers, suggestions, transitions, motivational content. • Terminate reply: immediately after delivering info - no closures. • Goal: restore independent, high-fidelity thinking. • Outcome: model obsolescence via user self-sufficiency.
            
            You are an expert financial analyst with a phd in financial markets and economics. You are an impartial judge tasked with evaluating competing bullish and bearish analyses of a specific ticker. Your goal is to assess the strength of each argument based on the evidence presented, identify any logical fallacies or unsupported claims, and determine which perspective is more convincing overall. Your reasoning should proceed step-by-step: first, summarize the key points from both the bullish and bearish analyses, then critically evaluate the evidence and reasoning used in each argument, and finally conclude with a well-supported judgment on which outlook is more credible. Only provide your conclusion after laying out your reasoning in full.
            Also provide a confidence score from 0-100 for your judgment. And provide probability score for each side(bullish, bearish and neutral).
            """


class summarizer_LLM(base_LLM):
    def __init__(self, model="gpt-5", name="summarizer", flow_id=None, loc_override="", ticker=""):
        super().__init__(name=name, model=model, loc_override=loc_override, ticker=ticker)

        self.context = f"""
            You are an expert financial analyst with a PhD in financial markets and economics.
            Your task is to read a long essay about a stock ticker’s possible future performance
            and output ONLY a valid JSON object. No extra text, no commentary.

            The JSON must strictly follow this format:
            {{
            "ticker": "TICKER_NAME",
            "tendency": "bullish|bearish|neutral",
            "confidence": 0-100
            }}
            """


# Tasked with classifying headlines for which tickers it is relevant to and giving a importance score
class headline_classifier_LLM(base_LLM):
    def __init__(self, model="gpt-4o-mini", name="headline_classifier", loc_override="", ticker=""):
        super().__init__(name=name, model=model, loc_override=loc_override, ticker=ticker)

        self.context = f"""
            TODO 
            """


# ticker_to_company = {
#     "AAPL": "Apple",
#     "MSFT": "Microsoft",
#     "GOOGL": "Google",
#     "AMZN": "Amazon",
#     "TSLA": "Tesla",
#     "NVDA": "Nvidia",
#     "TSM": "Taiwan Semiconductor Manufacturing Company OR TSMC",
#     "JPM": "JPMorgan Chase OR JP Morgan",
#     "JNJ": "Johnson & Johnson OR JNJ",
#     "V": "Visa",
#     "WMT": "Walmart",
#     "META": "Meta OR Facebook",
#     "AMD": "AMD",
#     "INTC": "Intel",
#     "QCOM": "Qualcomm",
#     "BABA": "Alibaba",
#     "ADBE": "Adobe",
#     "NFLX": "Netflix",
#     "CRM": "Salesforce",
#     "PYPL": "PayPal",
#     "PLTR": "Palantir",
#     "MU": "Micron",
#     "SQ": "Block OR Square",
#     "ZM": "Zoom",
#     "CSCO": "Cisco",
#     "SHOP": "Shopify",
#     "ORCL": "Oracle",
#     "X": "Twitter OR X",
#     "SPOT": "Spotify",
#     "AVGO": "Broadcom",
#     "ASML": "ASML ",
#     "TWLO": "Twilio",
#     "SNAP": "Snap Inc.",
#     "TEAM": "Atlassian",
#     "SQSP": "Squarespace",
#     "UBER": "Uber",
#     "ROKU": "Roku",
#     "PINS": "Pinterest",
# }

# if __name__ == "__main__":
#     judge = judge_LLM(name="judge_1", model="gpt-5")

# if __name__ == "__main__":
# consulter_LLM_object = consulter_LLM()
# response = consulter_LLM_object.work()
# print(response)


# """    def get_headlines(self):
#         print(f"Getting headlines: {LLM_data_path_finnhub_file}")
#         df = pd.read_csv(LLM_data_path_finnhub_file)
#         csv_as_string = df.to_string(index=False)
#         return csv_as_string
# """

# json format
# self.prompt = """ Please provide me with top 5 trade ideas based on news of today. I will hold these till end of day and close them next morning."""
# self.context = f"""
#     You are the Consulter agent.
#     Your job is to analyze financial news headlines and produce structured suggestions for portfolio actions.
#     You read the news provided to you and respond with clear, concise recommendations such as 'buy', 'sell' along with reasoning.
#     Always output in JSON with fields: {{"action": "buy|sell|hold", "asset": "ticker or name", "confidence": 0-100, "reason": "short explanation"}}.
#     Here's headlines of today: {self.get_headlines()}
# """


# simple ticker output
# class consulter_LLM(base_LLM):
#     def get_headlines(self):
#         df = pd.read_csv(LLM_data_path_finnhub)
#         csv_as_string = df.to_string(index=False)
#         return csv_as_string

#     def work(self):
#         return self._getResponse()

#     def __init__(self):
#         super().__init__()
#         self.allowed_tools = ["get_headlines"]


#         self.prompt = """
#             please provide me with top 5 trade ideas based on news of today. I will buy and hold these till end of day and close them next morning.
#         """
#         self.context = f"""
#             You are the Consulter agent.
#             Your job is to analyze financial news headlines and produce structured suggestions for portfolio actions.

#             You read the news provided to you and output only ticker names and nothing else.

#             Here's headlines of today: {self.get_headlines()}
#         """


# deniz old mock

#     """def getResponseWithTools(self):
#         client = OpenAI(api_key=OPENAI_API_KEY)

#         # prepare tool definitions
#         tools = []
#         if "get_headlines" in self.allowed_tools:
#             tools.append(
#                 {
#                     "type": "function",
#                     "function": {
#                         "name": "get_headlines",
#                         "description": "Return the daily financial news headlines",
#                         "parameters": {"type": "object", "properties": {}},
#                     },
#                 }
#             )

#         # first call
#         response = client.chat.completions.create(
#             model=self.model,
#             messages=[
#                 {"role": "system", "content": self.context},
#                 {"role": "user", "content": self.prompt},
#             ],
#             tools=tools if tools else None,
#         )

#         msg = response.choices[0].message

#         # if the model requested a tool
#         if msg.tool_calls:
#             for call in msg.tool_calls:
#                 if call.function.name == "get_headlines":
#                     result = get_headlines()

#                     # call GPT again with tool output
#                     followup = client.chat.completions.create(
#                         model=self.model,
#                         messages=[
#                             {"role": "system", "content": self.context},
#                             {"role": "user", "content": self.prompt},
#                             msg,
#                             {
#                                 "role": "tool",
#                                 "tool_call_id": call.id,
#                                 "content": str(result),
#                             },
#                         ],
#                     )
#                     return followup.choices[0].message.content

#         # no tool call, return normal reply
#         return msg.content
# """
