#
# SudokuDB - is reponsible for persistent storage, searching, and retrieving games based on difficulty or description
#
import sqlite3
import random
import time

# starter database of games
dbseed = [('007030296000180004095620038012000070570040900830001002640002007350014600001090805', '187435296263189754495627138912568473576243981834971562649852317358714629721396845', 'i43 ', 4, 'Easy 1'),
('200080700905017043600003002008360004100000007300072800500100009490520308002040005', '243685791985217643617493582728361954169854237354972816576138429491526378832749165', 'i47 ', 4, 'Easy 2'),
('280004019090700352000010400030047000000080000000006090503672040060091000400005600', '286354719194768352357219486938147265625983174741526893513672948862491537479835621', 'i20 s31 ', 8, 'Moderate 1'),
('208001360509003100000000009003000012100020800090000007400070003600308040000000605', '278951364549263178316847529763584912154729836892136457481675293625398741937412685', 'i09 s45 ', 8, 'Moderate 2'),
('050100206700090000003000400020300760000205000094600820308000040000504000000000100', '459173286786492351213856479821349765637285914594617823368921547172534698945768132', 'i01 s55 ', 8, 'Moderate 3'),
('010009700025006000000020080400000806900000020800307000090000040007910000060005000', '318459762725186394649723185471592836936841527852367419593678241287914653164235978', 'i01 s57 ', 8, 'Moderate - Will Shortz - 38'),
('300005124890010000000200000700080950040063800000050010500070080000000500003000007', '367895124892714635451236798716482953945163872238957416524671389679328541183549267', 'i03 s09 _r_ s43 ', 16, 'Demanding - Will Shortz P49'),
('600090800090000010300650000004000050000000069082400000406010000000300700100002005', '651297834297834516348651927964173258713528469582469173476915382825346791139782645', 's11 _r_ i13 s33 ', 16, 'Demanding - Will Shortz - 70'),
('080005030000403009002000007007080020030000040010070600500000900400506000020900010', '984765132176423859352891467647189325839652741215374698561237984498516273723948516', 's05 _r_ i04 s47 ', 16, 'Hard - The Week - 26 Mar 2021'),
('800100540000200070075004090000910000009807052007005010100030027000792000000000000', '862179543941253876375684291253916784619847352487325619196538427534792168728461935', 's22 _r_ s03 _r_ i27 ', 20, 'Harder 1'),
('800170540000200070075004090000910000009807052007005010100030027000792000000000000', '862179543941253876375684291253916784619847352487325619196538427534792168728461935', 's21 _r_ s03 _r_ i27 ', 20, 'Harder 2'),
('005900070000000080000003009007040000001006000623000005302000407004008090000010600', '245981376936527184718463259857342961491856723623179845382695417164738592579214638', 's14 _r_ s03 _r_ s39 ', 20, 'Very Hard 1'),
('030000405000000000007000010000790500006050800200040073000920007040300900000106000', '132867495964512738857439216481793562376251849295648173513924687648375921729186354', 'i01 s05 _r_ i03 s48 ', 20, 'Ultimate Challenge - Will Shortz - 100'),
('000000089007300050080054000000700002006080700500009000000210060040005200230000000', '425671389967328154183954627814736592396582741572149836759213468641895273238467915', 's09 _r_ i01 s09 _r_ s37 ', 24, 'Very Hard 2'),
('040701003130000040800000950080302005000080000900506030071000009090000024300408070', '249751863135869742867243951786312495523984617914576238471625389698137524352498176', 's17 _r_ i13 s01 _r_ i19 ', 24, 'Super Hard - The Week - 19 Mar 2021'),
('090000005007830000008006003000567010000100000950000300040000092000008600000910000', '396421785527839164418756923834567219762193548951284376143675892279348651685912437', 's17 _r_ i03 s01 _r_ s03 _r_ i31 ', 32, 'Ultimate Challenge - Will Shortz - 99'),
('050730004008200000104008000503000002000000000082000070020065013010070000630100027', '256731894398246751174958236563897142741523689982614375827465913419372568635189427', 's16 _r_ i02 s02 _r_ i01 s01 _r_ i05 s01 _r_ i22 ', 48, 'Wicked hard 1'),
('800000000003600000070090200050007000000045700000100300001000068008500010090000400', '819253647243671895576498231354987126162345789987126354421739568738564912695812473', 'i02 _r_ i03 _r_ _r_ i06 _r_ s01 _r_ s04 _r_ i38 ', 48, 'Daily Telegraph World\'s Hardest Sudoku'),
('040701003130000040800000950080300005000080000000506030071000009090000024300408070', '945721863136859247827634951784312695563987412219546738471263589698175324352498176', 's16 _r_ i02 s02 _r_ i12 s03 _r_ i02 s03 _r_ i06 _r_ i03 ', 56, 'Wicked hard 2'),]



