import random
import json


class Player:
    
    def __init__(self, n) -> None:
        self.player_name = n
        self.player_hand = []
        self.player_score = 0
class Game:
    def __init__(self):
        self.deck = []
        self.players = []
        self.number_of_players = 0
        self.discard_pile = []
        self.fini = False
        self.turn = 0
        self.hole = 1
            
            
    def get_player_names(self):
        return_players = []
        for p in self.players:
            return_players.append(p.player_name)
        return return_players
            
    def add_player(self,player_name):
        player = Player(player_name)
        self.players.append(player)
        print("added {player.player_name}")
        self.number_of_players += 1
        
    def remove_player(self,player_name):
        self.players.remove(player_name)
        print("removed {player.player_name}")
        self.number_of_players -=1
        
    def play(self):
        while self.hole < 10:
            print(f"Hole {self.hole}")
            self.print_player_board()
            for x, _ in enumerate(self.players):
                print(f"{self.players[x].player_name} Which Card would you like to flip over:", end =" ")
                num1 = int(input())
                print("Pick another:", end =" ")
                num2 = int(input()) 
                self.first_flips(self.players[x],num1,num2)
            rounds = 0;
            while not self.fini:
                if rounds == 0:
                    self.discard_pile.append(self.draw_top_card())
                
                for x, player in enumerate(self.players):
                    if rounds%len(self.players) == x:
                        self.player_turn(self.players[x])
                if not self.fini:
                    self.check_fini();
                rounds += 1;
            for x, player in enumerate(self.players):               
                if player != self.players[(rounds-1)%len(self.players)]:
                    self.player_turn(player)
            self.flip_all()
            self.print_player_board()
            for player in self.players:
                self.score(player)
            for player in self.players:
                print(player.player_score)
            self.hole +=1
            self.reset
        
                                            
    def draw_top_card(self):
        return self.deck.pop()
    
    def print_card(self, card):
        return f"{card[0]} of {card[1]}"
    
    def print_player_board(self):
        for number_of_players, player in enumerate(self.players):
            num = 0
            print(f"      player{number_of_players+1}'s hand\n")
            for x in range(2):
                for y in range(3):
                    revealed, card = player.player_hand[num]
                    if not revealed:
                        print(num+1, end = "               ");
                    else:
                        print(self.print_card(card),end = "   ")
                    num +=1
                print("\n");
    
                   
    def deal_hand(self, player):
        for x in range(6):
            player.player_hand.append((False, self.deck.pop()))
            
    def flip(self,num,player):
        _ , card = player.player_hand[num-1]
        player.player_hand[num-1] = ((True,card)) 
    
    def flip_all(self):
        for player in self.players:
            _, cards = zip(*player.player_hand)
            for x in range(6):
                player.player_hand[x] = ((True,cards[x]))
            
    
    def replace_card(self,player,card,num):
        _, discard = player.player_hand[num-1]
        self.discard_pile.append(discard)
        player.player_hand[num-1] = ((True,card))
    
    def first_flips(self,player,num1,num2):
        self.flip(num1, player)
        self.flip(num2, player)
    
    def check_fini(self):
        for player in self.players:
            reveild, _ = zip(*player.player_hand)
            if all (reveild):
                self.fini = True
                
    def score(self,player):
        for x, card in enumerate(player.player_hand):
            card_number = card[1][0]
            if card_number == ("Jack"):
                self.check_for_cancel(player,x,10)
            elif card_number == ("King"):
                self.check_for_cancel(player,x,0)
            elif card_number == ("Queen"):
                self.check_for_cancel(player,x,-1)
            elif card_number == ("Joker"):
                self.check_for_cancel(player,x,-5)
            elif card_number == ("2"):
                self.check_for_cancel(player,x,-2)
            elif card_number == ("Ace"):
                self.check_for_cancel(player,x,1)
            else:
                self.check_for_cancel(player,x,int(card_number))
    
    def check_for_cancel(self,player,card_index,value):
        card_number = player.player_hand[card_index][1][0]
        if(card_index<3):
            if(player.player_hand[card_index+3][1][0] != card_number):
                player.player_score += value
        elif(card_index>2):
            if(player.player_hand[card_index-3][1][0] != card_number):
                player.player_score += value

    def player_turn(self,player):
        self.print_player_board()
        print(self.discard_pile[len(self.discard_pile)-1])
        print(f"{player.player_name}, would you like too:\n1:Take this card\n2:Draw new card\nEnter 1 or 2:")
        input_value = int(input())
        if input_value == 2:
            self.discard_pile.append(self.draw_top_card())
            print(self.discard_pile[len(self.discard_pile)-1])
            print(f"{player.player_name}, would you like too:\n1:Take this card\n2:flip a card\nEnter 1 or 2:")
            input_value = int(input())
            if input_value == 1:
                print(f"{player.player_name}, choose where to put the card.")
                input_value = int(input())
                self.replace_card(player,self.discard_pile.pop(),input_value) 
            elif input_value == 2:
                print(f"{player.player_name}, choose a card to flip.")
                input_value = int(input())
                self.flip(input_value,player)
        else:
            print(f"{player.player_name}, choose where to put the card.")
            input_value = int(input())
            self.replace_card(player,self.discard_pile.pop(),input_value)
            
    def reset(self):
        suits = ("Hearts", "Diamonds", "Clubs", "Spades")
        ranks = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace")
        for suit in suits:
            for rank in ranks:
                self.deck.append((rank, suit))
        self.deck.append(("Joker", "Black"))
        self.deck.append(("Joker", "Red"))
        random.shuffle(self.deck)
    
    def game_state(self):
        state = {
            'hole': self.hole,
            'fini': self.fini,
            'discard_pile': self.discard_pile,
            'players': [player.to_dict() for player in self.players],  # Use the player's `to_dict` method
            'deck': self.deck  # You could also exclude the deck if you prefer to re-shuffle
        }
        return state
    
    def load_game_state(self, state):
        self.hole = state['hole']
        self.fini = state['fini']
        self.discard_pile = state['discard_pile']

        # Recreate players from the state
        self.players = []
        for player_state in state['players']:
            player = Player(player_state['name'])
            player.player_hand = player_state['hand']
            player.player_score = player_state['score']
            self.players.append(player)

        self.deck = state['deck']