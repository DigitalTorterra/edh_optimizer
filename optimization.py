import pulp as pl
import exploration


# Load deck
cards = exploration.load_deck('moxfield_output.json')
card_labels = [card.label for card in cards]

# Weights
tag_weights = {
    'Beaters': 1,
    'Burn': 1,
    'Card Draw': 2,
    'Counter Doubler': 1,
    'Counter Increment': 1,
    'Counters': 1,
    'Interaction': 1,
    'Kicker': 1,
    'Land': 1,
    'Ramp': 2,
    'Recursion': 1,
}
cmc_weight = 0
price_weight = 0

tag_mins = {
    # 'Beaters': 1,
    # 'Burn': 1,
    'Card Draw': 10,
    # 'Counter Doubler': 1,
    # 'Counter Increment': 1,
    # 'Counters': 1,
    # 'Interaction': 1,
    # 'Kicker': 1,
    'Land': 38,
    'Ramp': 10,
    'Recursion': 3,
}

required_cards = [
    'hallar_the_firefletcher',
    'sol_ring',
    'arcane_signet',
    'twinflame_tyrant',
]

# Define problem
prob = pl.LpProblem("Deck Building", pl.LpMaximize)

# Variables
card_vars = pl.LpVariable.dicts(
    'Card',
    card_labels,
    lowBound=0,
    upBound=1,
    cat='Binary'
)

# Objective function
tag_sum = pl.lpSum([tag_weights[tag] * card_vars[card.label]
                    for card in cards
                    for tag in card.tags])
cmc_sum = pl.lpSum([card_vars[card.label] * card.cmc
                    for card in cards])
price_sum = pl.lpSum([card_vars[card.label] * card.price
                    for card in cards])

prob += (
    tag_sum + cmc_sum * cmc_weight + price_sum * price_weight,
    'Total weighted sum of cards'
)

# Constraints
prob += (pl.lpSum([card_vars[i] for i in card_labels]) == 100, 'Deck_Size')

for tag, min_val in tag_mins.items():
    prob += (
        pl.lpSum([card_vars[card.label] for card in cards if tag in card.tags]) >= min_val,
        f'Minimum {tag} cards'
    )

for label in required_cards:
    prob += (
        card_vars[label] == 1,
        f'Required card: {label}'
    )


# Solve problem and explore solution
prob.solve()

final_decklist = [card for card in cards if card_vars[card.label].value() == 1]

exploration.summarize_card_list(final_decklist)
exploration.print_deck(final_decklist, 'mtgo')
# prob += (
#     pl.lpSum([tag_weights[tag]])
# )

# prob += (
#     pl.lpSum([costs[i] * ingredient_vars[i] for i in Ingredients]),
#     "Total Cost of Ingredients per can",
# )
