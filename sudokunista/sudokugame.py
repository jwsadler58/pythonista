# Sudoku solver
# John Sadler 2019-2021
#
# Represent the game by:
# 1. an 81 element board list. Each square can have a value from 0..9, where 0 means uncommitted
# 2. a 9 element rows list. Each element is a set that represents the unused values in the row
# 3. a 9 element cols list analogous to the rows list
# 4. a 9 element boxes list analogous to rows and cols
# 5. a constant rcb lookup table of 81 elements. Each element is a tuple that contains row,col,box for
#    the corresponding square
#
# Solving strategies:
# 1. Intersect: Identify all squares with only one DoF and fill them
# 2. Subtract: Identify any R,C, or B where a value has exactly one unfilled 
#    square that can contain it. Fill it.
# 3. Recursive backtracking solver 
#
# Rate a game state based on difficulty to complete: determine level based on solve techniques required
# I'll use the length of the solve status string as a first approximation - it logs the chain of techniques
# hsolve used to find the solution. Intersect and Subtract are close to basic techniques a human would use to fill
# squares with no degrees of freedom or squares that are uniquely valued in an R, C, or B. Recursion is a guess, and
# has the potential to require backtracking. This is tedious for a human solver.
#
# Given a game state, rate its difficulty
# Create a game of a given difficulty
#
# Observations:
# A valid sudoku is still valid after 
# - permuting the rows in a band (row of 3 boxes), or the columns in a stack (column of 3 boxes)
# - permuting any two stacks or two bands
# - Remapping the symbols
# - Transposition, rotation, mirroring
# Any three boxes on a diagonal can be filled from an empty state with no Row Col coupling
# This suggests that many games can be generated at any given level from a "seed" game at that level 
# by applying the above rules
#

