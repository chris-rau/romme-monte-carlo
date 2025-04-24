import time
from concurrent.futures import ProcessPoolExecutor

def simulate_hands(n):
    from main import Hand, Deck, CandidateCache
    cache = CandidateCache()
    wins = 0
    hands_with_straights = 0
    hands_with_sets = 0
    hands_with_jokers = 0
    hands_qualifying = 0
    for _ in range(n):
        hand = Hand(cache=cache)
        hand.draw(Deck())
        if len(hand.straights) > 0:
            hands_with_straights += 1
        if len(hand.sets) > 0:
            hands_with_sets += 1
        if len(hand.jokers()) > 0:
            hands_with_jokers += 1
        if len(hand.qualifying_plays()) > 0:
            hands_qualifying += 1
        if hand.get_winning_plays() is not None:
            wins += 1
    return wins, hands_with_straights, hands_with_sets, hands_with_jokers, hands_qualifying

def main():
    total_hands = 10**6
    num_workers = 8
    hands_per_worker = total_hands // num_workers

    timestamp = time.time()

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = executor.map(simulate_hands, [hands_per_worker] * num_workers)


    winning_hands = 0
    with_straights = 0
    with_sets = 0
    with_jokers = 0
    qualifying_hands = 0
    for result in results:
        wins, hands_with_straights, hands_with_sets, hands_with_jokers, hands_qualifying = result
        winning_hands += wins
        with_straights += hands_with_straights
        with_sets += hands_with_sets
        with_jokers += hands_with_jokers
        qualifying_hands += hands_qualifying
    print()
    print(time.time() - timestamp)
    print()
    print("-" * 50)
    print(f"Total hands: {total_hands}")
    print(f"Winning hands: {winning_hands}")
    print(f"Winrate: {winning_hands / total_hands}")
    print(f"Hands with straights: {with_straights}")
    print(f"Straight rate: {with_straights / total_hands}")
    print(f"Hands with sets: {with_sets}")
    print(f"Set rate: {with_sets / total_hands}")
    print(f"Hands with jokers: {with_jokers}")
    print(f"Joker rate: {with_jokers / total_hands}")
    print(f"Hands qualifying: {qualifying_hands}")
    print(f"Qualification rate: {qualifying_hands / total_hands}")

if __name__ == "__main__":
    main()