import pandokia.helpers.cases
import shutil

class fits(pandokia.helpers.cases.FileTestCase) :

    # FileTestCase assumes that you created an output file and are
    # comparing to a reference file.  If the the test passes, it
    # deletes the output file.
    #
    # Because of this, we can't just have a static file to compare.
    # In this case, I wonder if the file comparator works, so 


    def test_same(self) :
        print("note: 1.fits is the same as ref.out1.fits")
        shutil.copyfile("1.fits","out1.fits")
        self.check_file("out1.fits","fits")

    def test_header(self) :
        print("note: 2.fits is the same as ref.out2.fits, but with additional header keywords")
        shutil.copyfile("2.fits","out2.fits")
        try :
            self.check_file("out2.fits","fits")
            assert AssertionError("files should have been different")
        except AssertionError, e :
            print "files different, assertion raised as expected"

