import os

import openai
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


def completions(prompt, max_tokens=300, engine="text-davinci-003"):
    completion = openai.Completion.create(engine=engine, prompt=prompt, max_tokens=max_tokens)
    if completion.choices:
        return completion.choices[0].text
    else:
        return f"No completion found for {prompt}"


def image_creation(prompt, number_of_images=4, image_size="512x512"):
    return openai.Image.create(prompt=prompt, n=number_of_images, size=image_size)
