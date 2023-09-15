import urllib.parse
import requests
import time

def get_scryfall_names(search_string):
    url = "https://api.scryfall.com/cards/search?q=" + urllib.parse.quote(search_string)
    time.sleep(0.1)  # Rate limit as requested by https://scryfall.com/docs/api
    response = requests.get(url)
    names = [entry["name"] for entry in response.json()["data"]]

    return names
