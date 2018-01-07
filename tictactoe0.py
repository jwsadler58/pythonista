import random 

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
	# Tuple of all winning tictactoes, ordered so as to favor stronger moves
	# by the heuristic in my_moves
	wins = ((5,1,9), (5,3,7), (5,2,8), (5,4,6), (1,3,2), (7,9,8), (1,7,4), (3,9,6))
	
	def __init__(self):
		self.board = [0 for i in range(10)]		# board[0] is ignored to match human and computer notation
		self.turn = random.choice([self.my_move, self.your_move])
		self.n_moves = 0
		self.check_board()		# create self.threats 
		
	def check_board(self):
		''' Check board for wins, return True if game is still on, False if it’s over.
		'''
		r = []
		for line in self.wins:
			t = self.board[line[0]] + self.board[line[1]] + self.board[line[2]]
			r.append(t)
		
		self.threats = r
	
		if 3 in r:		# Program wins
			self.game_over('win')
			return False
		elif -3 in r:	# player wins
			self.game_over('lose')
			return False
		elif self.n_moves > 8:
			self.game_over('draw')
			return False
		else:
			return True
		
	def game_over(self, outcome):
		if outcome == 'win':
			print('\n=== I win! ===')
		elif outcome == 'lose':
			print('\n=== You win ===')
		else:
			print('\n=== Draw ===')
		
	def print_board(self):
		tile = ('X', '_', 'O')
		for row in range(3):
			xo = list(tile[self.board[row * 3 + col] + 1] for col in range(1, 4))
			print(' {} {} {}'.format(xo[0], xo[1], xo[2]))
	
	def my_move(self):
		''' Choose move heuristically.
		
		First move: pick corner or center at random. 
		Subsequent moves:
		(Strategy denotes order of lines to target from threat vector)
		> First try to win (2)
		> Then try to block a loss (-2)
		> Then try to threaten a win (1)
		> Then try to block player’s threat
		> If all else fails choose an open tile at random
		'''

		# set a sentinel value so we can tell whether a move has been selected
		m = -1

		# first move is a random choice among the "good" tiles
		if self.n_moves == 0:
			m = random.choice((1, 3, 5, 7, 9, 5))
			# all other moves use a heuristic to select among the open squares based on the threat vector
		else:
			strategy = (2, -2, 1, -1)
			for s in strategy:
				if s in self.threats:
					i = self.threats.index(s)
					line = self.wins[i]
					for i in line:				# find an empty tile and take it
						if self.board[i] == 0:
							m = i
							break
				if m != -1:
					break
					
		# if we still don’t have a selection, choose among the open tiles
		# in heuristic order: center, corners, then edges
		if m == -1:
			opens = [i for i in range(1, 10) if self.board[i] == 0]
			for tm in (5, 1, 3, 9, 7, 2, 4, 6, 8):
				if tm in opens:
					m = tm
					break
					
		# We must have chosen a move by now - otherwise the game was already over
		assert m != -1
		self.board[m] = 1
		self.n_moves += 1
		self.turn = self.your_move
		return self.check_board()
	
	def your_move(self):
		self.print_board()
		m = -1
		opens = [i for i in range(1, 10) if self.board[i] == 0]
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

		self.board[m] = -1 # grab the selected tile for the player
		self.n_moves += 1
		self.turn = self.my_move
		return self.check_board()
		
	def play(self):
		while self.turn():
			pass
		self.print_board()

game = ttt()
game.play()

