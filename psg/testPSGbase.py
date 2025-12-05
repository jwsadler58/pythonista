import unittest
from PSGbase import *

class noteTests(unittest.TestCase):

	def testValidKey(self):
		self.assertEqual(validKey("C"), "C")
		self.assertEqual(validKey("f"), "F")
		self.assertEqual(validKey("f#"), "F#")		
		self.assertEqual(validKey("gb"), "Gb")
		with self.assertRaises(ValueError):
			validKey("qflat")
		with self.assertRaises(ValueError):
			validKey("FB")
		return
	
				
	def testDegreeToNote(self):
		self.assertEqual(degreeToNote(0),"C")
		self.assertEqual(degreeToNote(1),"C#")
		self.assertEqual(degreeToNote(12),"C")
		# flat key
		self.assertEqual(degreeToNote(0,"F"),"F")
		self.assertEqual(degreeToNote(11,"F"),"E")
		self.assertEqual(degreeToNote(10,"F"),"Eb")
		# sharp key
		self.assertEqual(degreeToNote(11,"G"),"F#")
		return
	
	
	def testNoteToDegree(self):
		self.assertEqual(noteToDegree("C"), 0)
		self.assertEqual(noteToDegree("C", "G"), 5)
		self.assertEqual(noteToDegree("B", "B"), 0)
		self.assertEqual(noteToDegree("C", "B"), 1)
		self.assertEqual(noteToDegree("C#", "B"), 2)
		self.assertEqual(noteToDegree("A#", "B"), 11)
		self.assertEqual(noteToDegree("C", "Cb"), 1)
		return
		
		
	def testNoteClass(self):
		n = Note()
		self.assertEqual(n.getName(), "C")
		self.assertEqual(n.getDegreeName(),"1")
		
		n= Note(0,"C")
		self.assertEqual(n.getDegreeName(),"1")
		return
	

	def testNoteFromName(self):
		n = Note.fromName("D","E")
		self.assertEqual(n.getDegreeName(), "b7")
		n.setTranspose(-3)
		self.assertEqual(n.getDegreeName(), "b7", "transpose should not change degree name")
		
		n = Note.fromName("F","Bb")
		self.assertEqual(n.getDegreeName(), "5")
	
		n = Note.fromName("F#","C")
		self.assertEqual(n.getDegreeName(), "-5")
		n = Note.fromName("Gb","C")
		self.assertEqual(n.getDegreeName(), "-5")
		
		n = Note.fromName("B","C")
		self.assertEqual(n.getDegreeName(), "7")
		self.assertEqual(n.getName(),"B")
		n.setTranspose(3)
		self.assertEqual(n.getName(),"D")
		n.setTranspose(-3)
		self.assertEqual(n.getName(),"G#")
		return
	
	
	def testNoteFromDegree(self):
		def run(deg, key, name):
			n = Note.fromDegreeName(deg, key)
			self.assertEqual(n.getDegreeName(), deg)
			self.assertEqual(n.getName(), name)
		
		run("1","E","E")
		run("b7", "E", "D")
		run("3","E","G#")
		run("4","C","F")
		run("7","A","G#")
		run("-5","A","D#")
		run("2","F","G")
		run("b3","F","Ab")
		run("3","F","A")
		run("4","F","Bb")
		return

				
if __name__ == '__main__':
	unittest.main()
