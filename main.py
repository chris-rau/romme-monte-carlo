import itertools
import math
import random
import time
from enum import Enum
from abc import abstractmethod
import matplotlib.pyplot as plt


VALUES = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]


class Suit(Enum):
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3
    CLUBS = 4
    JOKER = 5

    def __str__(self):
        match self:
            case Suit.CLUBS:
                return "♣"
            case Suit.DIAMONDS:
                return "♦"
            case Suit.HEARTS:
                return "♥"
            case Suit.SPADES:
                return "♠"
            case Suit.JOKER:
                return "X"
            case _:
                return "?"

    def __lt__(self, other):
        return self.value < other.value

    @classmethod
    def from_symbol(cls, symbol):
        match symbol:
            case "♥":
                return Suit.HEARTS
            case "♦":
                return Suit.DIAMONDS
            case "♠":
                return Suit.SPADES
            case "♣":
                return Suit.CLUBS
            case "X":
                return Suit.JOKER
        return None

    @staticmethod
    def non_joker_suits():
        return [suit for suit in Suit if suit != Suit.JOKER]


class Card:

    def __init__(self, suit, value):
        self.suit = suit
        self.value = value

    def is_joker(self):
        return self.value == "X" or self.suit == Suit.JOKER

    def __str__(self):
        return f"{self.value}{self.suit}"

    def __repr__(self):
        return self.__str__()

    def __value_ordinal(self):
        if self.is_joker():
            return 1000
        return VALUES.index(self.value)

    def __lt__(self, other):
        if self.value == other.value:
            return self.suit < other.suit
        return self.__value_ordinal() < other.__value_ordinal()

    def __eq__(self, other):
        return self.value == other.value and self.suit == other.suit

    def __hash__(self):
        return hash(self.__str__())

    def score(self):
        if self.is_joker():
            return math.nan
        if self.value == "A":
            return 11
        int_value = self.__value_ordinal() + 2
        if int_value > 10:
            int_value = 10
        return int_value

    def penalty_score(self):
        if self.is_joker():
            return 20
        return self.score()


    @classmethod
    def from_string(cls, string):
        if string[0:2] == "10":
            value = "10"
            suit = string[2]
        else:
            value = string[0]
            suit = string[1]
        return Card(Suit.from_symbol(suit), value)

class Deck:

    def __init__(self):
        self.cards = []
        for value in VALUES:
            for suit in Suit.non_joker_suits():
                self.cards.append(Card(suit, value))
                self.cards.append(Card(suit, value))
        for _ in range(6):
            self.cards.append(Card(Suit.JOKER, "X"))

    def __len__(self):
        return len(self.cards)

    def draw(self, n):
        draw = random.sample(self.cards, n)
        for card in draw:
            self.cards.remove(card)
        return draw


def extend_sets(previous_sets, card_candidates, extended_sets):
    for a_set in previous_sets:
        reduced_candidates = [card for card in card_candidates if card not in a_set]
        if len(reduced_candidates) >= 3:
            set_extensions = CardSet.find_single_sets(reduced_candidates)
            for set_extension in set_extensions:
                extended_set = CardSet(a_set.cards + set_extension.cards)
                if extended_set not in extended_sets:
                    extended_sets.add(extended_set)


