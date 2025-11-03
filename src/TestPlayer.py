from src.IndianPokerCompetition import IPAgent

import random

class TestAgent(IPAgent):

    def reset(self) -> None:
        pass

    def play(self, game_state) -> int:
        return random.randint(0, 3)