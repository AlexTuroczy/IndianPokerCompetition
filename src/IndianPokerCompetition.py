from typing import Protocol
import random
from enum import Enum

class RoundResult(Enum):
    """
        Specifies end state of a round
    """
    A_WIN = 1
    DRAW = 2
    B_WIN = 3

class VisibleState:
    """
        Encompasses the state of the game which is visible to the agent
    """

    def __init__(self, common_card_1: int, common_card_2: int, other_players_card: int, 
                 own_chips: int, others_chips: int, own_current_bet: int, 
                 others_current_bet: int, other_played: bool):
        
        self.common_card_1 = common_card_1
        self.common_card_2 = common_card_2
        self.other_players_card = other_players_card
        self.own_chips = own_chips
        self.others_chips = others_chips
        self.own_current_bet =  own_current_bet
        self.others_current_bet =  others_current_bet
        self.other_played = other_played


class IPAgent(Protocol):
    """
        Inteface for agents which the players implement
    """

    def reset(self) -> None: ...
    def play(self, visible_state: VisibleState) -> int: ...

class IPGame:
    """
        Implements the logic for a single game of Indian Poker
    """

    def __init__(self, seed: int, player_a: IPAgent, player_b: IPAgent, a_first: bool,
                  starting_chips: int = 20, blind: int = 1, max_length: int = 100000) -> None:
        self.seed = seed
        self.blind = blind
        self.player_a = player_a
        self.player_b = player_b
        self.a_chips = starting_chips
        self.b_chips = starting_chips
        self.max_length = max_length
        self.deck = [i for i in range(1, 11) for _ in range(4)]
        self.a_first = a_first
        self.rng = random.Random(seed)

    def calculateScore(self, card: int, common1: int, common2: int) -> int:
        """
            Associates each hand with a score, higher score means better hand.
        """
        # check straight
        straight = sorted([card, common1, common2])
        if tuple(straight) == (1, 9, 10):
            return 21
        if tuple(straight) == (1, 2, 10):
            return 22
        if straight[1] == (straight[0] % 10) + 1 and straight[2] == (straight[1] % 10) + 1:
            return 20 + straight[2]
        
        # check 3 of a kind
        if card == common1 and common1 == common2:
            return 20 + card

        # check 2 of a kind
        if card == common1 or card == common2:
            return 10 + card
        
        return card

    def playRound(self):

        a_card, b_card, common1, common2 = self.rng.sample(self.deck, 4)
        a_bet, b_bet = self.blind, self.blind
        current_bet = self.blind
        a_can_raise, b_can_raise = True, True

        a_turn = self.a_first

        while a_can_raise or b_can_raise:
            if a_turn:
                visible_state = VisibleState(common1, common2, b_card, 
                                             self.a_chips, self.b_chips, a_bet, b_bet, not b_can_raise)
                
                current_player = self.player_a
                    


            else:
                visible_state = VisibleState(common1, common2, a_card, 
                                        self.b_chips, self.a_chips,
                                        b_bet, a_bet, 
                                        not a_can_raise, )
                current_player = self.player_b


            proposed_bet = current_player.play(visible_state)

            if proposed_bet >= min(self.a_chips, self.b_chips):
                # all in
                proposed_bet = min(self.a_chips, self.b_chips)
            
            if proposed_bet < current_bet:
                # fold
                score_a = self.calculateScore(a_card, common1, common2)
                score_b = self.calculateScore(b_card, common1, common2)

                if a_turn:
                    # fold a straight or 3 of a kind or 2 of a kind and get penalty
                    if score_a > score_b:
                        if score_a > 20: # 10 extra chips on straight/triple
                            current_bet += 10
                        elif score_a > 10: # 5 extra chips on straight/triple
                            current_bet += 5
                    self.a_chips -= current_bet
                    self.b_chips += current_bet
                    self.a_first = False

                else:
                    if score_b > score_a:
                        if score_b > 20: # 10 extra chips on straight/triple
                            current_bet += 10
                        elif score_b > 10: # 5 extra chips on straight/triple
                            current_bet += 5
                    self.b_chips -= current_bet
                    self.a_chips += current_bet
                    self.a_first = True
                return 

            # raise or call
            if a_turn:
                a_bet = proposed_bet
                a_turn = False
                a_can_raise = False
                b_can_raise = proposed_bet > current_bet # raise

            else:
                b_bet = proposed_bet
                a_turn = True
                b_can_raise = False
                a_can_raise = proposed_bet > current_bet
            current_bet = max(current_bet, a_bet, b_bet) 

        # reveal
        winner = self.showdown(a_card, b_card, common1, common2)

        if winner == RoundResult.A_WIN:
            self.a_chips += a_bet
            self.b_chips -= a_bet
            self.a_first = True
        
        else:
            self.b_chips += a_bet
            self.a_chips -= a_bet
            self.a_first = False


    def showdown(self, a_card: int, b_card: int, common1: int, common2: int) -> RoundResult:
        """
            Determines who is winner once final bets are placed without folding, 
            or if there is a draw.
        """
            
        score_a = self.calculateScore(a_card, common1, common2)

        score_b = self.calculateScore(b_card, common1, common2)

        if score_a == score_b:
            return RoundResult.DRAW
        
        elif score_a > score_b:
            return RoundResult.A_WIN
        else:
            return RoundResult.B_WIN




    def playGame(self) -> tuple[float, float]:
        """
            Plays a game of Indian Poker

            Returns:
                (a_points, b_points): tuple[float, float] where
                    - a_points (float): number of points player a receives after game
                    - b_points (float): number of points player b receives after game
        """

        length = 0
        while self.a_chips > 0 and self.b_chips > 0 and length < self.max_length:
            self.playRound()
            length += 1
        
        if length >= self.max_length:
            return (0.5, 0.5)

        if self.a_chips > 0:
            return (1.0, 0.0)
        
        return (0.0, 1.0)


class IPTournament:
    """
        A tournament between two IPAgents, consisting of several games
    """

    def __init__(self, player_a: IPAgent, player_b: IPAgent, num_games: int = 100, seed: int = 1) -> None:
        self.player_a = player_a
        self.player_b = player_b
        self.num_games = num_games
        self.seed = seed
        self.a_points = 0.0
        self.b_points = 0.0

        

    def reset(self) -> None:
        self.player_a.reset()
        self.player_b.reset()
        self.a_points = 0.0
        self.b_points = 0.0

        
    def playTournament(self) -> None:

        for i in range(self.seed, self.seed+self.num_games):
            game = IPGame(i, self.player_a, self.player_b, a_first=i % 2 == 0)
            a_add_points, b_add_points = game.playGame()
            self.a_points += a_add_points
            self.b_points += b_add_points

    def __str__(self) -> str:
        return f"Player A: {self.a_points}, Player B: {self.b_points}"
        