class Hand:

    def __init__(self, size=13, cache=None):
        self.size = size
        self.cards = []
        self._straights = None
        self._sets = None
        self.cache = cache


    def draw(self, deck):
        self.cards = deck.draw(self.size)

    def __str__(self):
        return "|".join([str(c) for c in sorted(self.cards)])

    def __contains__(self, item):
        return item in self.cards

    def jokers(self):
        return [card for card in self.cards if card.is_joker()]

    def qualifying_plays(self):
        return [play for play in self.plays if play.is_qualifying()]

    def get_winning_plays(self):
        qualifying_plays = self.qualifying_plays()
        if len(qualifying_plays) == 0:
            return None
        constraints = {}
        for combination in itertools.combinations(self.plays, 2):
            play1 = combination[0]
            play2 = combination[1]

            contra = play1.contradicts(play2, self)
            constraints[(play1, play2)] = contra
            constraints[(play2, play1)] = contra

        candidates_len_2 = []
        for play1 in qualifying_plays:
            if len(play1) == 12:
                print(self)
                print("WINNER with 1", play1)
                return [play1]

            for play2 in self.plays:
                if play2 == play1 or constraints[(play1, play2)]:
                    continue

                candidate = [play1, play2]
                if total_coverage(candidate) == 12:
                    print(self)
                    print("WINNER with 2", candidate)
                    return candidate
                if total_coverage(candidate) < 12:
                    candidates_len_2.append(candidate)
                    # print("candidate (len 2):", candidate, total_coverage(candidate))

        candidates_len_3 = []
        for candidate2 in candidates_len_2:
            for play in self.plays:
                if play in candidate2 or contradicts_any(play, candidate2, constraints, len(self.jokers())):
                    continue
                candidate = candidate2 + [play]
                if total_coverage(candidate) == 12:
                    # print(self)
                    # print("WINNER with 3", candidate)
                    return candidate
                if total_coverage(candidate) < 12:
                    candidates_len_3.append(candidate)

        for candidate3 in candidates_len_3:
            for play in self.plays:
                if play in candidate3 or contradicts_any(play, candidate3, constraints, len(self.jokers())):
                    continue
                candidate = candidate3 + [play]
                if total_coverage(candidate) == 12:
                    # print(self)
                    # print("WINNER with 4", candidate)
                    return candidate

        return None


    @classmethod
    def from_string(cls, string):
        cards = []
        for card_str in string.split("|"):
            cards.append(Card.from_string(card_str))

        hand = Hand()
        hand.cards = cards
        return hand

    @property
    def plays(self):
        return self.straights + self.sets

    @property
    def sets(self):
        if self._sets is None:
            self._sets = get_all_sets(self, cache=self.cache)
        return self._sets

    @property
    def straights(self):
        if self._straights is None:
            self._straights = get_all_straights(self, cache=self.cache)
        return self._straights


def total_coverage(plays):
    return sum([len(play) for play in plays])

def contradicts_any(play, other_plays, constraints, total_jokers):
    for other_play in other_plays:
        if other_play == play:
            continue
        if constraints[(play, other_play)]:
            return True
    # check if total amount of jokers is ok
    used_jokers = len(play.jokers()) + sum([len(other.jokers()) for other in other_plays])
    if used_jokers > total_jokers:
        return True

    return False


def get_all_sets(hand, cache=None):
    sets = []

    for value in VALUES:
        candidates = [card for card in hand.cards if card.value == value or card.is_joker()]
        if len(candidates) < 3:
            continue
        if cache is not None:
            cached_sets = cache.load_card_set_result(candidates)
            if cached_sets is not None:
                sets.extend(cached_sets)
                continue

        found_sets = set()

        single_sets = CardSet.find_single_sets(candidates)
        found_sets = found_sets.union(single_sets)

        if len(candidates) >= 6:
            double_sets = set()
            extend_sets(single_sets, candidates, double_sets)
            found_sets = found_sets.union(double_sets)

            if len(candidates) >= 9:
                triple_sets = set()
                extend_sets(double_sets, candidates, triple_sets)
                found_sets = found_sets.union(triple_sets)

                if len(candidates) >= 12:
                    quad_sets = set()
                    extend_sets(triple_sets, candidates, quad_sets)
                    found_sets = found_sets.union(quad_sets)

        sets.extend(found_sets)

        if cache is not None:
            cache.save_card_set_result(candidates, found_sets)

    return sets


def previous_value(value):
    if value == "2":
        return "A"
    return VALUES[VALUES.index(value) - 1]

def next_value(value):
    if value == "A":
        return "2"
    return VALUES[VALUES.index(value) + 1]


def get_windows(extended_candidates, window_size):
    wrap_around = extended_candidates + extended_candidates
    windows = []
    for i in range(len(extended_candidates)):
        windows.append(wrap_around[i:i+window_size])
    return windows


def is_straight(cards, extensions, nr_of_jokers):
    for i,card in enumerate(cards[:-1]):
        next_card = cards[i+1]
        if next_card.value != next_value(card.value):
            return False

    # found straight in extended cards, check for joker amount
    non_joker_cards = [card for card in cards if not card in extensions]
    if len(non_joker_cards) + nr_of_jokers < len(cards):
        # Straight not valid, more jokers used than allowed
        return False

    # check for two jokers next to each other
    if nr_of_jokers > 0:
        for i,card in enumerate(cards[:-1]):
            next_card = cards[i+1]
            if card in extensions and next_card in extensions:
                return False
        if cards[0] in extensions and cards[-1] in extensions:
            return False
    return True


