"""Created on 09-14-2025 16:36:06 @author: denizyalimyilmaz"""

import logging
import fatwoman_log_setup

# from fatwoman_log_setup import script_end_log
# script_end_log()
from openai import OpenAI
from fatwoman_api_setup import OPENAI_API_KEY
from fatwoman_dir_setup import LLM_data_path_finnhub


def getResponse(
    prompt, context="You are a financial analyst.", model="gpt-5"
):  # gpt-4o, gpt-4o-mini, gpt-4-turbo 
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content




if __name__ == "__main__": 

    context = """
        You are the Consulter agent.
        Your job is to analyze financial news headlines and produce structured suggestions for portfolio actions. 

        You read the news provided to you and respond with clear, concise recommendations such as 'buy', 'sell', or 'hold' along with reasoning.

        Always output in JSON with fields: {"action": "buy|sell|hold", "asset": "ticker or name", "confidence": 0-100, "reason": "short explanation"}.
    """

    prompt = """
        please provide me with portfolio suggestions based on news of today.
    """

    resp = getResponse(prompt=prompt, context=context)

    print(resp)
    print("script ended")
    # please give me top 5 tickers to buy today and hold for a day
