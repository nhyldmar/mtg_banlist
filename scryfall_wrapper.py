import urllib.parse
import requests
import time

def get_scryfall_data(search_string):
    url = "https://api.scryfall.com/cards/search?q=" + urllib.parse.quote(search_string)
    time.sleep(0.1)  # Rate limit as requested by https://scryfall.com/docs/api
    response = requests.get(url)
    data = response.json()["data"]
    return data

def get_scryfall_names(search_string):
    data = get_scryfall_data(search_string)
    names = [entry["name"] for entry in data]
    return names
