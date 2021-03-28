# Pythonidsta Sudoku trainer GUI
# John Sadler 2019-2021
#
# Graphical version provides training hints for any selected square. 
# Green highlights in number pad are legal options for the selected square (Intersect)
# If there is a bright green highlight in the number pad, the selected square is the only one
# in its row, col, or block that can take that value (Subtract)
# Autogenerate pencil marks up to 4 options
#
# Pythonista game GUI
#
from scene import *
import sound
import ui
import time
from sudokugame import Sudoku
from sudokudb import SudokuDB
from sudokumenu import MenuScene
from dialogs import text_dialog

A = Action

def button_tapped(sender):
	key = sender.value

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
		if (w > h):
			l_tile = self.l_tile = w // 15
		else:
			l_tile = self.l_tile = h // 15
		
		gap = self.gap = l_tile//10
		l_board = (9 * l_tile) + (10 * gap)

		tile_shape = ui.Path.rounded_rect(0, 0, l_tile, l_tile, l_tile/8)
				
		# Build the board display
		board_shape = ui.Path.rounded_rect(0, 0, l_board, l_board, l_tile/6)
		self.board = ShapeNode(path=board_shape, parent=self)
		self.board.fill_color = board_color
		self.board.size = (l_board, l_board)
		
		# Build the number pad
		# panel size: 3 x 3 tiles plus spacers
		w_panel = 3*l_tile + (4*gap)
		panel_shape = ui.Path.rounded_rect(0, 0, w_panel, w_panel, l_tile/6)
		self.panel = ShapeNode(path=panel_shape, parent=self)
		self.panel.size = (w_panel, w_panel)
		self.panel.fill_color = board_color
		
		# Tile the digit keys in
		self.digits = []
		nkey = 1
		for row in range(1, -2, -1):
			for col in range(-1, 2):
				key = ShapeNode(path=tile_shape, parent=self.panel)
				key.size = (l_tile, l_tile)
				key.position = (col * (l_tile+gap), row * (l_tile+gap))
				key.fill_color = self.key_disabled_color
				key.value = nkey
				nkey += 1
				label = LabelNode(str(key.value), font=('Marker Felt', l_tile/2), parent=key)
				self.digits.append(key)

		# build the control pad
		# map button legends, actions, and gates
		labels = [
		      ("clear", self.do_clear, 		 self.ctrl_always),
				  ("load",  self.do_preload,   self.ctrl_always),
				  ("undo",  self.do_undo,      self.ctrl_fundo),
					("hint", 	self.do_hint, 		 self.ctrl_fsolvable),
					("mark",  self.do_marks,		 self.ctrl_fsolvable),
				  ("solve", self.do_solve,     self.ctrl_fsolvable),
				  ("nada",  self.do_clear,	 	 self.ctrl_never),
				  ("niente",self.do_clear,	 	 self.ctrl_never),
				  ("rien",  self.do_clear,	   self.ctrl_never),]		
		# 3 x 3 plus spacers, up to 9 control buttons
		# nrows = 3*(1+len(labels)//3)
		# h_panel = nrows * (L_tile+gap) + 2*gap
		panel_shape = ui.Path.rounded_rect(0, 0, w_panel, w_panel, l_tile/6)
		self.cpanel = ShapeNode(path=panel_shape, parent=self)
		self.cpanel.size = (w_panel, w_panel)
		self.cpanel.fill_color = board_color
		
		self.controls = []
		ntile = 0
		for row in range(1,-2,-1):
			for col in range(-1,2):
				if ntile >= len(labels):
					break			
				key = ShapeNode(path=tile_shape, parent=self.cpanel)
				key.size = (l_tile, l_tile)
				key.position = (col*(l_tile+gap), row*(l_tile+gap))
				label = LabelNode(labels[ntile][0], font=('Marker Felt', l_tile/4), parent=key)
				key.action   = labels[ntile][1]
				key.fenabled = labels[ntile][2]
				key.fill_color = self.key_disabled_color
				self.controls.append(key)
				ntile += 1
		
		# Status line display
		self.label = LabelNode('Sudoku Trainer - Sadler 2021', font=('Noteworthy', l_tile/4))
		self.label.position = (w/2, h-10)
		self.add_child(self.label)
		
		# bind the game and database
		self.game = Sudoku()
		self.db = SudokuDB()
		self.new_game()
	
			
	def new_game(self):
		self.game 					= Sudoku()
		self.selected_tile 	= None
		self.selected_key 	= None
		self.max_marks			= 0 			# state variable for pencil marks. 0 for off
		even_color 					= '#ffd2a1'
		odd_color 					= '#ffae55'
		l_tile 							= self.l_tile
		gap 								= self.gap
		self.undo = []		# each undo event is a list of (square, value) tuples

		# This flag tells the solver to save games when it solves. Set when the board is empty, cleared on Load or Solve
		self.save_on_solve 	= True
		self.game_title 		= None
				
		# insert tiles onto board in order from top left to bottom right, row major order
		# so that the order they appear in <tiles> matches the convention in class <Sudoku>
		self.tiles 					= []
		index 							= 0
		tile_shape 					= ui.Path.rounded_rect(0, 0, l_tile, l_tile, l_tile/8)
		
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
				marks = LabelNode(" ", font=('Noteworthy', l_tile/6), parent=tile, position=(0,l_tile/3))
				marks.color = '#141c6d'
				self.tiles.append(tile)
				index += 1
		self.ctrl_scan()
		self.did_change_size()


	def did_change_size(self):
		''' reposition board, digit panel and cpanel in response to orientation shifts '''
		# note origin appears to be at bottom left corner
		w = self.size.width
		h = self.size.height
		wboard = self.board.size[0]
		wpanel = self.panel.size[0]

		if w > h:		# landscape: board to the right, panels stacked on the left
			self.board.position  = self.size/2 + ((w-h)//2, 0)
			panelx = (w-h)//2
			self.cpanel.position = (panelx, (self.size.height + wpanel)//2 -self.l_tile - self.gap)
			self.panel.position  = (panelx, (self.size.height - wpanel-3*self.l_tile-self.gap)//2)
			self.label.position  = (w/2, h-10)
		else:  			# portrait
			self.board.position  = self.size/2 + (0, (h - w)// 2)
			panely = (h-w)//2
			self.panel.position  = ((w-wpanel-self.l_tile)//2, panely)
			self.cpanel.position = ((w+wpanel+self.l_tile)//2, panely)
			self.label.position  = (w/2, (h-w)-12)
			
		return


	def ctrl_scan(self):
		for key in self.controls:
			key.fill_color = self.key_enabled_color if key.fenabled() else self.key_disabled_color
		
	def ctrl_always(self):
		return True
		
	def ctrl_never(self):
		return False
	
	def ctrl_fsolvable(self):
		return (self.game.nfilled() > 17)
			
	def ctrl_fundo(self):
		return (len(self.undo) > 0)
	
	
	def sync_to_game(self, c = '#1e1e1e'):
		''' Write the game board to the graphical UI
		Factor to support load, solve, undo, intersect, subtract
		'''
		board = self.game.board
		for sq in range(81):
			v = board[sq]
			t = self.tiles[sq].children[0]
			m = self.tiles[sq].children[1]
			# refresh label in filled squares
			if v != 0:
				m.text=" "
				if t.text != str(v):	# only recolor changed squares
					t.text = str(v)
					t.color = c
			else:
				# Update marks in empty squares with DoF at or below max_marks
				t.text = ' '
				opts = self.game.get_sq_options(sq)
				if self.max_marks > 0:
					if (len(opts) <= self.max_marks):
						m.text = str(sorted(opts)).replace(',',' ').strip("[ ]")
				else:
					m.text = " "
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
					sound.play_effect('ui:click3')
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
					self.sync_to_game()
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
		else:
			sound.play_effect('ui:click3')
		if 0 not in self.game.board:
			sound.play_effect('voice:female_congratulations')
			self.label.text = "Win! " * 3

	def touch_moved(self, touch):
		pass
	
	
	def touch_ended(self, touch):
		self.ctrl_scan()
	
	
	def do_clear(self):
		self.new_game()


	def do_preload(self):
		self.menu = MenuScene('Load Game', 'Level', self.game.levels)
		self.present_modal_scene(self.menu)
		return
		
	# Support for preload(): modal menu to select game level
	def menu_button_selected(self, title):
		self.new_game()
		#map difficulty to int level range
		idx = self.game.levels.index(title)
		game_trd = self.db.load(self.game.level_limits[idx], self.game.level_limits[idx+1])
		if game_trd is None:
			self.label.text = "No games at level " + title
			return
		# convert the returned game to a list of integers 
		sgame = game_trd[0]
		board = list(map(int,sgame))

		# load and sync the game
		self.game.preload(board)
		self.sync_to_game(c='#347d25')
		
		# Set status string to game title if there is one
		desc = game_trd[3]
		if game_trd[1] is not None:
			desc = game_trd[1]
			self.game_title = desc
		self.label.text = "Game: " + desc
		
		self.save_on_solve = False
		self.dismiss_modal_scene()
		self.ctrl_scan()
		return


	def add_undo_block(self, pre, post):
		''' Add a block of moves to the undo list given the board state before and after the moves
		Factor to support load, solve, undo, intersect, subtract
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
	
	def do_marks(self):
		''' GUI support: toggle pencil marks in open tiles with 1-3 DoF '''
		self.max_marks = (self.max_marks + 1) % 5
		self.sync_to_game()
		self.label.text = "{} {}".format(self.label.text, self.max_marks)
		return
		
			
	def do_hint(self):
		''' GUI support: give a hint if possible '''
		hint = None
		hinttext = "No open squares"
		# find the open square with the fewest degrees of freedom
		openlist = self.game.get_opens_by_dof()
		
		if len(openlist) > 0:
			sq = openlist[0]
			dof = self.game.get_sq_options(sq)
			#
			# Default: if no forced square, then it's time for a guess
			hint = sq
			hinttext = "Take a Guess - square " + str(sq)
			#
			# if only one Dof, highlight
			if len(dof) == 1:
				hint = sq
				hinttext = "One value in square " + str(sq)
			else:
				#
				# find a forced value square and hint it instead
				for sq in openlist:
					uni = self.game.sq_has_unique(sq)
					if uni is not None:
						hint = sq
						hinttext = "Forced value in square " + str(sq)
						break
			#
			# Now animate the hinted square
			def wink(node, progress):
				node.fill_color = '#71d75c'
			
			def unwink(node, progress):
				node.fill_color = node.ucolor
					
			tile = self.tiles[sq]
			tile.run_action(A.sequence(A.call(wink, 0.01), A.rotate_by(2*math.pi, 0.5), A.call(unwink, 0.01)))
			
		self.label.text = hinttext
		return
		

	def do_solve(self):
		testgame = Sudoku(self.game)
		strgame = str(testgame).replace(',','')
		
		pre = testgame.board[:]
		if not testgame.hsolve():
			sound.play_effect('game:Crashing')
			self.label.text = "Solve Failed"
		else:
			strsoln = str(testgame).replace(',','')

			# Prompt or default title for new db entry, always update rating and rating string
			if self.save_on_solve:
				savtitle = self.game_title if self.game_title is not None else time.ctime()
				title = text_dialog("Title this game", savtitle)
				if title is None:
					title = savtitle
				self.db.save(strgame, strsoln, testgame.log, title)
				self.save_on_solve = False
				self.label.text = "Success! " + testgame.log + "[Saved]"
			else:
				self.db.annotate(strgame, testgame.log, None)
				self.label.text = "Success! " + testgame.log
					
			bd = testgame.board[:]
			for i in range(81):
				if bd[i] != pre[i]:
					self.game.fill(i, bd[i])
			self.sync_to_game()
			self.add_undo_block(pre, self.game.board)
	
	
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


