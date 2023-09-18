import csv
import itertools
import sqlite3
from typing import List

from scryfall import get_card_names_and_ids
from collections import namedtuple, defaultdict


Combo = namedtuple('Combo', ['ID', 'CI', 'Prerequisites', 'Steps', 'Results', 'Cards'])
# commanders spellbook appears to be hand-typed, because there's a lot of typos (usually relating to apostrophes)
typos = {
    "Cathar's Crusade": "Cathars' Crusade",
    "Otharri, Sun's Glory": "Otharri, Suns' Glory",
    "Druid's Repository": "Druids' Repository",
    "Nicol-Bolas, Dragon God": "Nicol Bolas, Dragon-God",
    'Sharuum, the Hegemon': 'Sharuum the Hegemon',
    'Urabrask, the Hidden': 'Urabrask the Hidden',
    "Ashnod, the Uncaring": "Ashnod the Uncaring",
    'Bruvac, the Grandiloquent': 'Bruvac the Grandiloquent',
    'Slimefoot the Stowaway': 'Slimefoot, the Stowaway',
    'Emiel, the Blessed': 'Emiel the Blessed',
    'Yoshimaru, Ever-Faithful': 'Yoshimaru, Ever Faithful',
    'Grima Wormtongue': 'Gríma Wormtongue',
    'Mikaeus the Unhallowed': 'Mikaeus, the Unhallowed',
    'Gandalf, the White': 'Gandalf the White',
    "Sea King's Blessing": "Sea Kings' Blessing",
    "Druid’s Call": "Druid's Call",
    "Imp's Taunt": "Imps' Taunt"
}
COLOURS = 'WUBRG'


def ingress():
    cards = set()
    combos: List[Combo] = []
    deck = {'commander': 'Sol Ring', 'cards': cards, 'commander2': None}
    with open('combos.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        assert next(reader) == ['ID', 'Card 1', 'Card 2', 'Card 3', 'Card 4', 'Card 5', 'Card 6', 'Card 7', 'Card 8',
                                'Card 9', 'Card 10', 'Color Identity', 'Prerequisites', 'Steps', 'Results',
                                'Variant IDs', '', 'Duplicate Protection']
        for row in reader:
            names = [typos.get(x.strip(), x.strip()) for x in row[1:11] if x != '']
            if not names:
                continue
            cards.update(names)
            combos.append(Combo(row[0], *row[11:15], names))

    card_ids, bad_names = get_card_names_and_ids(decks=[deck])
    assert not bad_names

    for combo in combos:
        cards = [card_ids[name] for name in combo.Cards]
        combo.Cards.clear()
        combo.Cards.extend(cards)

    c.executemany(
        """
        insert into combos (id, colour_identity, prerequisites, steps, results)
        values (?, ?, ?, ?, ?)
        """,
        ((combo.ID, combo.CI, combo.Prerequisites, combo.Steps, combo.Results)
         for combo in combos)
    )

    c.executemany(
        """
        insert into combos_x_cards (combo, card) values (?, ?)
        """,
        ((combo.ID, card) for combo in combos for card in combo.Cards)
    )

    db.commit()

    print(1)


db = sqlite3.connect('mtg.sqlite')
c = db.cursor()


def dumb_insert():
    import Result_34
    c.executemany(
        """
       insert into combos_with (c_a, c_b) values (?, ?)
       """,
        Result_34.rows
    )
    db.commit()


def add_card_greedy_num_combos(combos, deck, _cards):
    by_missing = by_cards_missing(combos, deck)
    for i in range(1, 11):
        if not by_missing[i]:
            continue
        count = defaultdict(lambda: [0 for _ in range(10)])
        for j in range(i, 11):
            for combo in by_missing[j]:
                for card in combo:
                    if combo in illegal_combos:
                        count[card][0] = -99999
                    if card not in deck:
                        count[card][j] += 1
        if not count:
            continue
        # sort count
        count = sorted(count.items(), reverse=True, key=lambda item: item[1])
        print("adding", count[0])
        return count