def get_all_straights(hand, cache=None):
    straights = []
    jokers = [card for card in hand.cards if card.is_joker()]
    for suit in Suit.non_joker_suits():
        candidates = [card for card in hand.cards if card.suit == suit]
        # remove duplicates
        candidates = list(set(candidates))
        candidates.sort()

        extended_candidates = candidates.copy()
        extensions = set()
        if len(jokers) > 0:
            for card in candidates:
                prev_card = Card(suit, previous_value(card.value))
                next_card = Card(suit, next_value(card.value))
                if prev_card not in extended_candidates:
                    extensions.add(prev_card)
                if next_card not in extended_candidates:
                    extensions.add(next_card)

        extended_candidates.extend(list(extensions))
        extended_candidates.sort()
        max_window_size = min(len(extended_candidates), len(candidates) + len(jokers))
        for window_size in range(3, max_window_size + 1):
            straight_candidates = get_windows(extended_candidates, window_size)
            for straight_candidate in straight_candidates:
                if is_straight(straight_candidate, extensions, len(jokers)):
                    straight = [(Card(Suit.JOKER, "X") if card in extensions else card) for card in straight_candidate]
                    straights.append(Straight(straight))

    return straights



class Play:

    def __init__(self, cards):
        self.cards = cards

    def __str__(self):
        return "|".join([str(c) for c in sorted(self.cards)])

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self.cards)

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return self.__str__() == other.__str__()

    def __contains__(self, item):
        return item in self.cards

    def __iter__(self):
        return iter(self.cards)

    def suits(self):
        return [card.suit for card in self.cards]

    def values(self):
        return [card.value for card in self.cards]

    def jokers(self):
        return [card for card in self.cards if card.is_joker()]

    def contradicts(self, other, hand):
        total_jokers = len(hand.jokers())
        if len(self.jokers()) + len(other.jokers()) > total_jokers:
            return True

        doubles = [card for card in hand.cards if (not card.is_joker()) and len([c for c in hand.cards if c == card]) > 1]
        for card in self.cards:
            if card in other.cards and not card in doubles and not card.is_joker():
                return True

        return False

    @abstractmethod
    def score(self):
        pass

    @abstractmethod
    def is_qualifying(self):
        pass



class Straight(Play):

    def __init__(self, cards):
        super().__init__(cards)

    def __str__(self):
        return "|".join([str(c) for c in self.cards])

    def score(self):
        score = 0
        for i,card in enumerate(self.cards[:-1]):
            next_card = self.cards[i+1]
            if card.is_joker():
                score += next_card.score() - 1
            else:
                score += card.score()
        if self.cards[-1].is_joker():
            score += self.cards[-2].score() + 1
        else:
            score += self.cards[-1].score()
        return score

    def is_qualifying(self):
        return self.score() >= 30


class CardSet(Play):

    def __init__(self, cards):
        super().__init__(cards)

    def score(self):
        not_a_joker = [card for card in self.cards if not card.is_joker()][0]
        return len(self.cards) * not_a_joker.score()

    def is_qualifying(self):
        if len(self.cards) <= 4:
            return self.score() >= 30
        elif len(self.cards) == 6:
            return self.score() / 2 >= 30
        elif len(self.cards) == 7:
            return self.score() / 7 * 4 >= 30
        elif len(self.cards) == 8:
            return self.score() / 2 >= 30
        elif len(self.cards) == 9:
            return self.score() / 3 >= 30
        elif len(self.cards) == 10:
            return self.score() / 10 * 4 >= 30
        elif len(self.cards) == 11:
            return self.score() / 11 * 4 >= 30
        return True

    @classmethod
    def find_single_sets(cls, candidates):
        if len(candidates) < 3:
            return set()

        combinations = []
        combinations.extend(itertools.combinations(candidates, 3))
        combinations.extend(itertools.combinations(candidates, 4))

        sets = []
        for combi in combinations:
            nr_of_jokers = len([card for card in combi if card.is_joker()])
            distinct_non_joker_suits = set([card.suit for card in combi if not card.is_joker()])
            if nr_of_jokers >= 3:
                # 3 jokers violate non-adjacency rule for jokers
                continue

            if len(distinct_non_joker_suits) == len(combi) - nr_of_jokers:
                if nr_of_jokers == 2 and Suit.CLUBS in distinct_non_joker_suits and Suit.DIAMONDS in distinct_non_joker_suits:
                    # 2 jokers violate adjacency rule for hearts and spades
                    continue
                sets.append(CardSet(combi))
        return set(sets)

    @classmethod
    def from_other_card_set(cls, other, new_card_value):
        cards = []
        for card in other.cards:
            if card.is_joker():
                cards.append(Card(Suit.JOKER, "X"))
            else:
                cards.append(Card(card.suit, new_card_value))
        return CardSet(cards)


