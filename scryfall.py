import csv
import pickle
import sqlite3

import requests
import scrython

db = sqlite3.connect('mtg.sqlite')
c = db.cursor()


def get_scryfall_data():
    # todo: sometimes we don't get the right price, since it only ever looks for the latest set
    # and if that's an online-only set, there's no usd price
    # (but also we generally want the cheapest printing, which might not be the latest)
    # (it probably is, though)
    bulk_data = scrython.bulk_data.BulkData()
    metadata, = filter(lambda x: x['type'] == 'oracle_cards', bulk_data.data())
    uri = metadata['download_uri']
    return requests.get(uri).json()


def price(x):
    if x is None:
        return None
    return int(float(x) * 100)


def update_cards_table(data):
    c.executemany(
        """
        insert into cards (card_name, thumbnail_url, price, scryfall_id, is_token, commander_legal, mana_cost, type_line, art_crop) 
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict do update set (card_name, thumbnail_url, price, is_token, commander_legal, mana_cost, type_line, art_crop) = (?1, ?2, ?3, ?5, ?6, ?7, ?8, ?9)
        """,
        (
            (row['name'], row.get('image_uris', {}).get('normal'), price(row['prices'].get('usd')),
             row['id'], 'Token' in row['type_line'],  row['legalities']['commander'],
             row.get('mana_cost', ''), row['type_line'], row.get('image_uris', {}).get('art_crop', '')
             )
            for row in data
            if row.get('layout') != 'art_series'
        )
    )
    db.commit()


def load_decks_w_cards_to_dict():
    decks: list[dict] = []

    # should take approximately 1 minute
    with open("decks_w_cards.csv", "r", encoding="utf8") as f:
        reader = csv.reader(f, quoting=csv.QUOTE_ALL)
        names = next(reader)
        assert names == ['url', 'savedate', 'commander', 'deckage', 'tribe', 'coloridentity', 'tcreature', 'tinstant',
                         'tsorcery', 'tartifact', 'tenchantment', 'tplaneswalker', 'commander2', 'tland', 'theme',
                         'cardhash', 'dprecon', 'cards', 'urlhash']
        for row in reader:
            deck = {key: value for key, value in zip(names, row)}
            cards, = csv.reader(
                deck['cards'].strip("{}").splitlines(), quotechar='"', delimiter=',', skipinitialspace=True,
                escapechar='\\'
            )
            deck['cards'] = cards
            decks.append(deck)

    with open('decks.pickle', 'wb') as f:
        pickle.dump(decks, f, pickle.HIGHEST_PROTOCOL)

    return decks


def get_card_names_and_ids(decks):
    # part 2: obtain name<>id map
    card_names = set()
    for deck in decks:
        card_names.update(deck['cards'])
        card_names.add(deck['commander'])
        if deck['commander2']:
            card_names.add(deck['commander2'])

    card_ids = {}
    bad_names = []
    for name in card_names:
        try:
            card_ids[name] = c.execute("select id from cards where card_name like ?", (name,)).fetchone()[0]
        except TypeError:
            try:
                card_ids[name] = c.execute("select id from cards where card_name like ?", (name + '%',)).fetchone()[0]
            except TypeError:
                bad_names.append(name)

    return card_ids, bad_names


# kinda subjective, but these are the ones i was most confident about
typos = {
    # vaguely rephrased cards (???)
    'Tarrasque': 'The Tarrasque',
    'Spike Pit Trap': 'Spiked Pit Trap',
    'Deathpriest of Myrkul': 'Death-Priest of Myrkul',
    'Ganax, Hunter of Stars': 'Ganax, Astral Hunter',  # there were _12_ of these!
    'Frenetic Devils': 'Frenzied Devils',
    'Approach of the Dragon': "Dragon's Approach",
    'Great Axe': 'Greataxe',
    'Minthara, Ruthless Soul': 'Minthara, Merciless Soul',
    'Amber Maul': "Amber Gristle O'Maul",  # kinda weird how wrong this is but what else could it be
    'Kagha, Archdruid of Shadow': 'Kagha, Shadow Archdruid',
    'Talisman of Segador': "Reaper's Talisman",  # it's spanish for reaper
    'Prophetic Hulk': 'Prophetic Titan',
    'Demonic Lightning': 'Demon Bolt',  # german

    # alternate card names (secret lair mostly)
    'Mind Flayer, the Shadow': 'Arvinox, the Mind Flail',
    'Will the Wise': "Wernog, Rider's Chaplain",
    'Chief Jim Hopper': 'Sophina, Spearsage Deserter',
    'Eleven, the Mage': 'Cecily, Haunted Mage',
    'Hawkins National Laboratory': 'Havengul Laboratory',

    # actual typos
    "Bane's Contigency": "Bane's Contingency",  # haha 10 people can't spell Contingency
    'Esix, Fractal Boon': 'Esix, Fractal Bloom',
    'Arcboud Whelp': 'Arcbound Whelp',
    'Starnheim Unleased': 'Starnheim Unleashed',
    'Perrie, the Pulveriser': 'Perrie, the Pulverizer',
    'Goblin Trap-Runner': 'Goblin Traprunner',
    'Said" // "Done': 'Said // Done',  # quotes are weird and its my fault
    'Trelasarra Moon Dancer': 'Trelasarra, Moon Dancer',
    'Solgurk, the Overslime': 'Slogurk, the Overslime',
    'MÃ¡rton Stromgald': 'Márton Stromgald',

    # misc
    'Master of Trinkets': 'Academy Manufactor',  # what? this one makes no sense
    'Bushitoad': 'Jade Avenger',  # ok this one is fuckin hilarious
    'Targ Nar, Large Beast, Chaotic Evil': 'Targ Nar, Demon-Fang Gnoll',
    'Katilda, Dawnhart Headwitch': 'Katilda, Dawnhart Prime',  # you can tell this one by the colour identity
}


