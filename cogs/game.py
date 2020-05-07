from enum import Enum
import random


class GameState(Enum):
    NOT_PLAYING = 0
    WAITING_FOR_LEADER = 1
    WAITING_FOR_ASSASSIN = 2
    WAITING_FOR_VOTE = 3
    WAITING_FOR_QUEST = 4


class Characters(Enum):
    MERLIN = 1
    ASSASSIN = 2
    GOOD_SERVANT = 3
    EVIL_SERVANT = 4


class Player:
    def __init__(self, member):
        self.member = member
        self.character = None

    def set_character(self, character):
        self.character = character

    def is_merlin(self):
        return self.character == Characters.MERLIN

    def is_good(self):
        return self.character == Characters.MERLIN or self.character == Characters.GOOD_SERVANT

    def is_assassin(self):
        return self.character == Characters.ASSASSIN

    def is_bad(self):
        return self.character == Characters.ASSASSIN or self.character == Characters.EVIL_SERVANT


class Board:
    def __init__(self, number_of_players):
        self.number_of_players = number_of_players
        self.leader = random.randint(0, number_of_players - 1)
        self.successes = 0
        self.fails = 0
        self.failed_votes = 0

        if number_of_players == 5:
            self.number_on_quest = [2, 3, 2, 3, 3]
            self.fails_needed = [1, 1, 1, 1, 1]
            self.number_of_good = 2
            self.number_of_evil = 1
        elif number_of_players == 6:
            self.number_on_quest = [2, 3, 4, 3, 4]
            self.fails_needed = [1, 1, 1, 1, 1]
            self.number_of_good = 3
            self.number_of_evil = 1
        elif number_of_players == 7:
            self.number_on_quest = [2, 3, 3, 4, 4]
            self.fails_needed = [1, 1, 1, 2, 1]
            self.number_of_good = 3
            self.number_of_evil = 2
        elif number_of_players == 8:
            self.number_on_quest = [3, 4, 4, 5, 5]
            self.fails_needed = [1, 1, 1, 2, 1]
            self.number_of_good = 4
            self.number_of_evil = 2
        elif number_of_players == 9:
            self.number_on_quest = [3, 4, 4, 5, 5]
            self.fails_needed = [1, 1, 1, 2, 1]
            self.number_of_good = 5
            self.number_of_evil = 2
        elif number_of_players == 10:
            self.number_on_quest = [3, 4, 4, 5, 5]
            self.fails_needed = [1, 1, 1, 2, 1]
            self.number_of_good = 5
            self.number_of_evil = 3

    def select_next_leader(self):
        if self.leader == self.number_of_players-1:
            self.leader = 0
        else:
            self.leader += 1

    def succeed_vote(self):
        self.failed_votes = 0

    def fail_vote(self):
        self.failed_votes += 1

    def succeed_quest(self):
        self.successes += 1

    def fail_quest(self):
        self.fails += 1

    def did_good_win(self):
        return self.successes >= 3

    def did_evil_win(self):
        return self.fails >= 3
