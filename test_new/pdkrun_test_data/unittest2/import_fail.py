import random
import unittest2

This line causes a syntax error on import!

print "this is a print statement that runs when import_fail.py is imported"

class TestSequenceFunctions(unittest2.TestCase):

    def test_choice(self):
        element = random.choice(self.seq)
        self.assertTrue(element in self.seq)

if __name__ == '__main__':
    unittest2.main()