class SudokuDB():
	def __init__(self):
		random.seed()
		self.this_game = "" # state variable for load()
		self.con = sqlite3.connect('sudoku.db')
		cur = self.con.cursor()
		
		# check existence of games table - if it doesn't exist, create it and prefill
		rownames = []
		for row in cur.execute("PRAGMA table_info(games)"):
			rownames.append(row[1])
		
		if rownames == []:
			print("Creating games table")
			cur.execute("CREATE TABLE IF NOT EXISTS games(game text UNIQUE, soln text, desc text, rating int, title text)")
			for row in dbseed:
				cur.execute("INSERT INTO games VALUES(?,?,?,?,?)", row)	
		elif 'title' not in rownames:
			print("updating games table to add title")
			cur.execute("ALTER TABLE games ADD COLUMN title text")
		
		self.con.commit()
		return
	
		
	def save(self, game, soln, desc, title=None):
		''' insert or replace a saved game as appropriate '''
		rating = len(desc)
		cur = self.con.cursor()
		if title is None:
			title = time.ctime()
		
		# If not unique, update 
		cur.execute("SELECT title,desc,rating FROM games WHERE game=?", (game,))
		rec = cur.fetchone()
		if rec is None:	
			cur.execute("INSERT INTO games VALUES(?,?,?,?,?)", (game, soln, desc, rating, title))
		else:
			title = rec[0] # if there's already a title, reuse it
			cur.execute("UPDATE games SET soln=?, desc=?, rating=?, title=? WHERE game=?", (soln, desc, rating, title, game))
		self.con.commit()
	
		
	def list(self):
		''' Print dump the rows by difficulty level '''
		cur = self.con.cursor()
		print("\n\nList O' Games")
		for row in cur.execute("SELECT rating,title FROM games ORDER BY rating"):
			print(row)
		return
	
	
	def dump(self):
		''' print games and titles in a form Python can parse'''
		cur = self.con.cursor()
		print("(game, title)")
		for row in cur.execute("SELECT game,soln,desc,rating,title FROM games ORDER BY rating"):
			game = str(row[0]).replace(',','') # remove commas
			soln = str(row[1]).replace(',','') # remove commas
			print("('{}', '{}', '{}', {}, '{}'),".format(game, soln, row[2], row[3], row[4]))
		
		
	def annotate(self, game, rating, title=None):
		''' change the rating and (optionally) title fields for a given game '''
		cur = self.con.cursor()
		rint = len(rating)
		cur.execute("UPDATE games SET desc=?,rating=? WHERE game=?", (rating, rint, game))
		if title is not None:
			cur.execute("UPDATE games SET title=? WHERE game=?", (title, game))
		self.con.commit()


	def get_table_info(self):
		cols = []
		cur = self.con.cursor()
		for row in cur.execute("PRAGMA table_info(games)"):
			cols.append(row)
		return cols

			
	# load a game given a difficulty level range. 
	# If more than one game meets the criteria, choose one at random
	# Returns a tuple containing rating int, title text, game text, desc text	
	# otherwise returns None
	def load(self, minrating, maxrating=None):
		if maxrating is None:
			maxrating = minrating
		
		cur = self.con.cursor()
		cur.execute("SELECT game,title,rating,desc FROM games WHERE rating BETWEEN ? AND ? LIMIT 100", (minrating, maxrating))
		l = cur.fetchall()
		if len(l) == 0:
			return None
		game = random.choice(l)
		# try to avoid sending the same game back twice in a row (if there is more than one in the rating class)
		if game == self.this_game:
			game = random.choice(l)
		self.this_game = game
		return game


	def get_all(self, maxrows=100):
		''' return a list of all the games in the DB '''
		cur = self.con.cursor()
		cur.execute("SELECT game,title,rating,desc FROM games ORDER BY rating LIMIT ?", (maxrows,))
		result = cur.fetchall()
		return result
	
		
	def count(self):
		cur = self.con.cursor()
		cur.execute("SELECT COUNT(game) FROM games")
		l = cur.fetchone()
		return l[0]


if __name__ == '__main__':
	db = SudokuDB()
	db.list()
	print(f"{db.count()} games")
	
