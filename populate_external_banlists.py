import scryfall_wrapper

def search_string_to_file(search_string, filename):
    name_list = scryfall_wrapper.get_scryfall_names(search_string)
    file = open(filename, mode="w")
    file.write("\n".join(name_list))

# Permitted duplicates (TODO: Restrict Nazgul and Seven Dwarves)
search_string_to_file("(t:basic t:land) or otag:relentless",
                      "whitelists/permitted_duplicates.txt")
# Banned in legacy
search_string_to_file("banned:legacy",
                      "banlists/banned_in_legacy.txt")
# Banned in modern
search_string_to_file("banned:modern",
                      "banlists/banned_in_modern.txt")
# Forced draw
search_string_to_file("o:'game is a draw'",
                      "banlists/forced_draw.txt")
# Commander keyword
search_string_to_file("o:commander -o:eminence -o:partner -t:background -t:planeswalker -commander",
                      "banlists/commander_keyword.txt")
