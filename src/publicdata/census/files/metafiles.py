# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

import pandas as pd
from functools import cached_property
from publicdata.census.dimensions import race_iterations
from publicdata.census.files.text_filter import universe_flags, ri_code_map,  ri_titles_p, age_patterns

"""Classes to acess metadata files"""
from publicdata.census.files.url_templates import (
    table_lookup_url,
    table_shell_url,
    api_var_url
)
from rowgenerators import parse_app_url


class Table(object):
    """Represents a  Census Table"""

    csv_header = 'id seq start title universe subject'.split()

    def __init__(self, table_id, title, universe=None, seq=None, fileid=None,
                 startpos=None, subject=None, row=None):
        self.unique_id = table_id
        self.title = title
        self.universe = universe
        self.releases = set()

        self.number_of_segments = 1  # > 1 for multi-segment tables, like b24010 or b24121

        self.seq = seq
        self.fileid = fileid
        self.startpos = startpos
        self.subject = subject

        self.fractionals = {}

        self.source_row = row  # Row from the source data

        self.columns = {}

    @property
    def row(self):
        return [
            self.unique_id,
            self.seq,
            self.startpos,
            self.title,
            self.universe,
            self.subject,

        ]

    @property
    def dict(self):
        from publicdata.census.codes import describe_table

        codes = describe_table(self.unique_id)

        d = {
            'table_id': self.unique_id,
            'seq': self.seq,
            'n_seg': self.number_of_segments,
            'start_pos': self.startpos,
            'title': self.title,
            'bare_title': self.bare_title,
            'technical': codes.technical,
            'universe': self.universe,
            'subject': self.subject,
            'age': self.age,
            'age_range': self.age_range,
            'sex': self.sex,
            'race': self.race,
        }

        d.update(universe_flags(self.universe))

        d['units'] = self.units

        return d



    @property
    def sex(self):
        return Column.extract_sex(self.universe)

    @property
    def race(self):
        """Return a race code from the table id"""

        race = ri_code_map.get(self.unique_id[-1].lower())
        if not race:
            race = Column.extract_raceeth(self.universe)

        return race

    @property
    def age(self):
        return Column.format_age(self.age_range)

    @property
    def age_range(self):
        return Column.extract_age(self.universe)

    @property
    def bare_title(self):
        import re
        from .text_filter import strip_phrases

        # Strip out races from the title
        t = re.sub(r'\s+', ' ', re.sub(ri_titles_p, '', self.title)).strip()

        # Strip the title even more

        for phrase in strip_phrases:
            t = re.sub(phrase, '', t, flags=re.IGNORECASE)

        t = t.replace('By Nativity', 'Nativity')

        if not t:
            d = {
                'people': 'Population',
                'housing': 'Housing Units',
                'dollars': 'Dollars',
            }



            t = d[self.units]

        import re
        def clean_title(v):
            v = re.sub(r'\s+', ' ', v)
            v = re.sub(r'By .*', '', v)
            v = re.sub(r'-- .*', '', v)
            v = re.sub(r'For .*', '', v)
            v = re.sub(r'In .*', '', v)
            return v.strip()

        t = clean_title(t)

        t = t.replace('And Types Of Internet', 'And Type Of Internet')
        t = t.replace('Median Sex', 'Sex').strip()


        return t

    @property
    def units(self):
        """Return the units of the table, from the universe"""

        u = self.universe.lower()

        if 'dollars' in u or 'dollars' in self.title.lower():
            return 'dollars'
        elif 'housing' in u:
            return 'housing'
        else:
            return 'people'


    def _repr_html_(self, **kwargs):
        column_rows = ''
        for col_pos in sorted(self.columns):
            c = self.columns[col_pos]
            sd = c.short_description or ''
            column_rows += f"<tr><td>{c.col_no}</td><td>{c.unique_id}</td>" + \
                           f"<td>{sd}</td><td>{c.name}</td></tr>\n"

        return f"""
        <h1>Census Table {self.unique_id}</h1>
        <i>{self.title}</i>
        <p>Universe: {self.universe}, Subject {self.subject}</p>
        <p>Seq {self.seq}, Start {self.startpos}<p>
        <table>
        <tr><th>#</th><th>Name</th><th>Short Description</th><th>Description</th></tr>
        {column_rows}
        </table>
        """


