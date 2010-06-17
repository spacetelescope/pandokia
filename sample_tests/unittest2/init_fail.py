import random
import unittest2

print "this is a print statement that runs when init_fail.py is imported"

class TestSequenceFunctions(unittest2.TestCase):

    def setUp(self):
        self.seq = range(10)
        raise ValueError("This is what happens when the object creation has an exception")

    def test_shuffle(self):
        # make sure the shuffled sequence does not lose any elements
        random.shuffle(self.seq)
        self.seq.sort()
        self.assertEqual(self.seq, range(10))

        # should raise an exception for an immutable sequence
        self.assertRaises(TypeError, random.shuffle, (1,2,3))

    def test_choice(self):
        element = random.choice(self.seq)
        self.assertTrue(element in self.seq)

if __name__ == '__main__':
    unittest2.main()

