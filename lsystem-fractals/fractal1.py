import matplotlib.pyplot as plt
import math
import json
import random

# L-system fractal drawing using a custom turtle
# Reference for l-system fractals: http://paulbourke.net/fractals/lsys/

def plotcoords(coords):
	x, y = zip(coords)
	plt.cla()
	plt.plot(x, y)

# fracturtle - drive pyplot using a saved state. 
# Turtle state is position (x,y) and heading
# Push and pop state
# 
class EZTurtle(object):
	
	def __init__(self, angle = math.pi/2.0, dist = 1.0):
		self.ang = angle
		self.dist = dist
		self.clear()
	
	def clear(self):
		self.x_list = []
		self.y_list = []
		self.states = []
		self.x = 0.0
		self.y = 0.0
		self.a = 0.0
		self._plot()
		
	def _plot(self):
		''' Add a coord pair to the move list '''
		self.x_list.append(self.x)
		self.y_list.append(self.y)
				
	def move(self):
		self.x_list.append(math.nan)
		self.y_list.append(math.nan)		
		self.draw()
	
	def draw(self):
		self.x += math.cos(self.a) * self.dist
		self.y += math.sin(self.a) * self.dist
		self._plot()

	def cw(self):
		self.a -= self.ang
		
	def ccw(self):
		self.a += self.ang

	def six(self):
		self.a += math.pi
	
	def push(self):
		assert(len(self.states) < 1000)
		self.states.append( (self.x, self.y, self.a, self.dist, self.ang) )
		
	def pop(self):
		assert(len(self.states) > 0)
		(self.x, self.y, self.a, self.dist, self.ang) = self.states.pop()
		self.x_list.append(math.nan)
		self.y_list.append(math.nan)
		self._plot()
			
	def noop(self):
		pass
		
	def walk_lsystem(self, lsys, ang=None, color='black'):
		ops = {'F' : self.draw, 
		       'f' : self.move, 
		       '+': self.cw, 
		       '-' : self.ccw, 
		       '[' : self.push, 
		       ']' : self.pop,
		       '|' : self.six}

		if ang is not None:
			self.ang = ang
		
		for c in lsys:
			ops.get(c, self.noop)()

		plt.clf()
		plt.plot(self.x_list, self.y_list, color=color)
		plt.axes().set_aspect('equal')
		plt.axis('off')
		plt.show()

def apply_lsystem(axiom, rules):
	''' Apply the rules to the axiom for n iterations and return the resulting string '''
	return ''.join(rules.get(c, c) for c in axiom)

def iterate_lsystem(axiom, rules, n):
	for _ in range(n):
		axiom = apply_lsystem(axiom, rules)
		if len(axiom) > 100000:
			break
	return axiom

# spec for a fractal: angle = 2pi/slices, axiom, rules, growth factor
def drawfractal(spec, n=0):
	angle = 2.0 *math.pi / spec.get('slices', 4.0)
	grow = spec.get('grow', 1.0)
	length = spec.get('length', 1.0) / (grow ** max(n-1, 0))
	axiom = spec['axiom']
	rules = spec['rules']
	color = spec.get('color', 'blue')
	
	t = EZTurtle(angle, length)
	l = iterate_lsystem(axiom, rules, n)
	t.walk_lsystem(l, angle, color)
	(xl, xh) = plt.gca().get_xlim()
	(yl, yh) = plt.gca().get_ylim()
	print('range: ', max(xh-xl, yh-yl), 'len: ', len(l))
	print('axiom: ', axiom, ' rules: ', rules)

def test(lsys, slices = 5):
	angle = 2.0 * math.pi / slices
	length = 1.0
	t = EZTurtle(angle, length)
	t.walk_lsystem(lsys, angle)		


crystal = {'slices': 4.0,
           'grow'  : 3.0,
           'axiom' : 'F+F+F+F',
           'rules' : {'F': 'FF+F++F+F'}}

hilbert = {'slices': 4.0,
           'grow'  : 2.0,
           'axiom' : 'L',
           'rules' : {'L' : '+RF-LFL-FR+', 'R' : '-LF+RFR+FL-'}}

peagos  = {'slices': 6.0,
           'grow'  : 3.0,
           'axiom' : 'X',
           'rules' : {'X' : 'X+YF++YF-FX--FXFX-YF+', 'Y' : '-FX+YFYF++YF+FX--FX-Y'}}

