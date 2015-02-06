from __future__ import print_function
print("We are here!")

raise Exception("Bomb the import")

def test() :
    # does not get executed
    print("Here")
