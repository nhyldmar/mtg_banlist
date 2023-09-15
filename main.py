import commander_spellbook_wrapper
import scryfall_wrapper

import re


card_regex_pattern = re.compile(r"(?<amount>\d{1,2})x? (?<name>.*)")


class Deck:
    """Deck container for assessing validity."""
    validity_dict = dict.fromkeys([
        "100 card maindeck",
        "no duplicates",
        "commander keyword",
        "mana turbo",
        "two card combo",
        "cheap generic tutor",
        "banned in modern",
        "banned in legacy",
        "empty library",
        "zero mana counterspells",
        "forced draw",
        "in banlist"
    ])

    cards = []

    def __init__(self, decklist):
        self.cards = self.deck_string_to_card_list(decklist)

    @staticmethod
    def deck_string_to_card_list(deck_string):
        re.findall()

    def print_validity(decklist):
        """Given a deck in '1x Card Name' format, print if it is valid or what is invalid."""


    def is_valid_deck(decklist):
        """Given a deck in '1x Card Name' format, return a boolean of if it's valid."""


    def get_deck_validity(decklist):
        """Given a deck in '1x Card Name' format, return a dictionary of validitity checks."""


    def is_100_card_maindeck(deck):
        return False
