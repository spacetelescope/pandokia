from pandokia.helpers import cases

class Mytest(cases.FunctionHolder):
    """The methods in this class would just be functions if I didn't want to
    use the tda and tra dictionaries."""

    def test1():
        do ordinary function things
        self.tda['cat']='mouse'
        assert True

   def test2(self):
       do ordinary function things
       self.tra={1:2, 3:45}
       assert 3 > 1
