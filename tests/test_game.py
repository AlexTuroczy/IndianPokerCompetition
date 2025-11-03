import unittest

from src.IndianPokerCompetition import IPTournament, IPGame

from src.TestPlayer import TestAgent

class Test(unittest.TestCase):

    def test_game(self):
        player_a = TestAgent()
        player_b = TestAgent()
        tournament = IPTournament(player_a, player_b, num_games = 100)

        tournament.playTournament()
        print(tournament.__str__())