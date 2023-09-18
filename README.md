# Custom MtG Commander Banlist Parser

Friends and I have some rules we use to add to the commander banlist in order to keep the game more fun. This is a parser people can use to check if their deck is legal within our custom restrictions. Feel free to fork this for your own purposes.

## Categories

- Any cards that contain the word commander, except for cards with Eminence abilities, Partner, Backgrounds and Planeswalkers and cards given specific exemptions (none yet). (e.g. Command Tower)
- Any non-land permanents that create more mana than they cost on the turn they are played. (e.g. Mana Vault)
- Any two or fewer card combo wins (cards in the command zone do not count as a card). (e.g. Exquisite Blood + Sanguine Blood, two cards draw/tutor the rest of the combo)
- Any two-mana or cheaper generic tutors to hand or top of deck. (e.g. Demonic Tutor)
- Cards that read “empty your library” effectively. (e.g. Demonic Consultation)
- Zero-mana counterspells. (e.g. Force of Will)
- Cards that force draws. (e.g. Divine Intervention)
- Banned in legacy
- Banned in modern

## Specific

- Alpha Dual Lands
- Ancient Tomb
- Doubling Season
- Arctic Foxes :\)
- Esper Sentinel
- Intuition
- Reanimate
- Rotpriest
- The Tabernacle at Pendrell Vale
- Winter Orb
- Stasis
- Ad Nauseam
- Rhystic Study
- Smothering Tithe
- Mana Drain
- Dockside Extortionist

## TODO

- [x] Add a discord bot that can be used to interface with this
- [ ] Combo check
- [x] Mana turbo check
- [x] Empty library check
- [x] More robust regex for other text formats
