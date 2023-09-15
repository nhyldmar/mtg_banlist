import scryfall_wrapper

def search_string_to_file(search_string, filename):
    name_list = scryfall_wrapper.get_scryfall_names(search_string)
    file = open(filename, mode="w")
    file.write("\n".join(name_list))

search_string_to_file("banned:legacy", "banlists/legacy_banned.txt")
search_string_to_file("banned:modern", "banlists/modern_banned.txt")