class Column(object):
    """Represents a column in a Census Table"""
    csv_header = 'tableid id colno desc short_desc'.split()

    def __init__(self, table, table_id, col_id, col_no,
                 name=None, short_desc=None, path=None,
                 seq_file_col_no=None, parent=None, row=None):
        self.table = table
        self.table_id = table_id
        self.unique_id = col_id
        self.name = name.strip(':') if name else None
        self.short_description = short_desc or name

        self.path = path

        self.col_no = col_no
        self.seq_file_col_no = seq_file_col_no

        self.parent = parent  # Name of Parent column

        self.source_row = row  # Row from the source data

    @property
    def row(self):
        return [
            self.table_id,
            self.unique_id,
            self.col_no,
            self.seq_file_col_no,
            self.name,
            self.short_description,
            self.path,
        ]

    @classmethod
    def extract_sex(cls, v):
        """Extract sex from the universe"""

        v = v.lower()

        if 'female' in v or 'women' in v:
            return 'female'
        elif 'male' in v or 'men' in v:
            return 'male'
        else:
            return 'all'

    @property
    def sex(self):
        if '/male' in self.path:
            return 'male'
        elif '/female' in self.path:
            return 'female'
        else:
            return 'all'

    @classmethod
    def extract_raceeth(cls, v):

        v = v.lower()

        # Special case for a specific table, C02003
        if 'two or more races' in v:
            return 'many'

        for code, race, term in race_iterations:
            if term.lower() in v.lower():
                return race

        # Maybe there is more race information in the table title, but
        # it isn't an iteration, like:
        # b02015: Asian Alone By Selected Groups

        for code, race, term in race_iterations:
            if term.lower() in v.lower():
                return race

        return 'all'

    @property
    def raceeth(self):

        # More reliable to get it from the race iteration code
        race_from_table = ri_code_map.get(self.table_id[-1].lower())

        if race_from_table and race_from_table != 'all':
            return race_from_table

        return self.extract_raceeth(self.path)

    @classmethod
    def extract_age(cls, v):

        v = v.lower()

        if v and 'year' in v:

            # Ignore:
            # "Grandparents living with own grandchildren under 18 years"
            if 'grandp' in v.lower() or 'grandc' in v.lower():
                return None

            # We do need to process these, but not the part about children under 18
            # Presence Of Own Children Under 18 Years By Age Of Own Children Under 18 Years By Employment Status For Females 20 To 64 Years
            if 'own children' in v:
                v = v.replace('own children under 18 years', '')

            v = v.replace('1 year ago', '').replace('year-round', '')

            m = age_patterns['to'].search(v)
            if m:
                return (int(m.group('lower')), int(m.group('upper')))

            m = age_patterns['and'].search(v)
            if m:
                return (int(m.group('lower')), int(m.group('upper')))

            m = age_patterns['under'].search(v)
            if m:
                return (0, int(m.group('upper')))

            m = age_patterns['over'].search(v)
            if m:
                return (int(m.group('lower')), 120)

            m = age_patterns['single'].search(v)
            if m:
                return (int(m.group('upperlower')), int(m.group('upperlower')))

        return None

    @property
    def age_range(self):
        """Parse the description for an age range"""

        return self.extract_age(self.path)

    @classmethod
    def format_age(cls, age_range):
        if age_range:
            return "{:03d}-{:03d}".format(*age_range)
        else:
            return 'all'

    @property
    def age(self):
        return self.format_age(self.age_range)

    @property
    def min_age(self):
        ar = self.age_range
        if ar:
            return ar[0]
        else:
            return 0

    @property
    def max_age(self):
        ar = self.age_range
        if ar:
            return ar[1]
        else:
            return 120

    @classmethod
    def extract_poverty(cls, v):
        pov_map = {
            'under 1.00': 'lt100',
            'below 100 percent of the poverty level': 'lt100',
            'below poverty level': 'lt100',
            'below the poverty level': 'lt100',
            'above poverty level': 'gt100',
            'above the poverty level': 'gt100',
            '100 to 149 percent of the poverty level': '100-150',
            'at or above 150 percent of the poverty level': 'gt150',
            '1.00 to 1.99': '100-200',
            '2.0  and over': 'gt200',
            '2.00 to 3.99 of poverty threshold': '200-400',
            '1.00 to 1.37 of poverty threshold': '100-137'
        }

        for term, code in pov_map.items():
            if term in v:
                return code

        return 'all'

    @property
    def poverty_status(self):
        return self.extract_poverty(self.path)

    @staticmethod
    def remove_path_elem(e):
        """Remove elements from the path that are not useful for analysis"""
        from .text_filter import path_filter

        removes = ['total', 'years', 'male', 'female', 'tallied']

        removes.extend(e[0] for e in path_filter)

        for r in removes:
            if r in e:
                return True

        return False

    @property
    def filtered_path(self):
        return '/'.join([e for e in self.path.split('/') if not Column.remove_path_elem(e)])

    def path_flags(self):
        from .text_filter import path_filter

        flags = {}
        for e, var, val in path_filter:
            flags[var] = None

        for p in self.path.split('/'):
            for e, var, val in path_filter:
                if e.lower() == p.lower():
                    flags[var] = val

        return flags

    @property
    def dict(self):
        d = {
            'sex': self.sex,
            'race': self.raceeth,
            'age': self.age,
            'age_range': self.age_range,
            'min_age': self.min_age,
            'max_age': self.max_age,
            'poverty_status': self.poverty_status,
            'path': self.path,
            'filtered_path': self.filtered_path,
        }

        d.update(self.path_flags())

        return d


