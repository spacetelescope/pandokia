import etc_utils.helpers.filecomp as filecomp


def test_1():
    filecomp.check_file(
        'diff/i1.txt',
        'diff',
        'diff/o1.txt',
        quiet=False,
        raise_exception=True)
