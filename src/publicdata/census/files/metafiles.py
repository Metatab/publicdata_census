# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

import re
import pandas as pd
from functools import cached_property

"""Classes to acess metadata files"""
from publicdata.census.files.url_templates import (
    table_lookup_url,
    table_shell_url,
    api_var_url
)
from rowgenerators import parse_app_url

race_iterations = [
    ('A', 'white', 'White'),
    ('B', 'black', 'Black or African American'),
    ('C', 'aian', 'American Indian and Alaska Native'),
    ('D', 'asian', 'Asian'),
    ('E', 'nhopi', 'Native Hawaiian and Other Pacific Islander'),
    ('F', 'other', 'Some Other Race'),
    ('G', 'many', 'Two or More Races'),
    ('H', 'nhwhite', 'White Alone, Not Hispanic or Latino'),
    ('N', 'nhisp', 'Not Hispanic or Latino'),
    ('I', 'hisp', 'Hispanic or Latino'),
    ('C', 'aian', 'American Indian'),
    (None, 'all', 'All races')]

ri_code_map = {code.lower(): race for code, race, term in race_iterations if code}

# A regex to remove race interations from the table titles
ri_titles = []
for _, _, ri in race_iterations:
    ri_titles.append(fr"\({ri}\)".title())
    ri_titles.append(fr"\({ri} Householder\)".title())
    ri_titles.append(fr"\({ri} Alone\)".title())
    ri_titles.append(fr"\({ri} Alone Householder\)".title())

p = re.compile('|'.join(ri_titles))

def remove_ri_title(v):
    return re.sub(r'\s+',' ', re.sub(p,'',v)).strip()


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
            self.subject
        ]

    @property
    def dict(self):
        return {
            'table_id': self.unique_id,
            'seq': self.seq,
            'start_pos': self.startpos,
            'title': self.title,
            'universe': self.universe,
            'subject': self.subject
        }

    @property
    def race(self):
        """Return a race code from the table id"""

        return ri_code_map.get(self.unique_id[-1].lower())

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

        self.path=path

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
    def extract_age(cls,v):

        pats = {
            'to': re.compile("(?P<lower>\d+) to (?P<upper>\d+) years"),
            'and': re.compile("(?P<lower>\d+) and (?P<upper>\d+) years"),
            'under': re.compile("under (?P<upper>\d+) years"),
            'over': re.compile("(?P<lower>\d+) years? and over"),
            'single': re.compile("(?P<upperlower>\d+) years"),

        }

        if v and 'year' in v:

            v = v.replace('1 year ago', '').replace('year-round', '')

            m = pats['to'].search(v)
            if m:
                return (int(m.group('lower')), int(m.group('upper')))

            m = pats['and'].search(v)
            if m:
                return (int(m.group('lower')), int(m.group('upper')))

            m = pats['under'].search(v)
            if m:
                return (0, int(m.group('upper')))

            m = pats['over'].search(v)
            if m:
                return (int(m.group('lower')), 120)

            m = pats['single'].search(v)
            if m:
                return (int(m.group('upperlower')), int(m.group('upperlower')))

        return None


    @property
    def age_range(self):
        """Parse the description for an age range"""
        import re

        return self.extract_age(self.path)

    @property
    def age(self):
        ar = self.age_range
        if ar:
            return "{:03d}-{:03d}".format(*ar)
        else:
            return 'all'

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
    def extract_poverty(cls,v):
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
            '2.00 to 3.99 of poverty threshold': '200-300',
            '1.00 to 1.37 of poverty threshold': '100-137'
        }

        for term, code in pov_map.items():
            if term in v:
                return code

        return 'all'

    @property
    def poverty_status(self):
        return self.extract_poverty(self.path)

    @property
    def dict(self):
        return {
            'sex': self.sex,
            'raceeth': self.raceeth,
            'age': self.age,
            'age_range': self.age_range,
            'min_age': self.min_age,
            'max_age': self.max_age,
            'poverty_status': self.poverty_status,
            'path': self.path,
        }

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
                        full_path = '/'+api_meta['label'].replace('Estimate!!', '').replace('!!', '/').replace(':', '').lower()

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
        df =  pd.DataFrame([table.dict for table in self.tables.values()])

        # Mark tables that have paths that are not unique, which happens because
        # there are too many columns with '--' in them

        cdf = self.columns_df
        tpath = cdf.table_id + cdf.path
        bad_tables_ids = list(sorted(set([e[0] for e in list(tpath.value_counts()[tpath.value_counts()>1].index.str.split('/'))])))

        df['race'] = df.table_id.str.replace('PR','').str.slice(-1).apply(lambda v: ri_code_map.get(v.lower()))

        # Some tables don't have race iterations, but do have a race in the universe
        df.loc[df.race.isnull(), 'race'] = df.loc[df.race.isnull(), 'universe'].apply(Column.extract_raceeth)

        df['age'] = df.universe.apply(Column.extract_age)

        # Strip off the race specification for race iterations
        df['bare_title'] = df.title
        df.loc[~df.race.isnull(), 'bare_title'] = df[~df.race.isnull()].title.apply(remove_ri_title )

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

        ac = [ud(dict(uid=e.unique_id, table_id=e.table_id, name=e.name), e.dict) for e in cols]
        df = pd.DataFrame(ac)

        # Filter the path so that it doesn't include elements that have their own columns,
        # such as race, age, poverty

        def keep_path_elem(v):

            def extract_sex(v):
                if v == 'male':
                    return 'male'
                elif v == 'female':
                    return 'female'
                else:
                    return None

            if extract_sex(v) is None and Column.extract_age(v) is None and Column.extract_poverty(
                    v) == 'all' and v != 'total':
                return True
            else:
                return False

        def filter_path(v):
            return list(filter(keep_path_elem, v.split('/'))) if v else v

        df['filtered_path'] = df.path.apply(filter_path).apply(lambda v: '/'.join(v[:-1]))

        t = df.filtered_path.str.split('/')
        t = t.apply(lambda v: v[1:])
        df['n_levels'] = t.apply(len)

        for i in range(1, df.n_levels.max()):
            df[f'level_{i}'] = df.path.apply(filter_path).apply(lambda v: v[i] if len(v) > i + 1 else None)

        df['filtered_path'] = df['filtered_path'].replace('', None)

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