class TableShell(object):
    """Access object for table shell files.

    The Shell Files, such as:

        https://www2.census.gov/programs-surveys/acs/summary_file/2016/documentation/user_tools/ACS2016_Table_Shells.xlsx

    The Shell files have information about each table and columns, including:
        * Table Id
        * Data column line number in the table
        * Column title ( called "Stub" )
        * Which release the column is available in

    """

    def __init__(self, year, release):
        url_s = table_shell_url(year=year, release=release, stusab=None, summary_level=None, seq=None)

        self.url = parse_app_url(url_s)

        self._tables = None

    def _process(self, tables=None):

        if self._tables:
            return self._tables

        tables = tables or {}

        for row in self.url.generator.iter_rp:

            if not row[0].strip():
                continue

            table_id_key = row[0].strip().lower()

            try:
                uid = row['UniqueID']
            except KeyError:
                uid = row['Unique ID']

            if not uid:  # Table row

                if table_id_key not in tables:
                    tables[table_id_key] = Table(row[0], row['Stub'].strip())
                elif 'Universe' in row['Stub']:
                    tables[table_id_key].universe = row['Stub'].strip().replace('Universe: ', '')

            else:  # column row

                try:
                    line_no = int(row['Line'])

                except ValueError:
                    # Probably, the line number  is a float, which indicates a header line. Header lines don't have
                    # estimates associated with them, so we exclude them.
                    pass
                else:

                    if not line_no in tables[table_id_key].columns:
                        startpos = tables[table_id_key].startpos or 0

                        tables[table_id_key].columns[line_no] = Column(None, row[0], uid, line_no,
                                                                       short_desc=row['Stub'],
                                                                       seq_file_col_no=line_no + startpos,
                                                                       row=row.dict)
                    else:
                        tables[table_id_key].columns[line_no].short_desc = row['Stub']

        self._tables = tables

        return self._tables

    @property
    def tables(self):
        if self._tables:
            return self._tables

        self._process()

        return self._tables


