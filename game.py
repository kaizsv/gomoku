import numpy as np
import timeit
from player import Player
from agent import Agent
from board import Board

class Game:
    def __init__(self, size, renju):
        self.player1 = None
        self.player2 = None
        self.size = size
        self.renju = renju
        self.board = None
        self.condition = 1
        self.rl_iter_games = 100000
        self.d = 0
        self.game_condition()

    def game_condition(self):
        condition = input('\nChoose game mode\n1) single player\n2) learning\n3) exit\n>')
        if condition == 1:
            self.board = Board(n=self.size, r=self.renju, learning=False)
            first = input('\nYou want to play\n1) black\n2) white\n>')
            if first == 1:
                self.player1 = Player(1, False, self.board.size)
                self.player2 = Agent(2, False, self.board.size)
            elif first == 2:
                self.player1 = Agent(1, False, self.board.size)
                self.player2 = Player(2, False, self.board.size)
            # start game
            self.board.set_player(self.player1, self.player2)
            self.play_game()
        elif condition == 2:
            self.board = Board(n=self.size, r=self.renju, learning=True)
            self.player1 = Agent(1, True, self.board.size)
            self.player2 = Agent(2, True, self.board.size)
            # start learning
            self.reinforcement_learning()
        elif condition == 3:
            self.condition = 0
        else:
            # wrong input, choose again
            return self.game_condition()

    def reinforcement_learning(self):
        max_turn = self.board.size ** 2
        start_time = timeit.default_timer()
        for j in range(self.rl_iter_games):
            #if j % 1000 == 0:
            print j
            self.board.reset()
            reward = 0
            winner = 0
            states_seq = []
            action_prob_seq = []
            action_seq = []
            # black first move
            action = self.player1.fair_board_move(self.board)
            if self.d:
                print '\nfirst ', action
            for turn in range(max_turn):
                # even for player1 (black), odd for player2 (white)
                if turn & 1:
                    player = self.player2
                    opponent = self.player1
                else:
                    player = self.player1
                    opponent = self.player2

                # current state
                state = self.board.set_next_state(action, symbol=player.player)
                # opponent's action
                opponent_state = opponent.convert_state(state)
                action_prob = self.board.forward(opponent_state)
                action = opponent.move(action_prob, self.board.legal_moves)
                while not self.board.is_legal_move(action):
                    print 'b'
                    a_gold = np.zeros(max_turn)
                    a_gold[action] = -1
                    self.board.backward(opponent_state, a_gold, self.d)
                    action_prob = self.board.forward(opponent_state)
                    action = opponent.move(action_prob, self.board.legal_moves)

                if self.d:
                    print 'state ', state
                    print 'opp_state ', opponent_state
                    print 'action_prob ', action_prob
                    print 'action ', action
                states_seq.append(state)
                action_prob_seq.append(action_prob)
                action_seq.append(action)
                if self.board.is_terminal(action, symbol=opponent.player):
                    # opponent win
                    if self.d:
                        print 'winner ', opponent.player
                    reward = 1
                    winner = opponent.player
                    break
                elif self.board.is_full():
                    # tie game
                    if self.d:
                        print 'tie'
                    reward = 0
                    winner = 0
                    break

            if reward == 0:
                continue
            for idx in range(len(states_seq)):
                if idx & 1:
                    #continue
                    player = self.player2
                    opponent = self.player1
                else:
                    player = self.player1
                    opponent = self.player2
                # current state
                state = states_seq[idx]
                # opponent's action
                state = opponent.convert_state(state)
                reward = opponent.get_reward(winner)
                a_gold_idx = action_seq[idx]
                a_gold = np.zeros(max_turn)
                a_gold[a_gold_idx] = reward
                if self.d:
                    print '\nb state ', state
                self.board.backward(state, a_gold, self.d)
                if self.d:
                    print 'b pre cal prob ', action_prob_seq[idx]
                    print 'b action ', a_gold_idx, 'reward ', reward
                    print 'b prob ', self.board.forward(state)
        end_time = timeit.default_timer()
        self.board.save_nn(self.rl_iter_games)
        print "Finish learning %d games in %d minutes" % (self.rl_iter_games, (end_time-start_time)/60)

    def play_game(self):

        # sub function for new game
        def new_game():
            c = input('\n1) New game?\n2) No, I want to leave\n>')
            if c != 1:
                print '\nBye Bye.\n'
                self.condition = 0

        if type(self.player1) is Agent:
            p, s = self.player1, 'p1_'
        else:
            p, s = self.player2, 'p2_'
        # start to play game
        if not self.board.load_nn(self.rl_iter_games):
            return
        max_turn = self.board.size ** 2
        print(self.board)
        # black first move
        action = self.player1.fair_board_move(self.board)
        if action < 0:
            new_game()
            return
        for turn in range(max_turn - 1):
            # even for player1 (black), odd for player2 (white)
            if turn & 1:
                player = self.player2
                opponent = self.player1
            else:
                player = self.player1
                opponent = self.player2

            # current state
            state = self.board.set_next_state(action, symbol=player.player)
            print(self.board)
            # opponent's action
            opponent_state = opponent.convert_state(state)
            if type(opponent) is Agent:
                action_prob = self.board.forward(opponent_state)
            action = opponent.move(action_prob, self.board.legal_moves)
            while not self.board.is_legal_move(action) and not action < 0:
                if type(opponent) is Player:
                    print 'Illegal move'
                action = opponent.move(action_prob, self.board.legal_moves)
            if action < 0:
                new_game()
                return
            if self.board.is_terminal(action, symbol=opponent.player):
                # opponent win
                state = self.board.set_next_state(action, symbol=opponent.player)
                print(self.board)
                if type(opponent) is Player:
                    print '\nGood job, You win!!!\n'
                else:
                    print '\nToo bad, player ' + str(player.player) + ' beats you!!!\n'
                new_game()
                return
            elif self.board.is_full():
                print '\nTie game\n'
                new_game()
                return
