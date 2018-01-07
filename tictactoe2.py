import random
import json

# This game engine is based on Q Learning (a form of Reinforcement Learning)
#
# TicTacToe basics
# The board is numbered
# 123
# 456
# 789
# and represented as a list of length 10, where the zeroth entry is unused
# where 0 is an empty square, 1 is a computer-held square, and -1 is a player-held square
# using this convention you can add up the values of the squares in a row, col, of diag to determine 
# whether there is a win (+3), a loss (-3), or a threat (2 of 3 occupied)

class ttt:
	# Tuple <wins> lists all winning tictactoes, ordered so as to favor stronger moves
	# by the heuristic in my_moves
	wins = ((5,1,9), (5,3,7), (5,2,8), (5,4,6), (1,3,2), (7,9,8), (1,7,4), (3,9,6))
	# The <policy> dictionary keeps a history of all board positions encountered, paired with a
	# list of possible response moves. It is initialized with a response to an empty board.
	# Key notation is: '-' open tile, 'X' first turn, 'O' second turn.
	# All keys are length 9. 
	# Value is a list of length 9 floats corresponding to the reward weight for each tile
	policy = {}
	chatty = False
	
	def __init__(self, train=False):
		# <moves> is the sequence of tiles chosen in the game 
		self.moves = []
		# Clear and then populate the threat vector
		self.threats = []
		self.check_board()
		self.result = ''
		# Mode selection - train or play
		if train:
			self.set_players(self.the_Q, self.shallow_thought)
		else:
			self.set_players(self.the_Q, self.puny_human)
		# <this_game> lists moves of the current game numerically in move order. 
		# At the end of the game, <game_over> walks through <policy> and adjust the weights of 
		# corresponding entries based on game outcome.
		# initialize with an empty board
		self.this_game = [self.printable()]
	
	def set_players(self, p1, p2):
		# Select first to move from the two opponents
		# self.players[0] is first to move and gets 'X'
		self.players = [p1, p2]
		if random.choice([0,1]) == 0:
			self.players = list(reversed(self.players))
		self.turn = self.players[0]
	
	def new_game(self, train=False):
		''' Clear only in-game state, leave the policy dict alone.
		'''
		self.__init__(train)
		print(self.turn.__name__, 'is X')
		self.play()
	
	
	def printable(self):
		''' Return a string representation of the current board state
		
		First char is guaranteed to be a space
		'''
		
		bd = [' ']
		for i in range(9):
			bd.append('-')
		
		markers = 'XO'
		f = 0
		for m in self.moves:
			bd[m] = markers[f]
			f ^= 1		# toggle the index flag between 0 and 1
		
		s = ''.join(bd)
		assert len(s) == 10
		assert s[0] == ' '
		return s
	
	
	def print_board(self):
		if not self.puny_human in self.players:
			return
		print(' ')
		bd = self.printable()
		for r in range(1, 8, 3):
			print(bd[r], bd[r+1], bd[r+2])
	
	
	def check_board(self):
		''' Check board for wins, return True if game is still on, False if it’s over.
		
		Side-effect: Calculate the threat vector from the point of view of the 
		next player to move: positive weights for next player’s opportunities, 
		negative weights for next player’s threats
		'''
		# Construct board weighted from the perspective of next player to move
		board = [0 for i in range(10)]
		weight = -1
		for m in list(reversed(self.moves)):
			board[m] = weight
			weight = -weight
		# Calculate the threat vector and assign it to self.threats
		r = []		
		for line in self.wins:
			t = board[line[0]] + board[line[1]] + board[line[2]]
			r.append(t)
		self.threats = r
		
		# final move of the game is either a win or a draw
		# 3 in r would imply that next player to move already won - that’s an error
		assert 3 not in r
		if -3 in r:
			print('===', self.turn.__name__, 'wins! ===')
			self.result = 'win'
			return False
		elif len(self.moves) > 8:
			self.result = 'draw'
			print('=== Draw ===')
			return False
		else:
			return True
	
		
	def log_move(self, m):
		''' Do housekeeping associated with taking a square. 
		'''
		# Fail if tile out of range, more than 8 moves, or tile is already occupied 
		assert m in range(1, 10)
		assert len(self.moves) < 9
		assert m not in self.moves
		
		self.moves.append(m)
		key = self.printable()
		self.this_game.append(key)
		if self.chatty:
			print('# Logged: ', key)
		return self.check_board()
	
	
	def shallow_thought(self):
		''' Choose move heuristically using the threat vector updated by check_board()
		
		First move: pick corner or center at random. 
		Subsequent moves:
		(Strategy denotes order of lines to target from threat vector)
		> First try to win (2)
		> Then try to block a loss (-2)
		> Then try to threaten a win (1)
		> Then try to block player’s threat
		> If all else fails choose an open tile at random
		This version is less deterministic to be a sparring partner for the_Q
		'''
		# set a sentinel value so we can tell whether a move has been selected
		m = -1
		# first move is a random choice among the "good" tiles
		if len(self.moves) == 0:
			m = random.choice((1, 3, 5, 7, 9, 5))
			# all other moves use a heuristic to select among the open squares based on the threat vector
		else:
			strategy = (2, -2, 1, -1)
			for s in strategy:
				if s in self.threats:  # Get all threat lines that match the criterion
					lines = []
					for i in range(len(self.threats)):
						if self.threats[i] == s:
							lines.append(i)
					if len(lines) == 0:
						continue
					i = random.choice(lines)
					line = self.wins[i]
					moves = []
					for j in line:				# choose an empty tile
						if j not in self.moves:
							moves.append(j)
					if len(moves) > 0:
						m = random.choice(moves)
						break
					
		# if we still don’t have a selection, choose among the open tiles
		# in heuristic order: center, corners, then edges
		if m == -1:
			opens = [i for i in range(1, 10) if i not in self.moves]
			for tm in (5, 1, 3, 9, 7, 2, 4, 6, 8):
				if tm in opens:
					m = tm
					break
					
		# We must have chosen a move by now - otherwise the game was already over
		assert m != -1
		return self.log_move(m)
	
	
	def puny_human(self):
		''' Prompt console to choose a valid move, or pick on at random
		'''
		
		self.print_board()
		m = -1
		opens = [i for i in range(1, 10) if i not in self.moves]
		try:
			m = int(input('your move? '))
			if m not in opens:
				print('Valid moves are ', str(opens))
				m = int(input('your move? '))
		except ValueError:
			print("Please enter a valid digit next time")
	
		if m not in opens:
			m = int(random.choice(opens))
			print ('I chose {} for you'.format(m))

		return self.log_move(m)
	
	
	def init_policy_entry(self, bd):
		''' Create a new entry in <self.policy> corresponding to configuration <bd>
		
		<bd> in the format returned by printable()
		'''
		assert bd not in self.policy
		assert len(bd) == 10
		assert bd[0] == ' '
		
		# Missing state: create one, zero out occupied tiles
		pol = []
		for i in range(len(bd)):
			if bd[i] == '-':
				pol.append(0.5)
			else:
				pol.append(0.0)
		self.policy[bd] = pol
		if self.chatty:
			print('# Policy added: ', bd, ''.join(str(pol)))
	
	
	def dump_policy(self):
		for i, bd in enumerate(self.policy):
			pol = self.policy[bd]
			print(bd, end=' ')
			for f in pol:
				print('{:0.2f}'.format(f), end=' ')
			print(' ')
	
	
	def update_policy(self):
		# skip update unless win
		if self.result != 'win':
			return
		# There should always be one more board state than the number of moves
		# since <this_game> starts with an empty board 
		assert len(self.this_game) == 1 + len(self.moves)
		
		alpha = 0.3
		beta  = 0.8
		reward = 1
		# Work backwards through the game,
		# growing reward for winning moves,
		# and shrinking reward for losing moves.
		# Weaken the reward exponentially on earlier move pairs in the game.
		# If a game state is missing from the <policy>, create it with default values
		for i in range(len(self.moves)-1, -1, -1):
			bd = self.this_game[i]
			if bd not in self.policy:
				self.init_policy_entry(bd)
			# grow/shrink rewards on winning/losing states
			m = self.moves[i]
			r = self.policy[bd]
			if reward > 0:		# augment winning move
				r[m] += (1 - r[m]) * alpha
			else:				# diminish losing move
				r[m] -= r[m] * alpha
				alpha *= beta	# diminish reward strength exponentially
			reward = -reward 
	
	
	def the_Q(self):
		''' Select a move using Markov process on the <policy> list
		'''
		bd = self.this_game[-1]
		if not bd in self.policy:
			self.init_policy_entry(bd)
		pol = self.policy[bd]
		# If there is a single maximum reward, choose it.
		# Otherwise choose randomly among the biggest rewards.
		max = 0.0
		maxes = []
		for m in range(1, len(bd)):
			if pol[m] > max:
				max = pol[m]
		for m in range(1, len(bd)):
			if pol[m] == max:
				maxes.append(m)
		
		assert len(maxes) > 0
		if len(maxes) == 1:
			m =maxes[0]
		else:
			m = random.choice(maxes)
		return self.log_move(m)

		# Generate random value scaled by total reward in the policy for this state
		'''
		t = 0.0
		for m in range(1, len(bd)):
			t += pol[m]
		r = t * random.random()
		# Use the cumulative reward to select a move
		t = 0.0
		for m in range(1, len(bd)):
			t += pol[m]
			if t > r:
				return self.log_move(m)
		assert False
		'''
	
	def save(self):
		f = open('polfile', 'w')
		json.dump(self.policy, f)
		f.close()
	
	def load(self):
		f = open('polfile', 'r')
		self.policy = json.load(f)
		f.close()
			
	def play(self):
		i = 0
		while self.turn():
			i ^= 1
			self.turn = self.players[i]
		
		self.update_policy()
		if self.chatty:
			self.print_board()

	def train(self, n=1000):
		for ng in range(n):
			self.new_game(True)	
		
		self.update_policy()
		print(len(self.policy), 'Policy records')
		if self.chatty:
			self.print_board()


if __name__ == '__main__':
	game = ttt()
	game.load()
	game.play()

