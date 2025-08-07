import os

from dotenv import load_dotenv


load_dotenv()

MODEL_NAME = os.getenv('MODEL_NAME', 'google/gemini-2.5-flash')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
CACHE_SIZE = os.getenv('CACHE_SIZE', 10**4)
