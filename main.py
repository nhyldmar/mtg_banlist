import re
import os


card_regex_pattern = re.compile(r"^(?P<amount>\d{1,2})x? (?P<name>[^\(\n]*?)(?: \(.*)?$", re.MULTILINE)


class Deck:
    """Deck container for assessing validity."""
    banlist_dict = {
        "In custom banlist":        "custom_banned.txt",
        "Banned in legacy":         "banned_in_legacy.txt",
        "Banned in modern":         "banned_in_modern.txt",
        "Forced draw":              "forced_draw.txt",
        "Commander keyword":        "commander_keyword.txt",
        "Zero mana counterspell":   "zero_mana_counterspell.txt",
        "Cheap generic tutor":      "cheap_generic_tutor.txt",
        "Mana turbo":               "mana_turbo.txt",
        "Empty library":            "empty_library.txt"
    }

    cards = {}

    def __init__(self, deck_filename):
        with open(deck_filename) as deck_file:
            deck_string = deck_file.read()
            matches = re.findall(card_regex_pattern, deck_string)
            for (amount, name) in matches:
                self.cards[name] = amount

    def is_valid_deck(self):
        for clause, filename in self.banlist_dict.items():
            with open(f"banlists/{filename}") as file:
                banned_cards = file.read().splitlines()
                for card in self.cards.keys():
                    if card in banned_cards:
                        print(f"'{card}'is banned by clause: {clause}")


test_deck = Deck("deck.txt")
test_deck.is_valid_deck()
