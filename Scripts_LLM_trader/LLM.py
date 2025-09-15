"""Created on 09-14-2025 16:36:06 @author: denizyalimyilmaz"""
import logging
from matplotlib import text
import pandas as pd
import json
from openai import OpenAI
import os
from fatwoman_api_setup import OPENAI_API_KEY
from fatwoman_dir_setup import LLM_data_path_finnhub_file , LLM_data_path
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log

# Abstract Parent Class
class base_LLM:
    def __init__(self, name ='unnamed_LLM'):
        print(f"Initializing %s" %name)
        self.prompt = ""
        self.context = ""
        self.model = "gpt-4o"  # gpt-4o, gpt-4o-mini, gpt-4-turbo
        self.allowed_tools = []
        self.name = name

    def _getResponse(self, prompt=None, context=None, justMessage=True, dummy = True):
        filename = 'LLM_Name_' + self.name + '_response.txt'
        write_loc = os.path.join(LLM_data_path, filename)
        if dummy:
            print('Response reading from to %s' %write_loc)
            with open(write_loc, "r") as file: fin_response = file.read()
        else:
            print(f"Getting Response from %s" %self.name)
            if prompt:  self.prompt = prompt
            if context: self.context = context

            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.context},
                    {"role": "user", "content": self.prompt},
                ],
            )
            if justMessage: 
                fin_response = response.choices[0].message.content 
            else: 
                fin_response = response
            print('Response got, writing to %s' %write_loc)
            with open(write_loc, "w") as file: file.write(fin_response)
        return fin_response

class consulter_LLM(base_LLM):
    def __init__(self, name ='consulter_1'):
        super().__init__(name)
        self.allowed_tools = ["get_headlines"]

        self.prompt = """
            please provide me with top 5 trade ideas based on news of today. I will buy and hold these till end of day and close them next morning.
        """
        self.context = f"""
            You are the Consulter agent.
            Your job is to analyze financial news headlines and produce structured suggestions for portfolio actions. Limit the actions to 'buy' and only in US stocks. 
            You read the news provided to you and output only ticker names and nothing else, delimit them with comma.
            Here's headlines of today: {self.get_headlines()}
            """
    def get_headlines(self):
        print(f"Getting headlines: {LLM_data_path_finnhub_file}")
        df = pd.read_csv(LLM_data_path_finnhub_file)
        csv_as_string = df.to_string(index=False)
        return csv_as_string

    def work(self):
        return self._getResponse()

if __name__ == "__main__":
    consulter_LLM_object = consulter_LLM()
    response = consulter_LLM_object.work()
    # print(response)


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
