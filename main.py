import re
import os


card_regex_pattern = re.compile(r"(?P<amount>\d{1,2})x? (?P<name>.*)")


class Deck:
    """Deck container for assessing validity."""
    validity_dict = dict.fromkeys([
        # TODO: Implement these two to support companions
        # permitted duplicates
        # "100 card maindeck",
        # "no duplicates",
        "in banlist",
        "banned in legacy",
        "banned in modern",
        "forced draw",
        "commander keyword",
        "zero mana counterspells",
        "cheap generic tutor",
        "mana turbo",
        "empty library",
        # TODO: Integrate external work
        # "two card combo"
    ])

    cards = {}

    def __init__(self, deck_filename):
        with open(deck_filename) as deck_file:
            deck_string = deck_file.read()
            matches = re.findall(card_regex_pattern, deck_string)
            for (amount, name) in matches:
                self.cards[name] = amount

    def is_valid_deck(self):
        for filename in os.listdir("banlists"):
            with open(f"banlists/{filename}") as file:
                banned_cards = file.read().splitlines()
                for card in self.cards.keys():
                    if card in banned_cards:
                        print(f"'{card}' is banned by {filename}")


test_deck = Deck("deck.txt")
test_deck.is_valid_deck()
