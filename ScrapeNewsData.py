# Packages runterladen

!pip install openai
import os
from openai import AzureOpenAI
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

# Verbindung zu ChatGPT
os.environ['AZURE_OPENAI_KEY'] = '65ee6d36768e44b894d04c922e6cbe7a'
os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://mbeopenai.openai.azure.com/'

client = AzureOpenAI(
  api_key = os.getenv("AZURE_OPENAI_KEY"),
  api_version = "2023-05-15",
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
)