def add_card_greedy_cardwise(combos, deck, _cards):
    by_missing = by_cards_missing(combos, deck)
    card_goodness = dict(add_card_greedy_num_combos(combos, deck, _cards))
    if not by_missing[1]:
        return list(card_goodness.items())

    cards_to_consider = {card for combo in by_missing[1] for card in combo} - deck
    for card in cards_to_consider:
        deck_ = deck.union({card})
        combos_with = defaultdict(set)
        combo_list = by_missing[0].union(
            {combo for combo in by_missing[1] if card in combo}
        )
        for card_ in deck_:
            for combo in combo_list:
                if card_ in combo:
                    for card__ in combo:
                        if card_ != card__:
                            combos_with[card_].add(card__)
        card_goodness[card][0] = sum(len(cw)**0.8 for cw in combos_with.values())
    card_goodness = sorted(card_goodness.items(), reverse=True, key=lambda item: item[1])
    return card_goodness


def add_card_greedy_pairs(combos, deck, cards):
    by_missing = by_cards_missing(combos, deck)
    for i in range(1, 11):
        if not by_missing[i]:
            continue
        count = {}
        for c1, c2 in itertools.combinations(cards, 2):
            now_missing = by_cards_missing(combos, deck.union({c1, c2}))
            count[c1, c2] = len(now_missing[0]) - len(by_missing[0])
        # sort count
        count = sorted(count.items(), key=lambda item: -item[1])
        for card, x in count:
            #  todo tie-breaking logic
            break
        else:
            continue

        if i == 1:
            print("added", x, "combos with card", card)

        return card


def by_cards_missing(combos: set[set], cards: set):
    return {
        i: {combo for combo in combos if len(combo - cards) == i}
        for i in range(0, 11)
    }


def cleanup_combo_list(combos):
    # never add a card to the deck if it's only in a single combo
    in_combos = defaultdict(int)
    for combo in combos:
        for card in combo:
            in_combos[card] += 1
    good_combos = {
        combo for combo in combos if all(in_combos[card] > 1 for card in combo)
    }
    return good_combos


def get_illegal_combos():
    things = c.execute("""
        select c.id, cxc.card
        from (select combos.id, count(card) count
              from combos
                       join combos_x_cards cxc on combos.id = cxc.combo
              group by combos.id
              having count = 2) two
                 join combos c on two.id = c.id
                 join combos_x_cards cxc on c.id = cxc.combo
        where (results like "%mana%" and results like "%draw%")
           or results like "%win%"
           or results like "%infinite damage%"
           or results like "%draw the game%"
           or results like "%infinite lifeloss%"
           or results like "%infinite creature tokens with haste%"
           or results like "%Each opponent loses the game%"
           or results like "%Infinite turns%"
        """).fetchall()
    combos = defaultdict(set)
    for combo, card in things:
        combos[combo].add(card)

    global illegal_combos
    illegal_combos = {frozenset(combo) for combo in combos.values()}


def get_combo_lands(colour_identity=COLOURS):
    things = c.execute(f"""
select c.id, cxc.card from combos c
join combos_x_cards cxc on c.id = cxc.combo
join cards c2 on c2.id = cxc.card
where c2.type_line like '%land%' and c.id in (select c.id
from combos c
         join combos_x_cards cxc on c.id = cxc.combo
         join cards c2 on cxc.card = c2.id
where
    c2.type_line like '%land%'
and c.id in (select c.id
               from combos c
                        join combos_x_cards cxc on c.id = cxc.combo
                        join cards c2 on cxc.card = c2.id
               group by c.id
               having c.id not in (select c.id
                                   from combos c
                                            join combos_x_cards cxc on c.id = cxc.combo
                                            join cards c2 on cxc.card = c2.id
                                   where not c2.commander_legal = 'legal'

                                     or (
                                        {' or '.join(f"c2.mana_cost like '%{col}%'" for col in COLOURS if col not in colour_identity) or 'FALSE'}
                                       ))))
        """).fetchall()

    global combo_lands
    combo_lands = {land for lands in things for land in lands}


