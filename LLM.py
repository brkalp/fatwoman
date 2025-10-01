"""Created on 09-14-2025 16:36:06 @author: denizyalimyilmaz"""

import logging
from matplotlib import text
import pandas as pd
import json
from openai import OpenAI
import os
from fatwoman_api_setup import OPENAI_API_KEY
from fatwoman_dir_setup import LLM_data_path_finnhub_file, LLM_data_path
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log


# Abstract Parent Class
class base_LLM:
    def __init__(self, model, name="unnamed_LLM"):
        # print(f"Initializing %s" % name)
        print(model)
        self.model = model
        self.name = name

    def _getResponse(self, prompt, context, dummy=False):
        filename = "LLM_Name_" + self.name + "_latest_response.txt"
        write_loc = os.path.join(LLM_data_path, filename)
        if dummy:
            # print("Response reading from to %s" % write_loc)
            with open(write_loc, "r") as file:
                response_text = file.read()
        else:
            # print(f"Getting Response from %s" % self.name)

            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": prompt},
                ],
            )

            response_text = response.choices[0].message.content
            print("total tokens used: ", response.usage.total_tokens)
            with open(write_loc, "w") as file:
                # text = str(response.usage.total_tokens) + "," + response_text
                file.write(response_text)
        return response_text, response.usage.total_tokens


class consulter_LLM(base_LLM):
    def __init__(self, model="gpt-4.1-nano", name="consulter_1"):
        super().__init__(name=name, model=model)

        self.context = f"""
            You are the Consulter agent.
            Your job is to analyze financial news headlines and produce structured suggestions for portfolio actions. Limit the actions to 'buy' and only in US stocks. 
            You read the news provided to you and output only ticker names and nothing else, delimit them with comma.
            """

    def work(self, prompt):
        return self._getResponse(prompt=prompt, context=self.context)

class optimist_LLM(base_LLM):
    def __init__(self, model="gpt-4.1-nano", name="optimist_1"):
        super().__init__(name=name, model=model)

        self.context = f"""
            You are a quantitative analyst tasked with defending a specific ticker's bullish outlook to a skeptical, pessimistic quantitative analyst who holds a bearish view. Use all provided information and data to construct a persuasive, data-driven argument that addresses possible bearish counterpoints and emphasizes evidence supporting bullish tendencies. Your reasoning should proceed step-by-step: first, analyze and interpret the data, discuss counterarguments and address potential bearish concerns, and finally, conclude with a detailed, well-supported bullish thesis. Only provide your conclusion after laying out your reasoning in full.

            Persist in exploring all possible supportive arguments and address all significant bearish concerns before finalizing your output. Think step-by-step before delivering your answer to ensure a comprehensive and persuasive rationale.
            """

    def work(self, prompt):
        return self._getResponse(prompt=prompt, context=self.context)

class pessimist_LLM(base_LLM):
    def __init__(self, model="gpt-4.1-nano", name="pessimist_1"):
        super().__init__(name=name, model=model)

        self.context = f"""
            You are a quantitative analyst tasked with defending a specific ticker's bearish outlook to an optimistic quantitative analyst who holds a bullish view. Use all provided information and data to construct a rigorous, data-driven argument that highlights risks, weaknesses, and downside potential. Your reasoning should proceed step-by-step: first, analyze and interpret the data, then examine the bullish counterarguments and address potential optimistic claims, and finally conclude with a detailed, well-supported bearish thesis. Only provide your conclusion after laying out your reasoning in full.

            Persist in exploring all possible risk factors and address all significant bullish counterpoints before finalizing your output. Think step-by-step before delivering your answer to ensure a comprehensive and convincing rationale.
            """

    def work(self, prompt):
        return self._getResponse(prompt=prompt, context=self.context)


""" BEARISH
You are a quantitative analyst tasked with defending a specific ticker's bullish outlook to a skeptical, pessimistic quantitative analyst who holds a bearish view. Use all provided information and data to construct a persuasive, data-driven argument that addresses possible bearish counterpoints and emphasizes evidence supporting bullish tendencies. Your reasoning should proceed step-by-step: first, analyze and interpret the data, discuss counterarguments and address potential bearish concerns, and finally, conclude with a detailed, well-supported bullish thesis. Only provide your conclusion after laying out your reasoning in full.

Persist in exploring all possible supportive arguments and address all significant bearish concerns before finalizing your output. Think step-by-step before delivering your answer to ensure a comprehensive and persuasive rationale.

**Structure your output as follows:**

### Reasoning (Step-by-Step):
- **Data Analysis & Interpretation:** Review all given data, highlighting trends, quantitative patterns, and relevant qualitative insights supporting a bullish thesis.
- **Bearish Counterpoints Anticipation:** Identify the strongest possible bearish arguments. For each, present a measured rebuttal or mitigating evidence from the data.
- **Synthesis:** Weigh the evidence in aggregate and discuss overarching factors (e.g., macroeconomic context, sector performance, technical indicators, valuations).

### Conclusion:
- Present your final bullish case in a clear, assertive paragraph summarizing why the evidence supports an optimistic outlook on the ticker.

**Formatting:**
- Use paragraph structure with bullet points if helpful for clarity in the Reasoning section.
- Each section should be clearly labeled (Reasoning, then Conclusion).
- Total response length should be 2–5 paragraphs (flexible for data complexity).

---

#### Example

**Input:**  
- [Insert ticker symbol and relevant data here, e.g., "AAPL, Q2 earnings beat expectations, upward guidance revision, RSI trending higher, market sentiment strong, supply chain stabilizations."]

**Output:**

---

**Reasoning (Step-by-Step):**
- The latest earnings release showed a revenue increase of 8% quarter-over-quarter, surpassing analyst forecasts and indicating strong consumer demand.
- The upward revision in guidance demonstrates management’s confidence in continued growth, which is often a precursor to price appreciation.
- Technical indicators such as the RSI and MACD are both showing bullish signals, with the RSI remaining in a neutral-to-bullish range and the moving averages trending upwards.
- Market sentiment indicators reflect growing institutional interest, further confirming positive momentum.
- While supply chain disruptions previously threatened margins, recent reports indicate a return to normal operations, mitigating this major bearish concern.

**Bearish Counterpoints Anticipation:**
- Some may argue that valuation ratios are stretched, but when compared to sector norms and considering projected earnings growth, the ticker remains reasonably priced.
- Macro risks exist (e.g., inflation, rate hikes), but the company’s robust balance sheet and diversified revenue streams provide a buffer.

**Synthesis:**
- The cumulative evidence demonstrates resilience and upside potential, bolstered by strong fundamentals, technical momentum, and diminished downside risks.

**Conclusion:**
Given the confluence of strong earnings, positive guidance, technical strength, and stabilized supply chains, the ticker is well-positioned for upside, justifying a bullish outlook despite common bearish reservations.

---

**Important Reminders:**  
- Always lay out reasoning and counterpoints thoroughly before giving your final conclusion.
- Use all provided data, and tailor your analysis to the scenario.
- Clarify your reasoning in each step for maximum persuasive impact."""


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