def suit_string(card_collection):
    return "".join(sorted([str(card.suit) for card in card_collection]))


class CandidateCache:
    def __init__(self):
        self.set_cache = {}

    def save_card_set_result(self, candidates, card_sets):
        key = suit_string(candidates)
        self.set_cache[key] = card_sets

    def load_card_set_result(self, candidates):
        key = suit_string(candidates)
        non_jokers = [card for card in candidates if not card.is_joker()]
        if len(non_jokers) == 0:
            # all jokers is forbidden
            return []
        card_value = non_jokers[0].value
        if key in self.set_cache:
            cached_sets = set()
            for card_set in self.set_cache[key]:
                cached_sets.add(CardSet.from_other_card_set(card_set, card_value))
            return cached_sets
        return None


def nonzero(lst):
    return [val for val in lst if val != 0]


def plot_play_sizes(play_sizes, exclude_zero=True):
    straights = [play[0] for play in play_sizes if exclude_zero]
    sets = [play[1] for play in play_sizes]
    totals = [play[0] + play[1] for play in play_sizes]

    plt.hist(nonzero(straights) if exclude_zero else straights, bins=50)
    plt.title("Nr. of straights")
    plt.show()

    plt.hist(nonzero(sets) if exclude_zero else sets, bins=50)
    plt.title("Nr. of sets")
    plt.show()

    plt.hist(nonzero(totals) if exclude_zero else totals, bins=50)
    plt.title("Nr. of total plays")
    plt.show()

    plt.scatter(straights, sets)
    plt.title("Straights vs. sets")
    plt.show()

    new_straights = []
    new_sets = []
    for i in range(len(straights)):
        if straights[i] != 0 or sets[i] != 0:
            new_straights.append(straights[i])
            new_sets.append(sets[i])
    plt.hist2d(straights, sets)
    plt.title("Straights vs. sets")
    plt.show()

    plt.hist2d(new_straights, new_sets, bins=20)
    plt.title("Straights vs. sets (no (0,0))")
    plt.show()


def main():

    cache = CandidateCache()

    # hand = Hand.from_string("2♣|3♦|5♥|7♣|8♥|9♦|9♥|10♥|Q♠|K♥|K♠|A♠|A♣")
    # print(hand)
    # print(hand.plays)
    # print(hand.qualifying_plays())
    # print(hand.get_winning_plays())
    # return

    # hand = Hand()
    # hand.draw(Deck())
    # print(hand)
    # print(hand.plays)
    # print(hand.qualifying_plays())
    # print(hand.get_winning_plays())
    # return

    play_sizes = []

    total_hands = 0
    winning_hands = 0

    record = (None, 0)
    timestamp = time.time()
    for i in range(10**6):
        # if i % 10000 == 0:
        #     print(i)
        hand = Hand(cache=cache)
        hand.draw(Deck())
        winning = hand.get_winning_plays()
        total_hands += 1
        if winning is not None:
            winning_hands += 1
            print(f"{winning_hands} wins / {total_hands} total ({winning_hands/total_hands} winrate)")
        # print(hand.plays)
        # play_sizes.append((len(hand.straights), len(hand.sets)))

        if len(hand.plays) > record[1]:
            # print(len(hand.plays), hand)
            # print(hand.plays)
            record = (hand, len(hand.plays))
    print(time.time() - timestamp)

    print("-"*50)
    print(f"Total hands: {total_hands}")
    print(f"Winning hands: {winning_hands}")
    print(f"Winrate", winning_hands / total_hands)

    # plot_play_sizes(play_sizes)

if __name__ == "__main__":
    main()