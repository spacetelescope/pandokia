import os
topmarker='pandokia_top'

def find(fname):
    """Walk up the tree until the top, collecting an ordered list of all
    files that match fname. Reverse the list before returning."""
    here=os.path.abspath('.')
    done = False
    ans=[]
    n=0
    while not done:
        flist=os.listdir(os.curdir)
        if fname in flist:
            ans.append(os.path.abspath(fname))
        if topmarker in flist:
            done=True
        os.chdir('..')
        n = n + 1
        if n > 20 :
            raise ValueError('pandokia_top not found in tree')


    #cleanup
    os.chdir(here)
    #reverse the list so it comes back top-down
    ans.reverse()
    return ans
