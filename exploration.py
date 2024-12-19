"""
Things we want:
- type(s)
- price
- mana cost (probably as CMC?)
"""
from typing import List
import re
import json
from collections import Counter


def parse_card_type(type_line):
    modes = [i.strip() for i in type_line.split('//')]
    return [CardType(mode) for mode in modes]


class CardType:
    def __init__(self, type_line):
        self.legendary = 'Legendary' in type_line
        type_line = type_line.replace('Legendary', '').strip()

        if '—' in type_line:
            primary_types, secondary_types = [i.strip() for i in type_line.split('—')]
            self.secondary_types = secondary_types.split()
        else:
            primary_types = type_line
            self.secondary_types = []

        self.primary_types = primary_types.split()

    def __repr__(self):
        return f"""Legendary: {self.legendary}
        Primary Types: {self.primary_types}
        Secondary Types: {self.secondary_types}
        """

class Card:
    """Pass relevant details of the card into a class object."""
    def __init__(self,
                 card_dict,
                 tags,
                 quantity=1,
                 disambig=None):
        self._data = card_dict
        self.tags = tags
        self.quantity = quantity
        self.disambig = disambig

        self.parse_data()

    def parse_data(self):
        card_dict = self._data

        # Standard data
        self.label = self.create_label()
        self.name = card_dict['name']
        self.cmc = card_dict['cmc']
        self.price = self.parse_price()

        self.card_types = parse_card_type(card_dict['type_line'])

    def create_label(self):
        label = self._data['name'].lower()
        label = re.sub(r' +', '_', label)
        label = re.sub(r'\W+', '', label)
        label = re.sub(r'_+', '_', label)

        if self.disambig is not None:
            label = f'{label}_{self.disambig}'
        return label

    def parse_price(self):
        priority_list = ['usd', 'usd_etched', 'usd_foil']
        prices = self._data['prices']

        for key in priority_list:
            if key in prices:
                return prices[key]

        raise ValueError(f'No price found given priority list {priority_list}.')


    #     self.type_key = card_dict['type']
    #     self.type_line = card_dict['type_line']

    #     self.layout = card_dict['layout']



    #     # Parse key data
    #     self.mana_cost = card_dict['mana_cost']
    #     self.power = card_dict.get('power', None)
    #     self.toughness = card_dict.get('toughness', None)

    # def parse_mdfc(self):
    #     pass

def summarize_card_list(card_list):
    # Average values
    print(f'Deck Size: {len(card_list)}')
    print(f'Average CMC: {sum([c.cmc for c in card_list]) / len(card_list):.2f}')
    print(f'Average Price: {sum([c.price for c in card_list]) / len(card_list):.2f}')
    print()

    # Card types
    print('--- Card Types ---')
    primary_types = Counter([card_type
                             for card in card_list
                             for face in card.card_types
                             for card_type in face.primary_types])
    secondary_types = Counter([card_type
                               for card in card_list
                               for face in card.card_types
                               for card_type in face.secondary_types])

    print('Primary Types:')
    print(json.dumps(primary_types, sort_keys=True, indent=4))
    print('Secondary Types:')
    print(json.dumps(secondary_types, sort_keys=True, indent=4))
    print()

    # Tags
    print('--- Tags ---')
    tags = Counter([tag for card in card_list for tag in card.tags])
    print(json.dumps(tags, sort_keys=True, indent=4))
    print()


def print_deck(card_list, mode):
    if mode == 'mtgo':
        card_counts = Counter([card.name for card in card_list])
        for card_name, count in sorted(card_counts.items(), key=lambda x: x[0]):
            print(f'{count} {card_name}')

    elif mode == 'by_card_type':
        card_types = {card.card_types[0].primary_types[0] for card in card_list}

        for card_type in card_types:
            print(f'--- {card_type} ---')
            card_counts = Counter([card.name for card in card_list
                                   if card.card_types[0].primary_types[0] == card_type])

            for card_name in sorted(card_counts.keys()):
                print(f'{card_counts[card_name]} {card_name}')
            print()


def load_deck(json_path: str) -> List[Card]:
    with open(json_path, 'r') as fo:
        data = json.load(fo)

    commander = {'card': data['main'], 'quantity': 1}
    main_deck = data['boards']['mainboard']['cards']
    all_cards = [commander, *main_deck.values()]

    user_tags = data['authorTags']

    card_types = [parse_card_type(v['card']['name']) for v in main_deck.values()]

    parsed_cards = []
    fail = []

    for card in all_cards:
        try:
            if card['quantity'] > 1:
                card_objs = [
                    Card(
                        card['card'],
                        user_tags[card['card']['name']],
                        quantity=1,
                        disambig=i
                    )
                    for i in range(card['quantity'])
                ]
                parsed_cards.extend(card_objs)

            else:
                card_obj = Card(
                    card['card'],
                    user_tags[card['card']['name']],
                    quantity=1,
                )
                parsed_cards.append(card_obj)
        except Exception as e:
            fail.append(card)

    print(f'Successes: {len(parsed_cards)}, Failures: {len(fail)}')

    return parsed_cards


if __name__ == '__main__':
    parsed_cards = load_deck('moxfield_output_v2.json')
    summarize_card_list(parsed_cards)