def make_greedy(colour_identity):
    # 1. compute partial combos (combos which we don't have all the cards for right now)
    # 2. filter to partial combos missing one card
    # 3. find the card common to the plurality of those and add it
    # 4. repeat

    combos = defaultdict(set)

    result = c.execute(f"""
select c.id, cxc.card
from combos c
         join combos_x_cards cxc on c.id = cxc.combo
         join cards c2 on cxc.card = c2.id
where c.id in (select c.id
               from combos c
                        join combos_x_cards cxc on c.id = cxc.combo
                        join cards c2 on cxc.card = c2.id
               group by c.id
               having c.id not in (select c.id
                                   from combos c
                                            join combos_x_cards cxc on c.id = cxc.combo
                                            join cards c2 on cxc.card = c2.id
                                     where (
                                          {' or '.join(f"c2.mana_cost like '%{col}%'" for col in COLOURS if col not in colour_identity) or 'FALSE'}
                                       )))
    """).fetchall()
    for row in result:
        combos[row[0]].add(row[1])

    combos = cleanup_combo_list({frozenset(s) for s in combos.values()})

    deck = set()
    last_card = 60133
    new_card = None
    cards = {card for combo in combos for card in combo}
    while last_card != new_card:
        last_card = new_card
        new_card = add_card_greedy_cardwise(combos, deck, cards)[0][0]
        deck.add(new_card)
        cards.remove(new_card)
        if len(deck) >= 60:
            by_missing = by_cards_missing(combos, deck)
            combos_with = defaultdict(set)
            for card in deck:
                for combo in by_missing[0]:
                    if card in combo:
                        for card_ in combo:
                            if card != card_:
                                combos_with[card].add(card_)
            i, x = min(combos_with.items(), key=lambda x: len(x[1]))
            if i == last_card:
                break
            print("removed", len(x), x)
            deck.remove(i)
            cards.add(i)

    # calculate land-base
    symbols = defaultdict(int)
    for card in deck:
        mana_raw = c.execute('select mana_cost from cards where id = ?', (card,)).fetchone()[0]
        for m in mana_raw:
            if m in 'WBGUR':
                symbols[m] += 1
    total = sum(symbols.values())
    for colour, num in symbols.items():
        print(colour, (num / total) * 100)

    for i in range(1, 5):
        for combo in by_missing[i]:
            if len(deck) >= 90:
                break
            if all(card in combo_lands or card in deck for card in combo) and combo not in illegal_combos:
                for card in combo:
                    if card not in deck:
                        deck.add(card)
                by_missing[0].add(combo)

    print(f"this deck has {len(by_missing[0])} combos in ({len(deck)} cards)")
    # return len(by_missing[0])

    card_names = {card: c.execute("select card_name from cards where id=?", (card,)).fetchone()[0] for card in deck}
    open('deck_raw.txt', 'w').write('\n'.join(str(d) for d in deck))
    open('deck.txt', 'w').write('\n'.join(card_names[d] for d in deck))
    with open('deck_combos.txt', 'w') as f:
        for combo in by_missing[0]:
            f.write(' + '.join(sorted(card_names[comb] for comb in combo)) + '\n')

    print(i, x)


def try_all_colour_identities():
    best_combo_count = 0
    best_colour_identity = ''
    for i in range(6):
        for colour_identity in itertools.combinations(COLOURS, i):
            get_combo_lands(colour_identity)
            combo_count = make_greedy(colour_identity)
            if combo_count > best_combo_count:
                best_colour_identity = colour_identity
                best_combo_count = combo_count

    print('best colour identity is', best_colour_identity, 'with', best_combo_count, 'combos')


if __name__ == '__main__':
    # ingress()
    get_illegal_combos()
    get_combo_lands('RW')
    # try_all_colour_identities()
    make_greedy('RW')
