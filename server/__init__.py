from flask import Flask
# from flask_cors import CORS
import os

app = Flask(__name__)
# CORS(app)

Env = os.environ.get('OPENAI_TOKEN')
OpenAIToken = os.environ.get('OPENAI_TOKEN')
GoogleToken = os.environ.get('GOOGLE_TOKEN')
TeleToken = os.environ.get('BOT_TOKEN')

from server import scrapper