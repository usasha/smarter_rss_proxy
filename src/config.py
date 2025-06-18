import os

from dotenv import load_dotenv


load_dotenv()

MODEL_NAME = os.getenv('MODEL_NAME', 'google/gemini-2.5-flash-preview-05-20')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
