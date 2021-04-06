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

    def test_2020_blocks(self):

        from publicdata.census.files.url_templates import tiger_url

        self.assertEqual('shape+ftp://ftp2.census.gov/geo/tiger/TIGER2019/TABBLOCK/tl_2019_44_tabblock10.zip',
                         tiger_url(2019, 'block', 'RI'))
        self.assertEqual('shape+ftp://ftp2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_44_tabblock20.zip',
                         tiger_url(2020, 'block', 'RI'))

    def test_shell_not_linear_ring(self):

        import rowgenerators as rg

        t = rg.geoframe('censusgeo://2019/5/CA/tract')

        print(len(t))