dragon  = {'slices': 4.0,
           'grow'  : 1.5,
           'axiom' : 'X',
           'rules' : {'X' : 'X+YF+', 'Y' : '-FX-Y'}}

peano   = {'slices': 4.0,
           'grow'  : 2.0,
           'axiom' : 'F',
           'rules' : {'F' : 'F+F-F-F-F+F+F+F-F'}}

qkoch   = {'slices': 4.0,
           'grow'  : 2.0,
           'axiom' : 'F+F+F+F',
           'rules' : {'F' : 'F-F+F+FFF-F-F+F'}}

baroque = {'slices': 6.0,
           'grow'  : 2.0,
           'axiom' : 'F++F++F++',
           'rules' : {'F' : 'F+F--F+F'}}

sierp3  = {'slices': 6.0,
           'grow'  : 2.0,
           'axiom' : 'XF',
           'rules' : {'X' : 'YF+XF+Y', 'Y': 'XF-YF-X'}}

sierp4  = {'slices': 4.0,
           'grow'  : 2.0,
           'axiom' : 'F+XF+F+XF',
           'rules' : {'X' : 'XF-F+F-XF+F+XF-F+F-X'}}

jstest  = {'slices': 6.0,
           'grow'  : 2.0,
           'axiom' : 'F+F+F+F+F+F',
           'rules' : {'F' : 'F-F+F+'}}

tree1   = {'slices': 18.0, 
		   'grow'  : 1.5,
		   'color' : 'forestgreen',
		   'axiom' : 'X', 
		   'rules' : {'X':'F-[[X]+X]+F[+FX]-X', 'F':'FF'} }

tree2   = {'slices': 16.0, 
		   'grow'  : 2.0,
		   'color' : 'forestgreen',
		   'axiom' : 'F', 
		   'rules' : {'F':'FF+[+F-F-F]-[-F+F+F]'} }

snoflak5 = {'slices': 5.0, 
		   'grow'  : 1.25, 
		   'axiom' : 'F-F-F-F-F', 
		   'rules' : {'F':'F-F++F+F-F-F'} }

snoflak6 = {'slices': 6.0, 
		   'grow'  : 1.25, 
		   'axiom' : 'F++F++F', 
		   'rules' : {'F':'F-F++F-F'} }

penta   = {'slices': 10.0, 
		   'grow'  : 2.0, 
		   'color' : 'black',
		   'axiom' : 'F++F++F++F++F', 
		   'rules' : {'F':'F++F++F|F-F++F'} }

gosper6	= {'slices': 6.0, 
		   'grow'  : 2.0, 
		   'color' : 'black',
		   'axiom' : 'XF', 
		   'rules' : {'X':'X+YF++YF-FX--FXFX-YF+', 'Y':'-FX+YFYF++YF+FX--FX-Y'} }

hexa 	= {'slices': 12.0, 
		   'grow'  : 2.5, 
		   'color' : 'black',
		   'axiom' : 'F++F++F++F++F++F', 
		   'rules' : {'F':'F++F++F[++F[B]]|FF++F[C]', 'B':'++F++F', 'C':'B'} }

hexa2	= {'slices': 12.0, 
		   'grow'  : 2.0, 
		   'color' : 'maroon',
		   'axiom' : 'F', 
		   'rules' : {'F':'[-F+F+F][F[-F]+F]+F-F-F+'} }

hexa3	= {'slices': 12.0, 
		   'grow'  : 2.5, 
		   'color' : 'black',
		   'axiom' : 'F++F++F++F++F++F++', 
		   'rules' : {'F':'F[--F++F++F][++F--F--f]ffF'} }

examples = {'crystal':crystal, 
			'hilbert':hilbert, 
			'peano-gosper' :peagos, 
			'gosper6' : gosper6,
			'dragon' :dragon, 
			'peano'  :peano, 
			'quadkoch'  :qkoch, 
			'baroque':baroque, 
			'sierpinski3' :sierp3, 
			'sierpinski4' :sierp4,
			'tree1'  :tree1,
			'tree2'  :tree2,
			'snowflake5':snoflak5,
			'snowflake6':snoflak6,
			'penta' : penta,
			'hexa' : hexa}

def save():
	f = open('savedfractals', 'w')
	json.dump(examples, f)
	f.close()

drawfractal(hexa2, 2)