class TableLookup(object):
    """Access object for the TableLookup files.

    The Lookup files, such as:

        https://www2.census.gov/programs-surveys/acs/summary_file/2017/documentation/user_tools/ACS_5yr_Seq_Table_Number_Lookup.txt

    have information about each table and column, including:
        * Table Number
        * Column Line
        * Table start position in sequence file
        * Total cells in table and sequence
        * Short column title

    THe processing will also add information on the 'path' of the table,
    which relates how the column values roll up to higher level values.

    THe process will also fetch files from the Census API, which has information on the
    "path" of the columns, which relates how the column values roll up to higher level values. For instance,
    the path '/total/male/under 5 years' means that all of the values that have a path prefix
    of '/total/male' will be summed to get the total for all males, and the values for
    '/total/male' and '/total/female' will be summed to get the total for all people.

    The path is also used to set the flags for the column metadata, such as race, raceeth, sex,
    age, and poverty_status.

    """

    def __init__(self, year, release):

        self.url = table_lookup_url(year=year, release=release, stusab=None, summary_level=None, seq=None)

        self.api_url = api_var_url(year=year, release=release)

        self._tables = None

    def _process(self, tables=None):
        """Build the local data structure from the source data structure"""

        from rowgenerators.appurl.file import CsvFileUrl

        if self._tables:
            return self._tables

        tables = tables or {}

        url = str(parse_app_url(self.url).get_resource().get_target())

        csv_url = CsvFileUrl(url, encoding='latin1')

        import requests
        d = requests.get(self.api_url).json()
        self.api_vars = vars = d['variables']

        for row in csv_url.generator.iter_rp:

            table_id_key = row['Table ID'].strip().lower()

            if not row['Line Number'].strip():  # Either the table title, or the Universe row

                if 'Universe' not in row['Table Title']:
                    if table_id_key not in tables:

                        tables[table_id_key] = Table(row['Table ID'], row['Table Title'].strip().title(),
                                                     seq=[int(row['Sequence Number'])],
                                                     startpos=int(row['Start Position']),
                                                     subject=row['Subject Area'],
                                                     row=row.dict)

                    else:
                        # This case is for multi-segment tables
                        assert (int(row['Start Position']) == 7)  # Should always start at the beginning of the segment

                        tables[table_id_key].seq.append(int(row['Sequence Number']))

                        tables[table_id_key].number_of_segments += 1

                else:
                    tables[table_id_key].universe = row['Table Title'].replace('Universe: ', '').strip()

            else:  # column row
                try:

                    line_no = int(row['Line Number'])

                    if not line_no in tables[table_id_key].columns:

                        col_id = f"{row['Table ID']}_{line_no:03}"

                        api_meta = vars[col_id + 'E']
                        full_path = '/' + api_meta['label'].replace('Estimate!!', '').replace('/', '|').replace('!!',
                                                                                                                '/').replace(
                            ':', '').lower()

                        # Path elements that have '--' in them are grouping headings, and should be ignored.
                        path = '/'.join(filter(lambda v: not v.endswith('--'), full_path.split('/')))

                        tables[table_id_key].columns[line_no] = Column(tables[table_id_key], row['Table ID'],
                                                                       col_id,
                                                                       line_no,
                                                                       name=row['Table Title'],
                                                                       path=path,
                                                                       row=row.dict)
                    else:
                        tables[table_id_key].columns[line_no].description = row['Table Title']


                except ValueError as e:
                    # Headings, which have fractional line numebrs
                    tables[table_id_key].fractionals[row['Line Number']] = row.dict

        self._tables = tables

        return self._tables

    @property
    def tables(self):
        if self._tables:
            return self._tables

        self._process()

        return self._tables

    @cached_property
    def tables_df(self):
        """Return a DataFrame of the tables"""
        df = pd.DataFrame([table.dict for table in self.tables.values()])

        # Mark tables that have paths that are not unique, which happens because
        # there are too many columns with '--' in them

        cdf = self.columns_df
        tpath = cdf.table_id + cdf.path
        bad_tables_ids = list(
            sorted(set([e[0] for e in list(tpath.value_counts()[tpath.value_counts() > 1].index.str.split('/'))])))

        df['redundant_paths'] = df.table_id.isin(bad_tables_ids)

        return df

    @cached_property
    def columns_df(self):
        """Return a DataFrame of the columns"""

        def ud(d1, d2):
            d1.update(d2)
            return d1

        cols = []
        for table_name, table in self.tables.items():
            for column_name, c in table.columns.items():
                cols.append(c)

        ac = [ud(dict(column_id=e.unique_id, table_id=e.table_id, name=e.name), e.dict) for e in cols]
        df = pd.DataFrame(ac)

        # Filter the path so that it doesn't include elements that have their own columns,
        # such as race, age, poverty

        return df


class TableMeta(object):
    """Combines the lookup and  shell objects, but mostly just uses the TableLookup

    This should be deprecated and replaced, since it provides no additional utility over TableLookup
    """

    def __init__(self, year, release):

        self.year = year
        self.release = release

        self.ts = None
        self.tl = None

        self._tables = None

    def _process(self):

        if self._tables:
            return self._tables

        self._tables = {}

        self.tl = TableLookup(self.year, self.release)
        self._tables = self.tl._process(tables=self._tables)

        return self._tables

    @property
    def tables(self):
        if self._tables:
            return self._tables

        self._process()

        return self._tables

    @property
    def summary_levels(self):
        """Return a dict of summary level names, numbers and descriptions"""
        from geoid.core import names, descriptions

        sl = {}

        for sl_name, sl_no in names.items():
            sl[sl_no] = {
                'number': sl_no,
                'name': sl_name,
                'desc': descriptions.get(sl_no)
            }

        return sl

    @property
    def states(self):
        """Return a dict of state names, numbers and abbreviations"""
        from geoid.censusnames import geo_names, stusab

        states = {}

        for state_no, stusab in stusab.items():
            states[stusab] = {
                'name': geo_names[(state_no, 0)],
                'stusab': stusab,
                'number': state_no
            }

        states['US'] = {
            'name': 'United States',
            'stusab': 'US',
            'number': 0
        }

        return states

    def _repr_html_(self, **kwargs):

        return f"""
        <h1>Census Metadata {self.year}, release {self.release}
        <table>
        <tr><td>Meta Tables</td><td>{len(self.tables)}</td></tr>
        <tr><td>Shell Tables</td><td>{len(self.ts.tables) if self.ts else 0}</td></tr>
        <tr><td>Lookup Tables</td><td>{len(self.tl.tables) if self.tl else 0}</td></tr>
        </table>"""


class SequenceMeta(object):
    pass

