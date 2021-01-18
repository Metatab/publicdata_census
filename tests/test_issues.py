import unittest

class TestCase(unittest.TestCase):

    def setUp(self):

        import warnings # Must turn off warnings in the test function
        warnings.simplefilter("ignore")

        super().setUp()

    def test_basic_fetch(self):
        import rowgenerators as rg

        year = 2018
        release = 5
        state = 'CA'
        sl = 'tract'
        b11016 = rg.dataframe(f'census://{year}/{release}/{state}/{sl}/B11016')

        print(b11016.head())

