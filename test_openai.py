import os
import openai

# Use the API key from your environment
openai.api_key = os.getenv('OPENAI_API_KEY')

# Test the API with GPT-4
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Create a Python script that prints the current date and time"}
    ]
)

print("API Response:", response.choices[0].message.content)
