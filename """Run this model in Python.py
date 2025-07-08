"""Run this model in Python

> pip install openai
"""
from openai import OpenAI

client = OpenAI(
    base_url = "http://127.0.0.1:11434/v1",
    api_key = "unused", # required for the API but not used
)

response = client.chat.completions.create(
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "INSERT_INPUT_HERE",
                },
            ],
        },
    ],
    model = "deepseek-r1:32b",
    max_tokens = 80000,
    temperature = 0.6,
)

print(response.choices[0].message.content)