def filter_decks_to_valid_only(decks, card_ids, bad_names):
    # attempt to salvage some of the typos
    # this is very messy because each time it is literally just a pile of edge cases

    # some cards are surrounded by quotation marks, so that's probably wrong
    # there are notably two un-set cards that are, and several legal commander cards with quotation marks in
    # but none of these are double sided so if there's a typo we can't save it anyway
    def strip_quotes(name):
        if name.startswith('"') and name.endswith('"'):
            return name[1:-1]
        return name

    def process_name(name):
        stripped = strip_quotes(name)
        if stripped in typos:
            return typos[stripped]
        return stripped

    def name_is_valid(name):
        name = name[1]
        return (
                not (' // ' in name and len(set(name.split(' // '))) == 1)  # art card
                and not all(n.startswith('A-') for n in name.split(' // '))  # alchemy
                and not (
                name.endswith('Emblem') and name != 'Leering Emblem'  # emblems (oh god just kill me now)
            )
        )

    # double sided cards
    worse_names = []
    for name in bad_names:
        try:
            clean_name = process_name(name)
            results = list(filter(name_is_valid,
                                  c.execute(
                                      "select id, card_name from cards where card_name like '%' || ? || '%'",
                                      (clean_name,)).fetchall()
                                  ))

            if len(results) == 0:
                raise ValueError()
            if len(results) >= 2:
                # fix it.
                # Ok here's a problem: what if a card's name is embedded in another card? eg "emerald dragon"
                # options are "emerald dragon // dissonant wave" and "emerald dragonfly"
                # the pick is clearly the former, but it gets harder when there's more than two options.
                # if there's exactly one exact match, we can recover here
                results = filter(lambda x: any(name == clean_name for name in x[1].split(' // ')), results)

            (card_id, card_name), = results

            # sanity check: either it's an exact match, or it's a double sided card
            if '//' in card_name or card_name.lower() == clean_name.lower():
                card_ids[name] = card_id
            else:
                raise TypeError()
        except (TypeError, ValueError):
            worse_names.append(name)

    bad_decks = list(filter(
        lambda x: any(name in worse_names for name in x['cards']) or x['commander'] in worse_names or x[
            'commander2'] in worse_names,
        decks
    ))

    for deck in bad_decks:
        del decks[decks.index(deck)]

    return worse_names, bad_decks


def insert_data_to_database(decks, card_ids):
    c.executemany(
        """
        insert into decks (deck_url, commander, commander2, tribe, coloridentity, tinstant, tsorcery, tartifact,
        tenchantment, tplaneswalker, tland, theme, dprecon) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            (deck['url'], card_ids[deck['commander']], card_ids.get(deck['commander2']), deck['tribe'],
             deck['coloridentity'], int(deck['tinstant']), int(deck['tsorcery']), int(deck['tartifact']), int(deck['tenchantment']),
             int(deck['tplaneswalker']), int(deck['tland']), deck['theme'], int(deck['dprecon'])
             )
            for deck in decks
        )
    )
    # little bit of cleanup: turn the empty strings into nulls
    c.execute("update decks set tribe = null where tribe = ''")
    c.execute("update decks set theme = null where theme = ''")

    deck_ids = {url: d_id for d_id, url in c.execute("select id, deck_url from decks").fetchall()}

    # and now the big one: inserting every deck's cards
    c.executemany(
        """
        insert into decks_x_cards (deck, card) VALUES (?, ?)
        """,
        (
            (deck_ids[deck['url']], card)
            for deck in decks
            for card in set(
            card_ids[card] for card in (
                    deck['cards'] + [deck['commander']] + ([deck['commander2']] if deck['commander2'] else[])
            ))
        )
    )


def ingress_data_from_edhrec():
    try:
        with open('pickles/bad_decks.pickle', 'rb') as f:
            decks = pickle.load(f)
    except FileNotFoundError:
        decks = load_decks_w_cards_to_dict()

    print(f'loaded {len(decks)} decks, extracting names...')

    card_ids, bad_names = get_card_names_and_ids(decks)
    exact_match_count = len(card_ids)

    print(f'found {exact_match_count} exact matches, applying fuzzing rules...')

    bad_cards, bad_decks = filter_decks_to_valid_only(decks, card_ids, bad_names)

    print(f'found {len(card_ids) - exact_match_count} additional cards. '
          f'There are {len(bad_cards)} invalid cards.')
    print(f'rejected {len(bad_decks)} decks for containing invalid cards.')
    print(f'inserting {len(decks)} decks to the database...')

    insert_data_to_database(decks, card_ids)
    db.commit()

    with open('pickles/bad_decks.pickle', 'wb') as f:
        pickle.dump(bad_decks, f, pickle.HIGHEST_PROTOCOL)

    with open('pickles/bad_cards.pickle', 'wb') as f:
        pickle.dump(bad_cards, f, pickle.HIGHEST_PROTOCOL)

    print(f'successfully committed {len(decks)} decks.')


def ingress_owned_cards():
    pass

if __name__ == '__main__':
    data = get_scryfall_data()
    update_cards_table(data)

# ingress_data_from_edhrec()