class Sudoku (object):
	def __init__(self, orig = None):
		''' Construct a blank game (make a copy of existing Sudoku if orig parameter is passed) 
		'''
		initset = {i+1 for i in range(9)}			# the set of all legal values
		self.board = [0 for i in range(81)]			# uncommitted squares are zero
		self.rows  = [initset.copy() for i in range(9)]
		self.cols  = [initset.copy() for i in range(9)]
		self.boxes = [initset.copy() for i in range (9)]
		
		# Map game level descriptions to a rating range associated with each level
		# The solver generates the rating, so this belongs here and not in the DB module
		#
		self.levels = ['Easy', 'Medium', 'Hard', 'Nuts']
		self.level_limits = [0, 5, 10, 22, 100]
			
		if orig is None:	# construct mapping table for row, col, box by square index
			self.rcb = []
			self.box_sq_map = [[] for i in range(9)]
			for sq in range(81):
				r = sq // 9
				c = sq % 9
				b  = 3 * (r // 3) + (c // 3)
				t = (r, c, b)
				self.rcb.append(t)
				self.box_sq_map[b].append(sq)
				self.log = ""
		else:				# copy constructor
			self.rcb = orig.rcb	# reference rather than copy - rcb is a constant
			self.box_sq_map = orig.box_sq_map
			occupied = [i for i in range(81) if orig.board[i] != 0]
			for sq in occupied:
				self.fill(sq, orig.board[sq])
			self.log = orig.log		# copy not reference for a string
		return	
		
	def nfilled(self):
		''' return the number of filled squares on the board
		'''
		n = 0
		for i in range(81):
			if self.board[i]:
				n += 1
		return n
	
		
	def get_row(self, sq):
		''' Given a square index 'sq', return the index of its row on the board (0..8)
		'''
		assert sq in range(81)
		return self.rcb[sq][0]
		
	def get_sqs_in_row(self, row):
		''' return the list of indices of squares in a given row (0..8)
		'''
		assert row in range(9)
		return [i for i in range(row*9, row*9+9)]
		
	def get_col(self, sq):
		''' Given a square sq, return the index of its column on the board (0..8)
		'''
		assert sq in range(81)
		return self.rcb[sq][1]

	def get_sqs_in_col(self, col):
		''' return the list of indices of squares in a given col (0..8)
		'''
		assert col in range(9)
		return [i for i in range(col, 81, 9)]
		
		
	def get_box(self, sq):
		''' Given a square sq, return the index of its box on the board (0..8)
		'''
		assert sq in range(81)
		return self.rcb[sq][2]
	
	
	def get_sqs_in_box(self, box):
		''' return a list of the indexes of squares in a given box
		'''
		assert box in range(9)
		return self.box_sq_map[box]
	
	
	def fill(self, sq, value):
		''' Fill a square with a value
		If value is zero, unfill the square
		If legal, assign value to square and update housekeeping lists
		Return a set of squares in any R,C, or B that got completed (or empty set) to celebrate progress
		'''
		assert sq in range(81)
		assert value in range(10)
		completed = set()

		if self.board[sq] != 0:
			self.unfill(sq)
		
		if value != 0:
			assert self.board[sq] == 0		# square must be unoccupied by now
			(r, c, b) = self.rcb[sq]
			
			assert value in self.rows[r]	# confirm value is legal
			assert value in self.cols[c]
			assert value in self.boxes[b]
	
			self.board[sq] = value
			self.rows[r].remove(value)
			self.cols[c].remove(value)
			self.boxes[b].remove(value)
			
			if len(self.rows[r]) == 0:
				completed = completed | set(self.get_sqs_in_row(r))
			if len(self.cols[c]) == 0:
				completed = completed | set(self.get_sqs_in_col(c))
			if len(self.boxes[b]) == 0:
				completed = completed | set(self.get_sqs_in_box(b))
			
		return completed
						

	def unfill(self, sq):
		''' Remove a value from a square, updating housekeeping lists
		'''
		assert sq in range(81)
		if self.board[sq] == 0:
			return
		value = self.board[sq]
		(r, c, b) = self.rcb[sq]
		assert value not in self.rows[r]
		assert value not in self.cols[c]
		assert value not in self.boxes[b]
		self.board[sq] = 0
		self.rows[r].add(value)
		self.cols[c].add(value)
		self.boxes[b].add(value)
		return
	
	
	def preload(self, bd):
		''' Load a saved game. 
		If bd is a list or string description, load it directly
		If bd is in self.levels, load a game at that level from the db
		'''	
		# convert string description to list
		if isinstance(bd, str) and len(bd) == 81:
			bd = list(map(int,bd))
		
		if isinstance(bd, list):
			for i in range(len(bd)):
				if bd[i] != 0:
					self.fill(i, bd[i])
				else:
					self.unfill(i)
			return 0
		else:
			return -1
		

	def __str__(self):
		s = ""
		for sq in self.board:
			s += str(sq)
		return s

		
	def print(self):
		''' console print the board
		'''
		spacer = "-"*10 + "+" + "-"*11 + "+" + "-"*10
		print(" ")
		for r in range(9):
			out = ""
			for c in range(9):
				sq = 9 * r + c
				v = self.board[sq]
				if v == 0:
					v = "_"
				if c in [2, 5]:
					out += str(v) + " | "
				else:
					out += str(v) + "   "
			print(out)
			if r in [2, 5]:
				print(spacer)
		return
	
	
	def get_sq_options(self, sq):
		''' Return the set of allowed values for the given square
		Returns an empty set if the square is occupied
		'''
		if self.board[sq] != 0:
			return set()

		rcb = self.rcb[sq]
		return self.rows[rcb[0]] & self.cols[rcb[1]] & self.boxes[rcb[2]]

	def get_opens(self):
		''' Return the list of indices of open squares
		'''
		return [i for i in range(81) if self.board[i] == 0]
	
	def get_opens_by_dof(self, rev=False):
		''' Return the list of (open square index, DoF) tuples sorted by ascending DoF
		'''
		opens = [(i, len(self.get_sq_options(i))) for i in range(81) if self.board[i] == 0]
		opens.sort(key = lambda x: x[1], reverse=rev)
		return [i for i,j in opens]
	
	
	def intersect(self):
		''' Heuristic: Iterate through the uncommitted squares of the board and fill any that have exactly one degree of freedom. Return True if any squares were filled, False if there was nothing to do.
		'''	
		n = 0
		for i in range(81):
			options = self.get_sq_options(i)
			if len(options) == 1:
				self.fill(i, options.pop())
				n += 1
		return n
	
	
	def _sub_factor(self, squares):
		''' helper for subtract: find squares that have unique options in an r,c, or b and fill them
		    Assumes all the given _squares_ are in a common r,c,or b
		'''
		n = 0
		for sq1 in squares:
			if self.board[sq1] != 0:	# only interested in unoccupied squares
				continue
			opt1 = self.get_sq_options(sq1) # now subtract all other squares in the rcb
			for sq2 in squares:
				if self.board[sq2] != 0 or sq2 == sq1:
					continue
				opt2 = self.get_sq_options(sq2)
				opt1 = opt1 - opt2
			# if sq1 can take a unique value, fill it
			if len(opt1) == 1:
				self.fill(sq1, opt1.pop())
				n += 1
		return n
	
	
	def subtract(self):
		''' Heuristic: Find uncommitted squares that allow one value uniquely in a given R,C, or B
		    Iterate through each row, column and box. Identify a square that has a unique option
		    Fill that value
		    This approximates the simplest technique a human player would use
		'''
		n = 0
		for box in range(9):
			n += self._sub_factor(self.get_sqs_in_box(box))
		for row in range(9):
			n += self._sub_factor(self.get_sqs_in_row(row))
		for col in range(9):
			n += self._sub_factor(self.get_sqs_in_col(col))
		return n
	
			
	def _uni_factor(self, sq, squares):
		options = self.get_sq_options(sq)
		for sq1 in squares:
			if sq1 == sq or self.board[sq1] != 0:
				continue
			options = options - self.get_sq_options(sq1)
		return options
		
	def sq_has_unique(self, sq):
		''' Examine r,c,b associated with the given _sq_. If one DoF of the square is unique to the rcb, return it. Else return None
		'''
		(r,c,b) = self.rcb[sq]
		options = self._uni_factor(sq, self.get_sqs_in_row(r))
		if len(options) == 1:
			return options.pop()
		options = self._uni_factor(sq, self.get_sqs_in_col(c))
		if len(options) == 1:
			return options.pop()		
		options = self._uni_factor(sq, self.get_sqs_in_box(b))
		if len(options) == 1:
			return options.pop()
		return None
		

	def solve(self):
		''' Brute force backtracking solver - as simple as possible. 
		Returns first solution it finds or None if unsuccessful
		'''
		# for each empty square
		#   fill a valid value, and solve the resulting board
		#     if it works, return True (solution is self.board)
		# ran out of squares with no solution - return False
		
		opens = self.get_opens_by_dof()
		# look for a solved game first
		if len(opens) == 0:	# no empty squares -> game solved
			return True
		
		for sq in opens:
			options = self.get_sq_options(sq)
			for value in options:
				self.fill(sq, value)
				if self.solve() == True:
					return True
				self.unfill(sq)   # restore the board state
			return False		

	def hsolve(self):
		''' Backtracking sudoku solver - mimics the way a human might do it to arrive at a rating
		1. Use intersect() and subtract() to do all the easy squares
		2. For each uncommitted square, for each allowed value, 
		fill the value and try solving the resulting game.
		Return True if solved. Otherwise returns False. 
		Self.board contains the solved game as a side effect
		'''	
		#Todo: advanceed solving strategies: eliminate paired and tripled squares
		# mark which squares have not been filled for rollback later
		opens = self.get_opens()
		savelog = self.log

		# terminal case: game already solved
		if len(opens) == 0:	# no empty squares -> game solved
			return True
		
		t = 0			
		while True:			# simplify before the recursive step
			n = self.intersect()
			if n == 0: break
			t += n
		if t > 0:
			self.log += 'i{0:02} '.format(t)

		t = 0
		while True:
			n = self.subtract()
			if n == 0: break
			t += n
		if t > 0:
			self.log += 's{0:02} '.format(t)
		
		# check for solved game before recursive step	
		# Dof reversed appears to be the fastest route to a solution
		open1 = self.get_opens_by_dof(True)
		savelog = self.log
		
		for sq in open1:
			options = self.get_sq_options(sq)
			for value in options:
				self.fill(sq, value)
				# only one 'r' per level
				self.log = savelog + '_r_ '
				if self.hsolve() == True:
					return True
				self.unfill(sq)   # restore the board state
			
			# did not find a solution - unwind and return
			self.log = savelog
			unwind = set(opens).difference(self.get_opens())
			for sq in unwind:
				self.unfill(sq)
			return False
			
		# at this point open1 is empty - meaning we've solved the sudoku
		return True					

# regression tests - note the harder games have multiple solutions so they may fail even if solved successfully
if __name__ == '__main__':
	import time
	
	def test():
		n = 0
		while True:
			game = Sudoku()
			nn = game.preload(n)
			print("\n\nOriginal ", n)
			print(str(game))
			game.solve()
			print("\nCompleted ", n)
			print(str(game))
			n = nn
			if n == 0:
				return
	
	def timetest(n):
		tstamp = time.perf_counter()
		for i in range(10):
			game = Sudoku()
			game.preload(n)
			game.solve()
		print("Time: ", time.perf_counter()-tstamp)
		
		
	from sudokudb import dbseed, SudokuDB
	def re_rate():
		db = SudokuDB()
		gtrd = db.get_all()
		for row in gtrd:
			prob = row[0]
			game = Sudoku()
			game.preload(prob)
			if game.hsolve():
				db.annotate(prob, game.log)
				print(f"Solved {prob} with rating {game.log}")
			else:
				print(f"Failed to solve {prob}")
		return
			
	for row in dbseed:
		prob = row[0]
		soln = row[1]
		game = Sudoku()
		game.preload(prob)
		# solve all the demo games and indicate whether solutions match
		# game may not have a single solution. hsolve and solve use different search strategies and may produce different results
		if game.hsolve():
			if str(game) == soln:
				print(f'hsolve PASS {row[4]}')
			else:
				print(f'hsolve DIFF***** {row[4]}\n{str(game)}\n{soln}')
		else:
			print(f'hsolve FAIL***** {row[4]}')

		game = Sudoku()
		game.preload(list(map(int,prob)))
		if game.solve():
			if str(game) == soln:
				print(f'solve  PASS: {row[4]}')
			else:
				print(f'solve  DIFF***** {row[4]}\n{str(game)}\n{soln}')
		else:
			print(f'solve  FAIL***** {row[4]}')		

