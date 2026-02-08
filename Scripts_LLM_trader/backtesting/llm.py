from fatwoman_api_setup import OPENAI_API_KEY
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import LLM_data_path_finnhub_file, LLM_data_path
import os
from openai import OpenAI
from cache_db import log_chat_interaction, fetch_cached_row
 

class LLM:
    def __init__(self):
        self.model="gpt-4o-mini"

    def work(self, prompt, context):
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
                recycled=True
            )
            with open(self.write_loc, "w", encoding="utf-8") as file:
                file.write(cache["response"])

            return cache["response"]
        

        # If not found in cache, get new response from LLM, save it and return it
        response, tokens_input, tokens_output = self.__getResponse(
            prompt=prompt, context=context
        )      
 
        return response
 

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




def flow_26_1(data:dict, ticker:str):
    agent = LLM()

    prompt = f"Can you tell me whether I should buy or sell my asset for {ticker} based on these headlines: {data["headlines"]}"
    context = f"""
    Return ONLY a CSV text response. No JSON. No markdown. No extra lines before or after the CSV.

    Style rules:
    - No emojis, filler, hype, soft asks, conversational transitions, call-to-action appendixes.
    - Do not ask questions. Do not add suggestions beyond the required output.
    - Terminate immediately after the CSV.

    Task:
    Analyze the provided financial news headlines and output a structured assessment for the given ticker.

    CSV requirements:
    - Exactly 1 header row and 1 data row.
    - Use comma as delimiter.
    - Do not quote fields unless required by CSV rules (only if a field contains a comma, quote, or newline).
    - confidence must be an integer 0-100.
    - tendency must be one of: bullish, bearish, neutral.
    - ticker must be the exact ticker symbol provided.

    Output format (must match exactly):
    ticker,tendency,confidence
    {ticker},{'{tendency}'},{'{confidence}'}
    """

    response = agent.work(prompt=prompt, context=context)

    return response

if __name__ == "__main__": 
    data = {"headlines": "hello apple will fall hahaha"}
    ticker = "AMZN"
    response = flow_26_1(ticker=ticker, data=data)
    print("asds",response)
