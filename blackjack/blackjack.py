import random

class Card:
    def __init__(self, suit, rank, value):
        self.suit = suit
        self.rank = rank
        self.value = value

    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    def __init__(self):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
        values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
                  'Jack': 10, 'Queen': 10, 'King': 10, 'Ace': 11}
        self.cards = [Card(suit, rank, values[rank]) for suit in suits for rank in ranks]

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self):
        return self.cards.pop()

class Hand:
    def __init__(self):
        self.cards = []
        self.value = 0
        self.aces = 0

    def add_card(self, card):
        self.cards.append(card)
        self.value += card.value
        if card.rank == 'Ace':
            self.aces += 1
        self.adjust_for_ace()

    def adjust_for_ace(self):
        while self.value > 21 and self.aces:
            self.value -= 10
            self.aces -= 1

    def __str__(self):
        return ', '.join([str(card) for card in self.cards])

class Player:
    def __init__(self, name, balance):
        self.name = name
        self.balance = balance
        self.hand = Hand()

    def bet(self, amount):
        if amount > self.balance:
            raise ValueError("Insufficient balance to place this bet.")
        self.balance -= amount
        return amount

    def win_bet(self, amount):
        self.balance += amount

class Dealer:
    def __init__(self):
        self.hand = Hand()

    def play(self, deck):
        while self.hand.value < 17:
            self.hand.add_card(deck.deal_card())

class BlackjackGame:
    def __init__(self, player_name, balance):
        self.deck = Deck()
        self.deck.shuffle()
        self.player = Player(player_name, balance)
        self.dealer = Dealer()
        self.current_bet = 0

    def place_bet(self, amount):
        self.current_bet = self.player.bet(amount)

    def deal_initial_cards(self):
        for _ in range(2):
            self.player.hand.add_card(self.deck.deal_card())
            self.dealer.hand.add_card(self.deck.deal_card())

    def player_turn(self):
        while True:
            print(f"Your hand: {self.player.hand} (Value: {self.player.hand.value})")
            print(f"Dealer's visible card: {self.dealer.hand.cards[0]}")
            choice = input("Choose an action: (H)it, (S)tand, (D)ouble down: ").strip().lower()
            if choice == 'h':
                self.player.hand.add_card(self.deck.deal_card())
                if self.player.hand.value > 21:
                    print("You busted!")
                    return False
            elif choice == 's':
                return True
            elif choice == 'd':
                if self.player.balance >= self.current_bet:
                    self.player.bet(self.current_bet)
                    self.current_bet *= 2
                    self.player.hand.add_card(self.deck.deal_card())
                    if self.player.hand.value > 21:
                        print("You busted!")
                        return False
                    return True
                else:
                    print("Insufficient balance to double down.")
            else:
                print("Invalid choice.")

    def dealer_turn(self):
        print("Dealer's turn...")
        self.dealer.play(self.deck)
        print(f"Dealer's hand: {self.dealer.hand} (Value: {self.dealer.hand.value})")

    def determine_winner(self):
        if self.player.hand.value > 21:
            print("You lose this round.")
        elif self.dealer.hand.value > 21 or self.player.hand.value > self.dealer.hand.value:
            print("You win this round!")
            self.player.win_bet(self.current_bet * 2)
        elif self.player.hand.value < self.dealer.hand.value:
            print("You lose this round.")
        else:
            print("It's a push! Your bet is returned.")
            self.player.win_bet(self.current_bet)

    def reset_hands(self):
        self.player.hand = Hand()
        self.dealer.hand = Hand()

    def play(self):
        print(f"Welcome to Blackjack, {self.player.name}! Your starting balance is ${self.player.balance}.")
        while self.player.balance > 0:
            try:
                bet_amount = int(input(f"Place your bet (Balance: ${self.player.balance}): "))
                self.place_bet(bet_amount)
            except ValueError as e:
                print(e)
                continue

            self.deal_initial_cards()
            if self.player_turn():
                self.dealer_turn()
            self.determine_winner()
            self.reset_hands()

            if input("Play another round? (Y/N): ").strip().lower() != 'y':
                break
        print("Game over! Thanks for playing.")

if __name__ == "__main__":
    player_name = input("Enter your name: ")
    starting_balance = int(input("Enter your starting balance: "))
    game = BlackjackGame(player_name, starting_balance)
    game.play()
