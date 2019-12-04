# Sudoku solver
# John Sadler 2019
#
# Graphical version provides training hints for any selected square. Green highlights in number pad are 
# legal options for the selected square (Intersect) 
# If there is a bright green highlight in the number pad, the selected square is the only one
# in its row, col, or block that can take that value (Subtract)
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
# 3. Recursive depth-first solver (compute intensive. The solver runs much faster when starting with  
#    squares with the fewest DoF)
#
# Rate a game state based on difficulty to complete: determine level based on solve techniques required 
# Easy   -> Intersect only
# Medium -> Intersect and Subtract
# Hard   -> Solve
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

class Sudoku (object):
	def __init__(self, orig = None):
		''' Construct a blank game (make a copy of existing Sudoku if orig parameter is passed) 
		'''
		initset = {i+1 for i in range(9)}			# the set of all legal values
		self.board = [0 for i in range(81)]			# uncommitted squares are zero
		self.rows  = [initset.copy() for i in range(9)]
		self.cols  = [initset.copy() for i in range(9)]
		self.boxes = [initset.copy() for i in range (9)]
	
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
		else:				# copy constructor
			self.rcb = orig.rcb	# reference rather than copy - rcb is a constant
			self.box_sq_map = orig.box_sq_map
			occupied = [i for i in range(81) if orig.board[i] != 0]
			for sq in occupied:
				self.fill(sq, orig.board[sq])
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
	
	
	def preload(self, bd=0):
		''' Assuming a fresh board, Load a preset game. 
			Returns next valid board index 
			Insane puzzle source: https://www.telegraph.co.uk/news/science/science-news/9359579/Worlds-hardest-sudoku-can-you-crack-it.html
		'''
		
		easy = [0,0,7, 0,3,0, 2,9,6, 0,0,0, 1,8,0, 0,0,4, 0,9,5, 6,2,0, 0,3,8,
				0,1,2, 0,0,0, 0,7,0, 5,7,0, 0,4,0, 9,0,0, 8,3,0, 0,0,1, 0,0,2,
				6,4,0, 0,0,2, 0,0,7, 3,5,0, 0,1,4, 6,0,0, 0,0,1, 0,9,0, 8,0,5]
		med  = [2,8,0, 0,0,4, 0,1,9, 0,9,0, 7,0,0, 3,5,2, 0,0,0, 0,1,0, 4,0,0, 
				0,3,0, 0,4,7, 0,0,0, 0,0,0, 0,8,0, 0,0,0, 0,0,0, 0,0,6, 0,9,0, 
				5,0,3, 6,7,2, 0,4,0, 0,6,0, 0,9,1, 0,0,0, 4,0,0, 0,0,5, 6,0,0]
		hard = [2,0,8, 0,0,1, 3,6,0, 5,0,9, 0,0,3, 1,0,0, 0,0,0, 0,0,0, 0,0,9, 
				0,0,3, 0,0,0, 0,1,2, 1,0,0, 0,2,0, 8,0,0, 0,9,0, 0,0,0, 0,0,7, 
				4,0,0, 0,7,0, 0,0,3, 6,0,0, 3,0,8, 0,4,0, 0,0,0, 0,0,0, 6,0,5]
		hard1= [0,0,0, 0,0,0, 0,8,9, 0,0,7, 3,0,0, 0,5,0, 0,8,0, 0,5,4, 0,0,0,
				0,0,0, 7,0,0, 0,0,2, 0,0,6, 0,8,0, 7,0,0, 5,0,0, 0,0,9, 0,0,0,
				0,0,0, 2,1,0, 0,6,0, 0,4,0, 0,0,5, 2,0,0, 2,3,0, 0,0,0, 0,0,0]
		expt = [8,0,0, 1,0,0, 5,4,0, 0,0,0, 2,0,0, 0,7,0, 0,7,5, 0,0,4, 0,9,0, 
				0,0,0, 9,1,0, 0,0,0, 0,0,9, 8,0,7, 0,5,2, 0,0,7, 0,0,5, 0,1,0, 
				1,0,0, 0,3,0, 0,2,7, 0,0,0, 7,9,2, 0,0,0, 0,0,0, 0,0,0, 0,0,0]
		expt1= [0,5,0, 7,3,0, 0,0,4, 0,0,8, 2,0,0, 0,0,0, 1,0,4, 0,0,8, 0,0,0, 
				5,0,3, 0,0,0, 0,0,2, 0,0,0, 0,0,0, 0,0,0, 0,8,2, 0,0,0, 0,7,0, 
				0,2,0, 0,6,5, 0,1,3, 0,1,0, 0,7,0, 0,0,0, 6,3,0, 1,0,0, 0,2,7]
		insane=[8,0,0, 0,0,0, 0,0,0, 0,0,3, 6,0,0, 0,0,0, 0,7,0, 0,9,0, 2,0,0,
				0,5,0, 0,0,7, 0,0,0, 0,0,0, 0,4,5, 7,0,0, 0,0,0, 1,0,0, 3,0,0,
				0,0,1, 0,0,0, 0,6,8, 0,0,8, 5,0,0, 0,1,0, 0,9,0, 0,0,0, 4,0,0,]
		
		boards = [easy, med, hard, hard1, expt, expt1, insane]
		#TODO: hard1 breaks the solver
		bd = bd % len(boards)
		board = boards[bd]
		for i in range(len(board)):
			if board[i] != 0:
				self.fill(i, board[i])
			else:
				self.unfill(i)
		return (bd + 1) % len(boards)
	

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
		'''
		if self.board[sq] != 0:
			return set()

		rcb = self.rcb[sq]
		return self.rows[rcb[0]] & self.cols[rcb[1]] & self.boxes[rcb[2]]

	def get_opens(self):
		''' Return the list of indices of open squares
		'''
		return [i for i in range(81) if self.board[i] == 0]
	
	def get_opens_by_dof(self):
		''' Return the list of (open square index, DoF) tuples sorted by ascending DoF
		'''
		opens = [(i, len(self.get_sq_options(i))) for i in range(81) if self.board[i] == 0]
		opens.sort(key = lambda x: x[1])
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
		


	def solve(self, depth=0):
		''' Backtracking sudoku solver - easy squares first
		1. Use intersect() and subtract() to do all the easy squares
		2. For each uncommitted square, fo.                                                                                                                                                                                                                                        r each allowed value, 
		fill the value and try solving the resulting game.
		Return the filled board if solved. Otherwise return None
		'''
		self.log = ""
		n = 1
		t = 0
		while n > 0:			# simplify as much as possible
			n = self.intersect()
			t += n
		if t > 0:
			self.log += 'i{0:02} '.format(t)

		n = 1
		t = 0
		while n > 0:
			n = self.subtract()
			t += n
		if t > 0:
			self.log += 's{0:02} '.format(t)
		
		opens = self.get_opens_by_dof()	# faster than reverse sort by DoF
		if len(opens) == 0:	# no empty squares -> game solved
			return self.board
					
		for sq in opens:
			rcb = self.rcb[sq]
			options = self.rows[rcb[0]] & self.cols[rcb[1]] & self.boxes[rcb[2]]
			if len(options) == 0:	# found an empty square that has zero DoF - unsolveable
				return None

			# recursive solve: try each possible value of the open square
			for value in options:
				testgame = Sudoku(self)
				testgame.fill(sq, value)
				bd = testgame.solve(depth+1)
				if bd is not None:
					self.log += 'r{0:02} '.format(depth) + testgame.log
					for i in range(81):
						self.fill(i, bd[i])
					return bd
		return None
	

#
# Graphical part of the game for Pythonista
#

from scene import *
import sound
A = Action

class MyScene (Scene):
	def setup(self):
		self.background_color   = '#c4b9c2'
		board_color             = '#141c6d'
		self.key_disabled_color = '#888888'
		self.key_enabled_color  = '#84bb88'
		self.boardkey_color	    = '#1e1e1e'
		
		# Size the board to fit the tiles with a gap on all sides
		# The gameboard is 10 tiles wide and high. The control panels are 2.4 tiles wide and 10 high		# use the centerpoint of the display as the origin for placing the tiles
		# Node origins seem to default to their centerpoints, so this simplifies the math
		
		w = self.size.width
		h = self.size.height
		l_tile = self.l_tile = w // 14
		gap = self.gap = l_tile//10
		l_board = (9 * l_tile) + (10 * gap)

		tile_shape = ui.Path.rounded_rect(0, 0, l_tile, l_tile, l_tile/8)
				
		# Build the board display
		board_shape = ui.Path.rounded_rect(0, 0, l_board, l_board, l_tile/6)
		self.board = ShapeNode(path=board_shape, parent=self)
		self.board.fill_color = board_color
		self.board.size = (l_board, l_board)
		self.board.position = self.size/2 + ((w - h)// 2, 0)
		
		# build the number pad display
		w_panel = l_tile + (2 * gap)
		panel_shape = ui.Path.rounded_rect(0, 0, w_panel, l_board, l_tile/6)
		self.panel = ShapeNode(path=panel_shape, parent=self)
		self.panel.fill_color = board_color
		self.panel.size = (w_panel, l_board)
		self.panel.position = (2*(w-h)//3, h//2)
		# build the numeric pad
		self.digits = []
		for row in range(-4, 5):
			key = ShapeNode(path=tile_shape, parent=self.panel)
			key.size = (l_tile, l_tile)
			key.position = (0, row * (l_tile + gap))
			key.fill_color = self.key_disabled_color
			key.value = row + 5
			label = LabelNode(str(key.value), font=('Marker Felt', l_tile/2), parent=key)
			self.digits.append(key)
		
		# build controls display
		self.cpanel = ShapeNode(path=panel_shape, parent=self)
		self.cpanel.fill_color = board_color
		self.cpanel.size = (w_panel, l_board)
		self.cpanel.position = ((w-h)//3 - self.gap, h//2)
		
		# Associate control legends with actions to do
		labels = [("clear", self.do_clear,     self.ctrl_always),
				  ("load",  self.do_preload,   self.ctrl_always),
				  ("undo",  self.do_undo,      self.ctrl_fundo),
#				  ("intr",  self.do_intersect, self.ctrl_fsolvable),
#				  ("sub",   self.do_subtract,  self.ctrl_fsolvable),
				  ("solve", self.do_solve,     self.ctrl_fsolvable)]

		self.controls = []
		for row in range(len(labels)):
			key = ShapeNode(path=tile_shape, parent=self.cpanel)
			key.size = (l_tile, l_tile)
			key.position = (0, row * (l_tile + gap) - 4 * (l_tile + gap))
			label = LabelNode(labels[row][0], font=('Marker Felt', l_tile/4), parent=key)
			key.action   = labels[row][1]
			key.fenabled = labels[row][2]
			key.fill_color = self.key_disabled_color
			self.controls.append(key)			
		
		# label display
		self.label = LabelNode('some text', font=('Chalkboard SE', l_tile/4))
		self.label.position = (w/2, 10)
		self.add_child(self.label)
		self.game = Sudoku()
		self.new_game()
	
			
	def new_game(self):
		self.game = Sudoku()
		self.selected_tile = None
		self.selected_key = None
		even_color =	'#ffd2a1'
		odd_color =     '#ffae55'
		l_tile = self.l_tile
#		self.status = 'Draw'
		gap = self.gap
		self.preload_index = 0
		self.undo = []		# each undo event is a list of (square, value) tuples
		
		# insert tiles onto board in order from top left to bottom right, row major order
		# so that the order they appear in <tiles> matches the convention in class <Sudoku>
		self.tiles = []
		index = 0
		tile_shape = ui.Path.rounded_rect(0, 0, l_tile, l_tile, l_tile/8)
		
		for row in range(4,-5,-1):
			for col in range(-4,5):
				tile = ShapeNode(path=tile_shape, parent=self.board)
				tile.size = (l_tile, l_tile)
				tile.position = (col * (l_tile + gap), row * (l_tile + gap))
				box = self.game.get_box(index)
				
				tile.ucolor = even_color if box % 2 == 0 else odd_color
				tile.fill_color = tile.ucolor
				tile.index = index
				v = self.game.board[index]
				ltext = ' ' if v == 0 else str(v) 
				label = LabelNode(ltext, font=('Marker Felt', l_tile/2), parent=tile)
				label.color = self.boardkey_color
				self.tiles.append(tile)
				index += 1
		self.ctrl_scan()

	
	def ctrl_scan(self):
		for key in self.controls:
			key.fill_color = self.key_enabled_color if key.fenabled() else self.key_disabled_color
	
		
	def ctrl_always(self):
		return True
	
	
	def ctrl_fsolvable(self):
		return (self.game.nfilled() > 15)
	
			
	def ctrl_fundo(self):
		return (len(self.undo) > 0)
	
	
	def sync_to_game(self, c = '#1e1e1e'):
		''' Write the game board to the graphical UI
		'''
		board = self.game.board
		for sq in range(81):
			v = board[sq]
			t = self.tiles[sq].children[0]
			if v != 0:
				if t.text != str(v):	# only recolor changed squares
					t.text = str(v)
					t.color = c
			else:
				t.text = ' '	

		
	def did_change_size(self):
		# TODO: rearrange display for portrait mode
		w = self.size.width
		h = self.size.height
		self.board.position = self.size/2 + ((w - h)// 2, 0)
		self.cpanel.position = ((w-h)//3 - self.gap, h//2)
		self.panel.position = (2*(w-h)//3, h//2)
		self.label.position = (w/2, 10)
		return


	def touch_began(self, touch):
		touch_loc = self.point_from_scene(touch.location)
		if touch_loc in self.board.frame:
			self.do_board_touch(touch)
		elif touch_loc in self.panel.frame:
			self.do_digits_touch(touch)
		elif touch_loc in self.cpanel.frame:
			self.do_ctrl_touch(touch)
	
	
	def do_board_touch(self, touch):
		''' If a board tile is touched, highlight it and color panel keys in the DoF
		'''
		touch_loc = self.board.point_from_scene(touch.location)
		for tile in self.tiles:
			if touch_loc in tile.frame:
				if self.selected_tile is not None:				# restore unselected color
					self.selected_tile.fill_color = self.selected_tile.ucolor
				tile.fill_color = '#fdffd9'
				self.selected_tile = tile
				# reflect DoF of selected tile in the key panel
				dof = self.game.get_sq_options(tile.index)
				for val in range(9):
					if val+1 in dof:
						self.digits[val].fill_color = self.key_enabled_color
					else:
						self.digits[val].fill_color = self.key_disabled_color
				
				# extra highlight a digit that is forced in this square
				uni = self.game.sq_has_unique(tile.index)
				if uni is not None:
					self.digits[uni-1].fill_color = '#2bd408'
				break

		
	def do_ctrl_touch(self, touch):
		''' Handle touches in the control pane
		'''
		touch_loc = self.cpanel.point_from_scene(touch.location)
		for ctrl in self.controls:
			if touch_loc in ctrl.frame:
				if ctrl.fill_color == self.key_enabled_color:
					self.label.text = ctrl.children[0].text
					ctrl.action()
				else:
					sound.play_effect('game:Crashing')


	def do_digits_touch(self, touch):
		''' Handle touches in the number pane
		'''
		touch_loc = self.panel.point_from_scene(touch.location)
		for key in self.digits:
			if touch_loc in key.frame:
				if self.selected_tile and key.fill_color != self.key_disabled_color:
					self.selected_key = key
					sq = self.selected_tile.index
					v = self.game.board[sq]
					completed = self.game.fill(sq, key.value)
					self.undo.append([(sq, v)])
					self.selected_tile.children[0].text = str(key.value)
					self.dopamine_check(completed)
				else:
					sound.play_effect('game:Crashing')


	def dopamine_check(self, completed_squares):
		''' check for completions after a digit keypress and make encouraging noises
		'''
		if len(completed_squares) > 0:
			sound.play_effect('digital:SpaceTrash3')
			for s in completed_squares:
				self.tiles[s].run_action(A.rotate_by(2*math.pi, 0.5))
		if 0 not in self.game.board:
			sound.play_effect('digital:ZapThreeToneUp')
			self.label.text = "Win! " * 3

	def touch_moved(self, touch):
		pass
	
	
	def touch_ended(self, touch):
		self.ctrl_scan()
	
	
	def do_clear(self):
		self.new_game()
	
			
	def do_preload(self):
		index = self.preload_index
		self.new_game()		# clears self.preload_index
		self.preload_index = self.game.preload(index)
		self.sync_to_game(c='#347d25')
		self.label.text = "Preload " + str(index)


	def add_undo_block(self, pre, post):
		''' Add a block of moves to the undo list given the board state before and after the moves
		'''
		undos = []
		for i in range(81):
			if pre[i] != post[i]:
				t = (i, pre[i])
				undos.append(t)
		if len(undos) > 0:
			self.undo.append(undos)
	
	
	def do_intersect(self):
		pre = self.game.board[:]
		t = 0
		n = 1
		while n > 0:
			n = self.game.intersect()
			t += n
		self.sync_to_game()
		self.add_undo_block(pre, self.game.board)
		self.label.text = "Intersect " + str(t)	
	
	
	def do_subtract(self):
		pre = self.game.board[:]
		t = 0
		n = 1
		while n > 0:
			n = self.game.subtract()
			t += n
		self.sync_to_game()
		self.add_undo_block(pre, self.game.board)
		self.label.text = "Subtract " + str(t)	
		
		
	def do_solve(self):
		testgame = Sudoku(self.game)
		pre = testgame.board[:]
		bd = testgame.solve()
		if bd is None:
			sound.play_effect('game:Crashing')
			self.label.text = "Solve Failed"
		else:
			for i in range(81):
				if bd[i] != pre[i]:
					self.game.fill(i, bd[i])
			self.sync_to_game()
			self.add_undo_block(pre, self.game.board)
			self.label.text = "Success! " + testgame.log
			print(str(pre))
			print(str(bd))
			print(self.label.text)
	
	
	def do_undo(self):
		''' undo a move or block of moves and rescync the display board
		'''
		if len(self.undo) == 0:
			sound.play_effect('game:Crashing')
			return
		
		undo_list = self.undo.pop()
		for (sq, val) in undo_list:
			if val != 0:
				self.game.fill(sq, val)
			else:
				self.game.unfill(sq)
		self.sync_to_game()




if __name__ == '__main__':
	run(MyScene(), show_fps=True, orientation=LANDSCAPE)

'''
def test():
	n = 0
	while True:
		game = Sudoku()
		n = game.preload(n)
		print("\n\nOriginal")
		game.print()
		game.solve()
		print("\nCompleted")
		game.print()
		if n == 0:
			break
	return


import timeit
g=5
def test5():
	game = Sudoku()
	game.preload(g)
	return game.solve()

print("ready")
'''




