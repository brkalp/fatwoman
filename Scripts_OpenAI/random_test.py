""" Created on 03-14-2024 21:55:57 @author: ripintheblue """
# pip install openai
import openai

openai.api_key = 'your_api_key_here'

# 
# 1. Basic Text Completion

response = openai.Completion.create(
  engine="text-davinci-003",
  prompt="Translate the following English text to French: 'Hello, world!'",
  temperature=0.7,
  max_tokens=60
)

print(response.choices[0].text.strip())
