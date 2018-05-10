# This is the example from the Python unittest documentation.

import random
import unittest2

# Ok, python's example doesn't do this, but you can see where this output
# shows up in the pandokia report.
print("this is a print statement that runs when example.py is imported")


class TestSequenceFunctions(unittest2.TestCase):

    def setUp(self):
        self.seq = list(range(10))

    def test_shuffle(self):
        # make sure the shuffled sequence does not lose any elements
        random.shuffle(self.seq)
        self.seq.sort()
        self.assertEqual(self.seq, list(range(10)))

        # should raise an exception for an immutable sequence
        self.assertRaises(TypeError, random.shuffle, (1, 2, 3))

    def test_choice(self):
        element = random.choice(self.seq)
        self.assertTrue(element in self.seq)

    def test_sample(self):
        # with self.assertRaises(ValueError):
        #    random.sample(self.seq, 20)
        for element in random.sample(self.seq, 5):
            self.assertTrue(element in self.seq)

if __name__ == '__main__':
    unittest2.main()
