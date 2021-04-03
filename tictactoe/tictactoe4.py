import random
import json
import numpy as np
import matplotlib.pyplot as plt

# This version is for tuning the algorithm parameters - instrumentation added...

# This game engine is based on Q Learning (a form of Reinforcement Learning)
# GUI version for Pythonista
# 
# Mar 2018
# Modified to account for the 8-fold symmetry of the board by mapping all board symmetries to
# the policy to accelerate learning rate.
# Scene-based iPad GUI replaces console interface
# Classes:
# Board - abstractions for the gameboard including logging moves printable representations
# TTT - TicTacToe Game engine 
# Myscene - GUI for iPad
#
# TicTacToe Conventions:
# 1) The board is numbered
#    1 2 3
#    4 5 6
#    7 8 9
# 2) Internally represented as a list of length 10, where:
#    The zeroth entry is unused to true up with the human numbering convention
#    0 denotes an empty square, 1 is a computer-held square, and -1 is a player-held square
#    This way, you can sum values in a row, col, of diag
#    to identify a win (+3), a loss (-3), or a threat (2 of 3 occupied)
#    The list of these sums is called the Threat Vector
# 3) 'X' is assigned to the first player to move

class Board:
	# Tuple <wins> lists all winning tictactoes, ordered so as to favor stronger moves
	# by the heuristic in my_moves
	wins = ((5,1,9), (5,3,7), (5,2,8), (5,4,6), (1,3,2), (7,9,8), (1,7,4), (3,9,6))
	
	def __init__(self, movelist=None):
		self.clear()
		if movelist is not None:
			self.preset(movelist)
	
	
	def preset(self, movelist):
		assert len(movelist) > 0
		for m in movelist:
			self.move(m)
	
	
	def clear(self):
		''' Clear the board for a new game
		'''
		# ordered list of moves in the game
		self.moves = []
		
		# <this_game> lists moves of the current game numerically in move order. 
		# At the end of the game, <game_over> walks through <policy> and adjust the weights of 
		# corresponding entries based on game outcome.
		# initialize with an empty board
		self.this_game = [self.string()]
		
		self.result = ''
		# <threats> weights potential wins from the perspective of next player to move. 
		# Each entry maps to the <wins> tuple
		self.threats = []
		self.check()
		
				
	def string(self, moves=None):
		''' Return a string[10] representation of the current board state
			First char is guaranteed to be a space
		'''
		if moves is None:
			moves = self.moves
		
		bd = [' ']
		for i in range(9):
			bd.append('-')
		
		markers = 'XO'
		f = 0
		for m in moves:
			bd[m] = markers[f]
			f ^= 1		# toggle the index flag between 0 and 1
		
		s = ''.join(bd)
		
		assert len(s) == 10
		assert s[0] == ' '
		return s
	
	
	def print(self):
		''' Print a representation of the board to the console
		'''
		bd = self.string()
		print(' ')
		for r in range(1, 8, 3):
			print(bd[r], bd[r+1], bd[r+2])
	
	
	def check(self):
		''' Check board for wins, return True if game is still on, False if it’s over.
		
		Side-effects: 
		Calculate the threat vector from the point of view of the next player to move: 
		+ positive weights for next player’s opportunities, 
		- negative weights for next player’s threats
		Set <result> string if game is over
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
			self.result = 'win'
			return False
		elif len(self.moves) > 8:
			self.result = 'draw'
			return False
		else:
			return True
	
		
	def move(self, m):
		''' Do housekeeping associated with taking a square. 
		'''
		# Fail if tile out of range, game over, or tile is already occupied 
		assert m in range(1, 10)
		assert len(self.moves) < 9
		assert self.result == ''
		assert m not in self.moves
		
		self.moves.append(m)
		self.this_game.append(self.string())
		return self.check()
		
	
	def opens(self):
		''' Return list of open squares
		'''
		opens = [i for i in range(1, 10) if i not in self.moves]
		return opens
	
		
	def transform(self, n):
		''' Perform a transform on the move list. Transform is defined by a length 10 
			transform tuple below. 
			Return the result without changing the board
		'''
		xforms = ((0, 1,2,3, 4,5,6, 7,8,9), (0, 7,4,1, 8,5,2, 9,6,3),
				  (0, 9,8,7, 6,5,4, 3,2,1), (0, 3,6,9, 2,5,8, 1,4,7), 
				  (0, 3,2,1, 6,5,4, 9,8,7), (0, 9,6,3, 8,5,2, 7,4,1),
				  (0, 7,8,9, 4,5,6, 1,2,3), (0, 1,4,7, 2,5,8, 3,6,9))
		
		assert(n < 8)
		xform = xforms[n]
		moves = self.moves		
		result = []
		
		for i in range(len(moves)):
			result.append(xform[moves[i]])
		return result		
	
	
class TTT:
	# Game engine for TicTacToe
	#
	# The <policy> dictionary keeps a history of all board positions encountered, paired with a
	# list of possible response moves. It is initialized with a response to an empty board.
	# Key notation is: '-' open tile, 'X' first turn, 'O' second turn.
	# All keys are length 9. 
	# Value is a list of length 9 floats corresponding to the reward weight for each tile
	# Several players are defined here: 
	# puny_human captures a move from the console by blocking for input
	# shallow_thought is a detuned heuristic player designed as a sparring partner
	# the_Q uses machine learning techniques to choose its moves
	
	policy = {}
	chatty = False
	alpha = 0.9
	beta = 0.5
	pwld = np.zeros(4)
	stats = [[],[],[],[]]		# records, wins, losses, draws	
	
	def __init__(self, train=None):
		# Mode selection - train or play
		if train is None:
			train = False	
		self.training = train
		
		# Make a clean board 
		self.board = Board()
		assert len(self.board.moves) == 0

		if train:
			self.set_players(self.the_Q, self.shallow_thought)
		else:
			self.set_players(self.the_Q, self.your_move)

		
	def set_players(self, p1, p2):
		# Select first to move from the two opponents
		# self.players[0] is first to move and gets 'X'
		self.players = [p1, p2]
		if random.choice([0, 1]) == 0:
			self.players = list(reversed(self.players))
		self.turn = self.players[0]

		
	def new_game(self, train=None):
		''' Clear only in-game state, leave the policy dict alone.
		'''
		if train is None:
			train = False
		self.__init__(train)
		if not self.training:
			print(self.turn.__name__, 'is X')
		self.play()
	
	
	def play(self):
		i = 0
		
		while self.turn():
			assert self.board.result == ''
			i ^= 1
			self.turn = self.players[i]

		if self.board.result == 'win':
			if self.turn.__name__ == "the_Q":
				self.pwld[1] += 1
			else:
				self.pwld[2] += 1
				
			self.update_policy()
		else:
			self.pwld[3] +=1
		
		self.pwld[0] = len(self.policy)
	
	
	def train(self, n=100):
		''' Run training matches between the_Q and shallow_thought
			Log number of wins, losses, draws and size of policy
			Use save() to persist the policy dict '''
		self.pwld=[0,0,0,0]
		for ng in range(n):
			self.new_game(True)	
		
#		print("Records: {0:4} Win: {1:2} Lose: {2:2} Draw: {3:2}".format(*self.pwld))
		for i in range(4):
			self.stats[i].append(self.pwld[i])


	def printable(self):
		return self.board.string()
	
	
	def print_board(self):
		if not self.training:
			self.board.print()
		
		
	def log_move(self, m):
		f = self.board.move(m)
		if self.chatty:
			key = self.board.string()
			print('# Logged: ', key, ' Result =', self.board.result, ' returning ', str(f))
		return f
	
	
	def shallow_thought(self):
		''' Choose move heuristically using the threat vector updated by board.check()
		
			First move: pick a tile at random to explore the state space for the_Q
			Subsequent moves:
			(Strategy denotes order of lines to target from threat vector)
			> First try to win (2)
			> Then try to block a loss (-2)
			> Then try to threaten a win (1)
			> Then try to block player’s threat
			> If all else fails choose an open tile at random
			This version is designed as a sparring partner for the_Q as opposed to the best possible
			heuristic opponent
		'''
		# entering the move, the game should not be over!
		assert self.board.result == ''
		# set a sentinel value so we can tell whether a move has been selected
		m = -1
		# first move is a random choice biased toward the "good" tiles
		if len(self.board.moves) == 0:
			m = random.choice((5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 3, 5, 7, 9, 1, 3, 5, 7, 9))
			# all other moves use a heuristic to select
			# among the open squares based on the <threats> vector
		else:
			threats = self.board.threats
			wins = self.board.wins
			
			strategy = (2, -2, 1, -1)
			for s in strategy:
				if s in threats:  # Get all threat lines that match the criterion:
					lines = []
					for i in range(len(threats)):
						if threats[i] == s:
							lines.append(i)
					if len(lines) == 0:
						continue
					i = random.choice(lines)
					line = wins[i]
					moves = []
					for j in line:				# choose an empty tile
						if j not in self.board.moves:
							moves.append(j)
					if len(moves) > 0:
						m = random.choice(moves)
						break
					
		# if we still don’t have a selection, choose among the open tiles
		# in heuristic order: center, corners, then edges
		if m == -1:
			opens = self.board.opens()
			for trial_move in (5, 1, 3, 9, 7, 2, 4, 6, 8):
				if trial_move in opens:
					m = trial_move
					break
					
		# We must have chosen a move by now - otherwise the game was already over
		assert m != -1
		return self.log_move(m)
	
	
	def your_move(self, m):
		''' GUI interface to select a tile
		'''
		opens = self.board.opens()
		if m not in opens:
			return False

		self.log_move(m)
		return True
	
	
	def puny_human(self):
		''' Prompt via console to choose a valid move
		'''
		
		opens = self.board.opens()		
		self.board.print()
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
	

	def the_Q(self):
		''' Select the move with highest reward value in the current board state in <policy>
		'''
		bd = self.board.this_game[-1]
		if not bd in self.policy:
			self.init_policy_entry(bd)
		pol = self.policy[bd]
		maxpol = max(pol)
		# If there is a single maximum reward, choose it.
		# Otherwise choose randomly among the biggest rewards.
		maxes = []
		for m in range(1, len(bd)):
			if pol[m] == maxpol:
				maxes.append(m)
		
		assert len(maxes) > 0
		if len(maxes) == 1:
			m = maxes[0]
		else:
			m = random.choice(maxes)
		return self.log_move(m)
	
	
	def save(self):
		f = open('tttpolicy', 'w')
		json.dump(self.policy, f)
		f.close()
	
	
	def load(self):
		f = open('tttpolicy', 'r')
		self.policy = json.load(f)
		f.close()
		print('Loaded {} Policy records'.format(len(self.policy)))		
		
		
	def init_policy_entry(self, bd):
		''' Create a new entry in <self.policy> corresponding to configuration <bd>
		
		<bd> in the format returned by board.string()
		'''
		assert bd not in self.policy
		assert len(bd) == 10
		assert bd[0] == ' '
		
		# Missing state: create, and zero out occupied tiles
		# to prevent the algo from trying to take an occupied tile
		pol = []
		for i in range(len(bd)):
			if bd[i] == '-':
				pol.append(0.5)
			else:
				pol.append(0.0)
		self.policy[bd] = pol
		#if self.chatty:
		#	print('# Policy added: ', bd, ''.join(str(pol)))
	
	
	def dump_policy(self):
		for i, bd in enumerate(self.policy):
			pol = self.policy[bd]
			print(bd, end=' ')
			for f in pol:
				print('{:0.2f}'.format(f), end=' ')
			print(' ')
	
	
	def update_policy(self):
		# skip update if draw - nothing new to learn
		if self.board.result != 'win':
			return
		
		alpha = self.alpha
		beta  = self.beta
		
		# For each of the 8 symmetric transforms of the board:
		# Generate this_game, a list of policy keys based on the moves of the game
		for i in range(8):
			xform = Board(self.board.transform(i))
			assert(xform.result == 'win')
			# There should always be one more board state than the number of moves
			# since <this_game> starts with an empty board
			moves = xform.moves
			this_game = xform.this_game
			assert len(this_game) == 1 + len(moves)				
			# Work backwards through the game,
			# growing reward for winning moves,
			# and shrinking reward for losing moves.
			# Weaken the reward exponentially on earlier move pairs in the game.
			# If a game state is missing from the <policy>, create it with default values
			reward = 1
			for i in range(len(moves)-1, -1, -1):
				bd = this_game[i]
				if bd not in self.policy:
					self.init_policy_entry(bd)
				# grow/shrink rewards on winning/losing states
				m = moves[i]
				r = self.policy[bd]
				if reward > 0:		# augment winning move
					r[m] += (1 - r[m]) * alpha
				else:				# diminish losing move
					r[m] -= r[m] * alpha
					alpha *= beta	# diminish reward strength exponentially
				reward = -reward 

def test(a=0.9, b=0.3):	
	title = "alpha:{0}  Beta:{1}".format(a, b)
	print(title)
	plt.title(title)
	ntrain = 30
	nreps = 10
	avg = np.zeros((4, ntrain))
	for rep in range(nreps):
		print(rep, end=' ')
		game = TTT()
		game.stats =[[],[],[],[]]
		game.policy = {}
		game.alpha = a
		game.beta = b
		for n in range(ntrain):
			game.train(100)
		plt.plot(game.stats[2], c='0.7')
		plt.plot(game.stats[3], c='0.7')
		avg += game.stats
		
	avg /= nreps
	plt.plot(avg[2], c='red')
	plt.plot(avg[3], c='orange')
	plt.show()
	plt.close()

print("ready")

