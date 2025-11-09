import unittest
from unittest.mock import MagicMock, patch
from blackjack_gui import BlackjackGame

class TestBlackjackGame(unittest.TestCase):

    def setUp(self):
        self.game = BlackjackGame()

    def test_natural_blackjack(self):
        self.game.start_round(10)
        self.game.player_hands = [['♥A', '♣J']]
        self.game.dealer_hand = ['♦K', '♠5']
        self.game.dealer_play()
        self.assertEqual(self.game.balance, 115)

    def test_surrender(self):
        self.game.start_round(20)
        self.game.player_hands = [['♥10', '♣6']]
        self.game.dealer_hand = ['♦A', '♠7']
        self.game.player_surrender()
        self.assertEqual(self.game.balance, 90)

    def test_insurance_lose_and_main_bet_win(self):
        self.game.start_round(10)
        self.game.player_hands = [['♥Q', '♣9']]
        self.game.dealer_hand = ['♠A', '♥7']
        self.game.resolve_insurance(wants_insurance=True)
        self.game.player_stay()
        self.assertEqual(self.game.balance, 105)

if __name__ == '__main__':
    unittest.main()