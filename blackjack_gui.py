import random
import tkinter as tk
from tkinter import simpledialog, messagebox

class BlackjackGame:
    def __init__(self, num_decks=6):
        self.num_decks = num_decks
        self.deck = []
        self.suits = ['♥', '♦', '♣', '♠']
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}

        self.player_hands = []
        self.current_hand_index = 0
        self.dealer_hand = []
        self.balance = 100
        self.bets = []
        self.insurance_bet = 0

        self.game_state = 'betting'
        self.message = "Welcome to Blackjack! Place your bet."

        self.shuffle_deck()

    def shuffle_deck(self):
        self.deck = [f"{suit}{rank}" for _ in range(self.num_decks) for suit in self.suits for rank in self.ranks]
        random.shuffle(self.deck)
        self.cut_card_position = len(self.deck) // 2 + random.randint(-len(self.deck) // 10, len(self.deck) // 10)

    def _get_hand_value(self, hand):
        value = sum(self.values.get(card[1:], 0) for card in hand)
        num_aces = sum(1 for card in hand if card.endswith('A'))
        while value > 21 and num_aces:
            value -= 10
            num_aces -= 1
        return value

    def deal_card(self, hand):
        if len(self.deck) < 20: self.shuffle_deck()
        if self.deck:
            card = self.deck.pop()
            hand.append(card)

    def start_round(self, bet):
        if not (0 < bet <= self.balance):
            self.message = "Invalid bet amount. Try again."
            return False

        self.balance -= bet
        self.bets = [bet]
        self.insurance_bet = 0
        self.player_hands = [[]]
        self.current_hand_index = 0
        self.dealer_hand = []

        self.deal_card(self.player_hands[0])
        self.deal_card(self.player_hands[0])
        self.deal_card(self.dealer_hand)
        self.deal_card(self.dealer_hand)

        self.game_state = 'player_turn'
        self.message = "Your turn. Hit or Stay?"

        if self.dealer_hand and self.dealer_hand[0].endswith('A'):
            self.game_state = 'insurance'
            self.message = "Dealer has an Ace. Do you want insurance?"
            return True

        player_score = self._get_hand_value(self.player_hands[0])
        if player_score == 21:
            self.message = "Blackjack! Let's see what the dealer has."
            self.game_state = 'dealer_turn'
            self.dealer_play()
        return True

    def resolve_insurance(self, wants_insurance):
        if wants_insurance:
            insurance_cost = self.bets[0] / 2
            if self.balance >= insurance_cost:
                self.balance -= insurance_cost
                self.insurance_bet = insurance_cost
                self.message = f"Insurance bet of ${insurance_cost} placed."
            else:
                self.message = "Not enough balance for insurance."

        is_dealer_blackjack = self._get_hand_value(self.dealer_hand) == 21

        if is_dealer_blackjack:
            if self.insurance_bet > 0:
                self.balance += self.insurance_bet * 3
                self.message += "\nDealer has Blackjack. Insurance pays out."
            else:
                self.message += "\nDealer has Blackjack."
            self.finalize_round()
        else:
            if self.insurance_bet > 0:
                self.message += "\nDealer does not have Blackjack. Insurance bet lost."

            if self._get_hand_value(self.player_hands[0]) == 21: # Player had a natural
                self.payout(2.5, 0)
                self.message += "\nBlackjack! You win!"
                self.game_state = 'betting'
            else:
                self.game_state = 'player_turn'
                self.message += "\nYour turn. Hit or Stay?"

    def get_current_player_hand(self):
        if self.current_hand_index < len(self.player_hands):
            return self.player_hands[self.current_hand_index]
        return None

    def player_hit(self):
        if self.game_state != 'player_turn': return
        hand = self.get_current_player_hand()
        if not hand: return

        self.deal_card(hand)
        if self._get_hand_value(hand) >= 21:
            self.next_hand_or_dealer_turn()

    def player_stay(self):
        if self.game_state != 'player_turn': return
        self.next_hand_or_dealer_turn()

    def player_double_down(self):
        if not self.can_double_down(): return

        hand = self.get_current_player_hand()
        bet = self.bets[self.current_hand_index]
        self.balance -= bet
        self.bets[self.current_hand_index] *= 2

        self.deal_card(hand)
        self.next_hand_or_dealer_turn()

    def player_split(self):
        if not self.can_split(): return

        hand_to_split = self.get_current_player_hand()
        bet = self.bets[self.current_hand_index]

        self.balance -= bet

        new_hand = [hand_to_split.pop()]
        self.player_hands.insert(self.current_hand_index + 1, new_hand)
        self.bets.insert(self.current_hand_index + 1, bet)

        self.deal_card(hand_to_split)
        self.deal_card(new_hand)

        is_ace_split = self.values.get(new_hand[0][1:], 0) == 11
        if is_ace_split:
            self.next_hand_or_dealer_turn()

    def player_surrender(self):
        if not self.can_surrender(): return

        bet = self.bets[0]
        self.balance += bet / 2
        self.player_hands[0] = [] # Mark as surrendered

        self.game_state = 'dealer_turn'
        self.dealer_play()


    def can_double_down(self):
        if self.game_state != 'player_turn': return False
        hand = self.get_current_player_hand()
        if not hand: return False
        bet = self.bets[self.current_hand_index]
        return len(hand) == 2 and self.balance >= bet

    def can_surrender(self):
        if self.game_state != 'player_turn': return False
        return len(self.player_hands) == 1 and len(self.player_hands[0]) == 2

    def can_split(self):
        if self.game_state != 'player_turn': return False

        hand = self.get_current_player_hand()
        if not hand or len(hand) != 2: return False

        bet = self.bets[self.current_hand_index]
        card1_val = self.values.get(hand[0][1:], 0)
        card2_val = self.values.get(hand[1][1:], 0)

        return card1_val == card2_val and self.balance >= bet

    def next_hand_or_dealer_turn(self):
        is_ace_split_on_first_hand = (len(self.player_hands) > 1 and
                                     self.values.get(self.player_hands[0][0][1:], 0) == 11)

        if is_ace_split_on_first_hand and self.current_hand_index == 0:
             self.current_hand_index += 1
             return

        if self.current_hand_index < len(self.player_hands) - 1:
            self.current_hand_index += 1
        else:
            self.game_state = 'dealer_turn'
            self.dealer_play()

    def dealer_play(self):
        all_busted = all(self._get_hand_value(h) > 21 for h in self.player_hands if h)
        if all_busted:
            self.finalize_round()
            return

        while self._get_hand_value(self.dealer_hand) < 17:
            self.deal_card(self.dealer_hand)

        self.finalize_round()

    def finalize_round(self):
        dealer_score = self._get_hand_value(self.dealer_hand)
        is_dealer_busted = dealer_score > 21
        is_dealer_blackjack = dealer_score == 21 and len(self.dealer_hand) == 2
        final_message = ""

        for i, hand in enumerate(self.player_hands):
            if not hand:
                final_message += f"Hand {i+1}: Surrendered.\n"
                self.payout(0, i)
                continue

            player_score = self._get_hand_value(hand)
            is_player_blackjack = player_score == 21 and len(hand) == 2
            hand_message = f"Hand {i+1} ({player_score}): "

            if player_score > 21:
                hand_message += "Busted."
                self.payout(0, i)
            elif is_player_blackjack and not is_dealer_blackjack:
                hand_message += "Blackjack! You win!"
                self.payout(2.5, i)
            elif is_dealer_busted:
                hand_message += f"Dealer busts! You win!"
                self.payout(2, i)
            elif player_score > dealer_score:
                hand_message += f"You win!"
                self.payout(2, i)
            elif dealer_score > player_score:
                hand_message += f"You lose."
                self.payout(0, i)
            else: # Push
                hand_message += "Push."
                self.payout(1, i)
            final_message += hand_message + "\n"

        self.message = final_message.strip()
        self.game_state = 'betting'
        if self.balance <= 0:
            self.message += "\nYou are out of money! Game over."
            self.game_state = 'game_over'

    def payout(self, multiplier, hand_index):
        if hand_index < len(self.bets):
             self.balance += self.bets[hand_index] * multiplier
             self.bets[hand_index] = 0

    def get_state(self):
        player_hand_str = " | ".join([f"Hand {i+1}: {' '.join(h)} ({self._get_hand_value(h)})" for i, h in enumerate(self.player_hands) if h])

        is_dealer_playing = self.game_state in ['dealer_turn', 'betting', 'game_over']

        dealer_score = 0
        if self.dealer_hand:
            dealer_score = self._get_hand_value(self.dealer_hand) if is_dealer_playing else self.values.get(self.dealer_hand[0][1:], 0)

        dealer_hand_str = ' '.join(self.dealer_hand) if is_dealer_playing else (f"{self.dealer_hand[0]} ?" if self.dealer_hand else "")

        return {
            "player_hands_str": player_hand_str,
            "dealer_hand": dealer_hand_str,
            "dealer_score": dealer_score,
            "balance": self.balance,
            "game_state": self.game_state,
            "can_double_down": self.can_double_down(),
            "can_surrender": self.can_surrender(),
            "can_split": self.can_split(),
        }

class BlackjackGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Blackjack")
        self.root.geometry("800x600")
        self.root.configure(bg='darkgreen')

        self.game = BlackjackGame()

        # ... (GUI setup is unchanged)
        self.top_frame = tk.Frame(root, bg='darkgreen')
        self.top_frame.pack(pady=10)
        self.dealer_frame = tk.Frame(root, bg='darkgreen')
        self.dealer_frame.pack(pady=10)
        self.player_frame = tk.Frame(root, bg='darkgreen')
        self.player_frame.pack(pady=10)
        self.controls_frame = tk.Frame(root, bg='darkgreen')
        self.controls_frame.pack(pady=20)
        self.adv_controls_frame = tk.Frame(root, bg='darkgreen')
        self.adv_controls_frame.pack(pady=10)

        self.balance_label = tk.Label(self.top_frame, text="", font=('Arial', 14), fg='white', bg='darkgreen')
        self.balance_label.pack(side=tk.LEFT, padx=20)
        self.message_label = tk.Label(self.top_frame, text="", font=('Arial', 12, 'bold'), fg='yellow', bg='darkgreen', wraplength=750)
        self.message_label.pack(side=tk.LEFT, padx=20)
        self.dealer_label = tk.Label(self.dealer_frame, text="Dealer's Hand:", font=('Arial', 16), fg='white', bg='darkgreen')
        self.dealer_label.pack()
        self.dealer_hand_label = tk.Label(self.dealer_frame, text="", font=('Courier', 24, 'bold'), fg='white', bg='darkgreen', height=2)
        self.dealer_hand_label.pack()
        self.player_label = tk.Label(self.player_frame, text="Your Hand:", font=('Arial', 16), fg='white', bg='darkgreen')
        self.player_label.pack()
        self.player_hand_label = tk.Label(self.player_frame, text="", font=('Courier', 20, 'bold'), fg='white', bg='darkgreen', height=2)
        self.player_hand_label.pack()

        self.bet_button = tk.Button(self.controls_frame, text="Bet", font=('Arial', 14), command=self.place_bet)
        self.bet_button.pack(side=tk.LEFT, padx=10)
        self.hit_button = tk.Button(self.controls_frame, text="Hit", font=('Arial', 14), command=self.hit)
        self.hit_button.pack(side=tk.LEFT, padx=10)
        self.stay_button = tk.Button(self.controls_frame, text="Stay", font=('Arial', 14), command=self.stay)
        self.stay_button.pack(side=tk.LEFT, padx=10)

        self.double_button = tk.Button(self.adv_controls_frame, text="Double Down", font=('Arial', 14), command=self.double_down)
        self.double_button.pack(side=tk.LEFT, padx=10)
        self.split_button = tk.Button(self.adv_controls_frame, text="Split", font=('Arial', 14), command=self.split)
        self.split_button.pack(side=tk.LEFT, padx=10)
        self.surrender_button = tk.Button(self.adv_controls_frame, text="Surrender", font=('Arial', 14), command=self.surrender)
        self.surrender_button.pack(side=tk.LEFT, padx=10)

        self.new_game_button = tk.Button(self.controls_frame, text="New Game", font=('Arial', 14), command=self.new_game, state=tk.DISABLED)
        self.new_game_button.pack(side=tk.RIGHT, padx=10)

        self.update_ui()

    def update_ui(self):
        state = self.game.get_state()

        self.balance_label.config(text=f"Balance: ${state['balance']:.2f}")
        self.message_label.config(text=state['message'])
        self.player_hand_label.config(text=state['player_hands_str'])
        self.dealer_hand_label.config(text=f"{state['dealer_hand']} ({state['dealer_score']})")

        if state['game_state'] == 'player_turn':
             self.player_label.config(text=f"Your Turn - Hand {self.game.current_hand_index + 1}:")
        else:
             self.player_label.config(text="Your Hand(s):")

        is_betting = state['game_state'] == 'betting'
        is_player_turn = state['game_state'] == 'player_turn'
        is_game_over = state['game_state'] == 'game_over'

        self.bet_button.config(state=tk.NORMAL if is_betting else tk.DISABLED)
        self.hit_button.config(state=tk.NORMAL if is_player_turn else tk.DISABLED)
        self.stay_button.config(state=tk.NORMAL if is_player_turn else tk.DISABLED)
        self.double_button.config(state=tk.NORMAL if state.get('can_double_down') else tk.DISABLED)
        self.split_button.config(state=tk.NORMAL if state.get('can_split') else tk.DISABLED)
        self.surrender_button.config(state=tk.NORMAL if state.get('can_surrender') else tk.DISABLED)
        self.new_game_button.config(state=tk.NORMAL if is_game_over else tk.DISABLED)

        if state['game_state'] == 'insurance':
            self.handle_insurance()
        if is_game_over:
            messagebox.showinfo("Game Over", self.game.message)

    def place_bet(self):
        bet_amount = simpledialog.askinteger("Bet", "How much?", parent=self.root, minvalue=1, maxvalue=int(self.game.balance))
        if bet_amount:
            self.game.start_round(bet_amount)
            self.update_ui()

    def hit(self):
        self.game.player_hit()
        self.update_ui()

    def stay(self):
        self.game.player_stay()
        self.update_ui()

    def double_down(self):
        self.game.player_double_down()
        self.update_ui()

    def split(self):
        self.game.player_split()
        self.update_ui()

    def surrender(self):
        self.game.player_surrender()
        self.update_ui()

    def handle_insurance(self):
        wants_insurance = messagebox.askyesno("Insurance", self.game.message)
        self.game.resolve_insurance(wants_insurance)
        self.update_ui()

    def new_game(self):
        self.game = BlackjackGame()
        self.update_ui()

if __name__ == '__main__':
    root = tk.Tk()
    app = BlackjackGUI(root)
    root.mainloop()
